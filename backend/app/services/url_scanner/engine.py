import concurrent.futures
from datetime import datetime, timezone
from ipaddress import ip_address

from app.services.rule_registry_service import filter_enabled_rules
from app.services.url_scanner.context import build_context
from app.services.url_scanner.network import is_public_ip
from app.services.url_scanner.rules import NETWORK_BOUND_RULE_NAMES, RULES
from app.services.url_scanner.types import RiskLevel, RuleResult, ScanContext, ScanReport, Severity
from app.utils.errors import APIError

CPU_ONLY_RULES = [r for r in RULES if r.__name__.rsplit(".", 1)[-1] not in NETWORK_BOUND_RULE_NAMES]

MAX_SCORE = 100
MIN_SCORE = 0

# Network-bound rules run concurrently (see _run_rules), but the engine still
# won't wait forever on a slow/unresponsive target: whichever of them haven't
# finished by this deadline are reported as timed-out rather than blocking
# the whole scan request indefinitely.
NETWORK_RULES_TIMEOUT_SECONDS = 8


def _rule_name(rule_module) -> str:
    return rule_module.__name__.rsplit(".", 1)[-1]


def _timeout_result(rule_module) -> RuleResult:
    name = _rule_name(rule_module)
    return RuleResult(
        rule=name,
        label=name.replace("_", " ").title(),
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="This check took too long to complete and was skipped.",
        detail="timeout",
    )


def _error_result(rule_module, exc: Exception) -> RuleResult:
    name = _rule_name(rule_module)
    return RuleResult(
        rule=name,
        label=name.replace("_", " ").title(),
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="This check failed unexpectedly and was skipped.",
        detail=str(exc),
    )


def _run_rules(ctx: ScanContext) -> list[RuleResult]:
    """Runs the fast, CPU-only rules synchronously, then the slow,
    network-bound ones (SSL, domain age, redirects) concurrently — so their
    latencies overlap instead of stacking up serially. Bounded by
    NETWORK_RULES_TIMEOUT_SECONDS so one slow/hanging target can't block a
    scan indefinitely."""
    active_rules = filter_enabled_rules("url", RULES, _rule_name)
    cpu_rules = [r for r in active_rules if _rule_name(r) not in NETWORK_BOUND_RULE_NAMES]
    network_rules = [r for r in active_rules if _rule_name(r) in NETWORK_BOUND_RULE_NAMES]

    results_by_name: dict[str, RuleResult] = {}
    for rule in cpu_rules:
        result = rule.evaluate(ctx)
        results_by_name[result.rule] = result

    if network_rules:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(network_rules))
        try:
            future_to_rule = {executor.submit(rule.evaluate, ctx): rule for rule in network_rules}
            done, not_done = concurrent.futures.wait(future_to_rule, timeout=NETWORK_RULES_TIMEOUT_SECONDS)

            for future in done:
                rule = future_to_rule[future]
                try:
                    results_by_name[_rule_name(rule)] = future.result()
                except Exception as exc:  # a rule bug shouldn't take the whole scan down
                    results_by_name[_rule_name(rule)] = _error_result(rule, exc)

            for future in not_done:
                rule = future_to_rule[future]
                results_by_name[_rule_name(rule)] = _timeout_result(rule)
        finally:
            # wait=False: don't block returning the response on stragglers —
            # any still-running thread finishes in the background and is
            # discarded. cancel_futures skips ones that hadn't started yet.
            executor.shutdown(wait=False, cancel_futures=True)

    return [results_by_name[_rule_name(rule)] for rule in active_rules]


RECOMMENDATION_BY_RULE = {
    "ip_address": "Avoid trusting URLs that use a raw IP address instead of a proper domain name.",
    "ssl_certificate": "Do not proceed if your browser shows a certificate warning for this site.",
    "https_check": "Do not enter sensitive data over an unencrypted (HTTP) connection.",
    "typosquatting": "This domain closely resembles a well-known brand — verify you're on the official website before proceeding.",
    "blacklist_check": "This domain is known to be malicious. Do not proceed, and report it if you received it via email or message.",
    "external_threat_intel": "This destination is flagged on global threat intelligence feeds. Close this page immediately and do not interact with its content.",
    "domain_age": "Newly registered domains are commonly used for short-lived phishing campaigns — proceed with caution.",
    "redirect_check": "Be cautious of sites that redirect you elsewhere before you reach the final page.",
}

