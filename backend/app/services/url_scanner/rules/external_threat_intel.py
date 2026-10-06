"""External Threat Intelligence scanner rule.

Checks the target URL and domain against global threat feeds (VirusTotal API
and URLhaus open threat database). Flags confirmed malicious campaigns
with CRITICAL severity.

Both providers report a three-valued `_ProviderResult` (MATCH / CLEAN /
UNAVAILABLE), not a boolean: collapsing "the provider confirmed this is
clean" and "the provider couldn't be reached/authenticated" into the same
`False` would let an auth failure, rate limit, missing API key, or outage
silently masquerade as a clean verdict. `evaluate()` only reports an overall
"clean" result when every provider it actually queried came back CLEAN —
if any came back UNAVAILABLE (and none MATCHed), the rule says so honestly
instead of claiming a confirmed-clean verdict it never reached.
"""

import base64
import os
from dataclasses import dataclass

import requests
from flask import current_app

from app.services.url_scanner.types import RuleResult, ScanContext, Severity
from app.services.url_scanner.whitelist import is_whitelisted_domain

THREAT_INTEL_TIMEOUT_SECONDS = 3.5

URLHAUS_API_URL = "https://urlhaus-api.abuse.ch/v1/url/"
# Official VirusTotal API v3 "Get a URL object" endpoint. The {id} path
# segment is the URL's identifier as VT v3 defines it: the URL string,
# base64 (URL-safe alphabet, no padding) encoded -- not a hash of the body,
# and not an unofficial/undocumented endpoint. See
# https://docs.virustotal.com/reference/url-info
VIRUSTOTAL_API_URL = "https://www.virustotal.com/api/v3/urls/{id}"


@dataclass
class _ProviderResult:
    status: str  # "match" | "clean" | "unavailable"
    detail: str = ""
    # Only set when status == "unavailable": missing_auth_key |
    # authentication_failed | rate_limited | provider_error | network_error |
    # invalid_response
    reason: str | None = None


