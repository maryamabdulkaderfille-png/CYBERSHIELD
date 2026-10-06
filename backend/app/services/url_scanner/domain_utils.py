def registrable_domain(hostname: str) -> str:
    """Approximate the registrable domain (last two labels).

    Doesn't consult a public-suffix list, so multi-part TLDs like
    `co.uk` are not handled specially — acceptable for the heuristics
    that use this (typosquatting/domain-age lookups), not a security
    boundary.
    """
    labels = [label for label in hostname.split(".") if label]
    return ".".join(labels[-2:]) if len(labels) >= 2 else hostname