BASE_RISK_RECOMMENDATIONS = [
    "Do not enter passwords or personal information on this site.",
    "Avoid financial transactions until you verify this site.",
    "Verify the official website through a trusted source (e.g. a search engine or bookmark) before proceeding.",
]


def _build_reasons(rule_results: list[RuleResult]) -> list[str]:
    return [f"✔ {r.message}" for r in rule_results if r.triggered]


def _build_recommendations(rule_results: list[RuleResult], risk_level: str) -> list[str]:
    recommendations: list[str] = []

    if risk_level in {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS}:
        recommendations.extend(BASE_RISK_RECOMMENDATIONS)

    for result in rule_results:
        if result.triggered and result.rule in RECOMMENDATION_BY_RULE:
            recommendation = RECOMMENDATION_BY_RULE[result.rule]
            if recommendation not in recommendations:
                recommendations.append(recommendation)

    if not recommendations:
        recommendations.append(
            "No significant risk indicators were found. Always stay cautious with personal information online."
        )

    return recommendations


def _score_and_risk(rule_results: list[RuleResult]) -> tuple[int, str]:
    score = MAX_SCORE + sum(r.impact for r in rule_results)
    score = max(MIN_SCORE, min(MAX_SCORE, score))
    return score, RiskLevel.from_score(score)


def _is_private_target(ctx: ScanContext) -> bool:
    """True when the target is a private/loopback/link-local/reserved
    address (reusing the same `is_public_ip` check the Personal Block List's
    "can't block private IPs" guard already uses) — not a valid public
    phishing-scan target at all, distinct from a domain that's merely
    unresolvable (which is left to degrade gracefully as it already does)."""
    if ctx.is_ip_host:
        return not is_public_ip(ip_address(ctx.hostname))
    if ctx.resolved_ips:
        return not all(is_public_ip(addr) for addr in ctx.resolved_ips)
    return False


def scan_url(raw_url: str) -> ScanReport:
    ctx = build_context(raw_url)

    if _is_private_target(ctx):
        raise APIError(
            "CyberShield does not scan private, internal, or loopback network addresses — "
            "they aren't valid public phishing targets.",
            422,
        )

    rule_results = _run_rules(ctx)
    score, risk_level = _score_and_risk(rule_results)

    return ScanReport(
        trust_score=score,
        risk_level=risk_level,
        reasons=_build_reasons(rule_results),
        recommendations=_build_recommendations(rule_results, risk_level),
        rule_results=rule_results,
        scanned_at=datetime.now(timezone.utc),
    )


def quick_classify(raw_url: str) -> tuple[int, str]:
    """A fast, network-free trust score/risk classification for a URL.

    Runs only the CPU-bound rules (no TLS handshake, no RDAP lookup, no HTTP
    requests) — used by the email scanner to triage every link found in an
    email without multiplying a single email scan into dozens of outbound
    network calls. Reuses the exact same rule modules and scoring formula as
    `scan_url`; it just runs a subset of them.

    This is an intentional divergence, not a bug: the same URL can
    legitimately score differently through `quick_classify` than through
    `scan_url`, because `scan_url` also runs the 4 network-bound rules
    (ssl_certificate, domain_age, redirect_check, external_threat_intel —
    see NETWORK_BOUND_RULE_NAMES) which can themselves move the score. Do not
    "fix" a mismatch between the two by merging them — pick the right call
    for the use case instead: `quick_classify` for triaging many links
    cheaply (email), `scan_url` for a single, thorough, user-facing scan.
    """
    ctx = build_context(raw_url, resolve_dns=False)
    active_rules = filter_enabled_rules("url", CPU_ONLY_RULES, _rule_name)
    rule_results = [rule.evaluate(ctx) for rule in active_rules]
    return _score_and_risk(rule_results)
