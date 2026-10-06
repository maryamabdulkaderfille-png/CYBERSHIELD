from app.services.url_scanner.rules import (
    blacklist_check,
    domain_age,
    external_threat_intel,
    https_check,
    ip_address,
    redirect_check,
    special_characters,
    ssl_certificate,
    subdomains,
    suspicious_keywords,
    typosquatting,
    url_length,
    whitelist_check,
)

# Order controls the order reasons appear in for the user-facing report.
RULES = [
    whitelist_check,
    url_length,
    https_check,
    ssl_certificate,
    ip_address,
    suspicious_keywords,
    special_characters,
    subdomains,
    typosquatting,
    domain_age,
    blacklist_check,
    external_threat_intel,
    redirect_check,
]

# These rules make real, potentially slow network calls (TLS handshake, RDAP
# lookup, HTTP HEAD requests, threat intel lookup). The engine runs them concurrently — see
# engine.py — instead of adding their latencies up serially.
NETWORK_BOUND_RULE_NAMES = {"ssl_certificate", "domain_age", "redirect_check", "external_threat_intel"}