def _check_virustotal(raw_url: str, api_key: str) -> _ProviderResult:
    """Queries VirusTotal API v3 for URL analysis. Every response/failure
    mode is classified explicitly so a failed or inconclusive check can
    never be read as "URL is clean" (see module docstring)."""
    if not api_key:
        return _ProviderResult(
            status="unavailable", detail="VirusTotal API key not configured.", reason="missing_auth_key"
        )

    url_id = base64.urlsafe_b64encode(raw_url.encode()).decode().strip("=")

    try:
        response = requests.get(
            VIRUSTOTAL_API_URL.format(id=url_id),
            headers={"x-apikey": api_key, "User-Agent": "CyberShield-ThreatIntel/1.0"},
            timeout=THREAT_INTEL_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        _log_provider_failure("VirusTotal", "timed out")
        return _ProviderResult(status="unavailable", detail="VirusTotal request timed out.", reason="network_error")
    except requests.exceptions.RequestException as exc:
        _log_provider_failure("VirusTotal", f"connection error ({exc.__class__.__name__})")
        return _ProviderResult(status="unavailable", detail="Could not connect to VirusTotal.", reason="network_error")

    if response.status_code in (401, 403):
        _log_provider_failure("VirusTotal", f"authentication failed (HTTP {response.status_code})")
        return _ProviderResult(
            status="unavailable", detail="VirusTotal authentication failed.", reason="authentication_failed"
        )
    if response.status_code == 404:
        # VT has no record of this URL at all (never submitted/analyzed) --
        # not an error. Treated the same as URLhaus's "no_results": a
        # successful check that found nothing, not an unavailable provider.
        return _ProviderResult(status="clean", detail="Not previously analyzed by VirusTotal.")
    if response.status_code == 429:
        _log_provider_failure("VirusTotal", "rate limited (HTTP 429)")
        return _ProviderResult(status="unavailable", detail="VirusTotal rate limit exceeded.", reason="rate_limited")
    if response.status_code >= 500:
        _log_provider_failure("VirusTotal", f"provider error (HTTP {response.status_code})")
        return _ProviderResult(
            status="unavailable", detail=f"VirusTotal provider error (HTTP {response.status_code}).",
            reason="provider_error",
        )
    if response.status_code != 200:
        _log_provider_failure("VirusTotal", f"unexpected status (HTTP {response.status_code})")
        return _ProviderResult(
            status="unavailable", detail=f"Unexpected VirusTotal response (HTTP {response.status_code}).",
            reason="provider_error",
        )

    try:
        data = response.json()
    except ValueError:
        _log_provider_failure("VirusTotal", "returned malformed JSON")
        return _ProviderResult(
            status="unavailable", detail="VirusTotal returned a malformed response.", reason="invalid_response"
        )

    if "data" not in data:
        _log_provider_failure("VirusTotal", "200 response missing expected 'data' envelope")
        return _ProviderResult(
            status="unavailable", detail="VirusTotal returned an unexpected response structure.",
            reason="invalid_response",
        )

    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    if malicious > 0:
        return _ProviderResult(
            status="match", detail=f"Flagged as malicious by {malicious} security vendors on VirusTotal."
        )
    if suspicious > 2:
        return _ProviderResult(
            status="match", detail=f"Flagged as suspicious by {suspicious} security vendors on VirusTotal."
        )
    return _ProviderResult(status="clean", detail="No malicious detections on VirusTotal.")


def _check_urlhaus(raw_url: str, auth_key: str) -> _ProviderResult:
    """Queries the URLhaus public API for verified active phishing/malware
    payloads. URLhaus requires an `Auth-Key` header (free registration at
    urlhaus.abuse.ch) — every response/failure mode is classified explicitly
    below rather than collapsed into a single pass/fail boolean, so a failed
    check can never be read as "URL is clean"."""
    if not auth_key:
        return _ProviderResult(status="unavailable", detail="URLhaus API key not configured.", reason="missing_auth_key")

    try:
        response = requests.post(
            URLHAUS_API_URL,
            data={"url": raw_url},
            timeout=THREAT_INTEL_TIMEOUT_SECONDS,
            headers={"User-Agent": "CyberShield-ThreatIntel/1.0", "Auth-Key": auth_key},
        )
    except requests.exceptions.Timeout:
        _log_provider_failure("URLhaus", "timed out")
        return _ProviderResult(status="unavailable", detail="URLhaus request timed out.", reason="network_error")
    except requests.exceptions.RequestException as exc:
        _log_provider_failure("URLhaus", f"connection error ({exc.__class__.__name__})")
        return _ProviderResult(status="unavailable", detail="Could not connect to URLhaus.", reason="network_error")

    if response.status_code in (401, 403):
        _log_provider_failure("URLhaus", f"authentication failed (HTTP {response.status_code})")
        return _ProviderResult(
            status="unavailable", detail="URLhaus authentication failed.", reason="authentication_failed"
        )
    if response.status_code == 429:
        _log_provider_failure("URLhaus", "rate limited (HTTP 429)")
        return _ProviderResult(status="unavailable", detail="URLhaus rate limit exceeded.", reason="rate_limited")
    if response.status_code >= 500:
        _log_provider_failure("URLhaus", f"provider error (HTTP {response.status_code})")
        return _ProviderResult(
            status="unavailable", detail=f"URLhaus provider error (HTTP {response.status_code}).",
            reason="provider_error",
        )
    if response.status_code != 200:
        _log_provider_failure("URLhaus", f"unexpected status (HTTP {response.status_code})")
        return _ProviderResult(
            status="unavailable", detail=f"Unexpected URLhaus response (HTTP {response.status_code}).",
            reason="provider_error",
        )

    try:
        data = response.json()
    except ValueError:
        _log_provider_failure("URLhaus", "returned malformed JSON")
        return _ProviderResult(status="unavailable", detail="URLhaus returned a malformed response.", reason="invalid_response")

    query_status = data.get("query_status")
    if query_status == "ok":
        threat = data.get("threat") or "malware/phishing"
        status = data.get("url_status") or "active"
        return _ProviderResult(
            status="match", detail=f"Verified threat on URLhaus feed ({threat}, status: {status})."
        )
    if query_status == "no_results":
        return _ProviderResult(status="clean", detail="Not listed on the URLhaus feed.")

    _log_provider_failure("URLhaus", f"unexpected query_status ({query_status!r})")
    return _ProviderResult(
        status="unavailable", detail="URLhaus returned an unrecognized response.", reason="invalid_response"
    )


def _log_provider_failure(provider: str, summary: str) -> None:
    try:
        current_app.logger.warning("%s threat-intel check unavailable: %s", provider, summary)
    except RuntimeError:
        pass  # no app context (e.g. a bare unit-test call) -- non-fatal, just skip logging


def _urlhaus_auth_key() -> str:
    key = os.getenv("URLHAUS_AUTH_KEY", "")
    try:
        if current_app and current_app.config.get("URLHAUS_AUTH_KEY"):
            key = current_app.config["URLHAUS_AUTH_KEY"]
    except RuntimeError:
        pass
    return key


def _virustotal_api_key() -> str:
    key = os.getenv("VIRUSTOTAL_API_KEY", "")
    try:
        if current_app and current_app.config.get("VIRUSTOTAL_API_KEY"):
            key = current_app.config["VIRUSTOTAL_API_KEY"]
    except RuntimeError:
        pass
    return key


def evaluate(ctx: ScanContext) -> RuleResult:
    # Whitelisted domains don't need threat intel queries
    if ctx.hostname:
        is_safe, brand = is_whitelisted_domain(ctx.hostname)
        if is_safe:
            return RuleResult(
                rule="external_threat_intel",
                label="Global Threat Intelligence",
                triggered=False,
                impact=0,
                severity=Severity.INFO,
                message=f"Verified authentic domain for {brand} — trusted by global reputation networks.",
            )

    vt_result = _check_virustotal(ctx.raw_url, _virustotal_api_key())
    if vt_result.status == "match":
        return RuleResult(
            rule="external_threat_intel",
            label="Global Threat Intelligence",
            triggered=True,
            impact=-100,
            severity=Severity.CRITICAL,
            message=vt_result.detail,
            detail=vt_result.detail,
        )

    urlhaus_result = _check_urlhaus(ctx.raw_url, _urlhaus_auth_key())
    if urlhaus_result.status == "match":
        return RuleResult(
            rule="external_threat_intel",
            label="Global Threat Intelligence",
            triggered=True,
            impact=-100,
            severity=Severity.CRITICAL,
            message=urlhaus_result.detail,
            detail=urlhaus_result.detail,
        )

    unavailable = [
        (name, result.reason)
        for name, result in (("virustotal", vt_result), ("urlhaus", urlhaus_result))
        if result.status == "unavailable"
    ]
    if unavailable:
        reason_detail = ",".join(f"{name}={reason}" for name, reason in unavailable)
        return RuleResult(
            rule="external_threat_intel",
            label="Global Threat Intelligence",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Global threat-intelligence check could not be completed — result unknown, not confirmed clean.",
            detail=f"unavailable:{reason_detail}",
        )

    return RuleResult(
        rule="external_threat_intel",
        label="Global Threat Intelligence",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Target is clean and not listed on global threat intelligence feeds.",
    )
