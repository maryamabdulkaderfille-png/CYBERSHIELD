"""Registry of frequently-impersonated brands for display-name / sender
analysis. To add a new brand, add one entry — no other code changes needed.

Each brand maps to the set of domains that are legitimately allowed to send
as that brand. An email whose display name names a brand but whose sender
domain isn't in that set is a strong impersonation signal.
"""

KNOWN_BRANDS: dict[str, set[str]] = {
    "microsoft": {"microsoft.com", "outlook.com", "live.com", "office.com", "microsoftonline.com"},
    "google": {"google.com", "gmail.com", "accounts.google.com"},
    "apple": {"apple.com", "icloud.com"},
    "amazon": {"amazon.com", "amazon.co.uk", "amazon.ca"},
    "paypal": {"paypal.com"},
    "facebook": {"facebook.com", "meta.com", "fb.com"},
    "netflix": {"netflix.com"},
    "instagram": {"instagram.com"},
    "linkedin": {"linkedin.com"},
    "bank of america": {"bankofamerica.com"},
    "chase": {"chase.com"},
    "wells fargo": {"wellsfargo.com"},
    "irs": {"irs.gov"},
    "usps": {"usps.com"},
    "dhl": {"dhl.com"},
    "fedex": {"fedex.com"},
}

# Free/consumer email providers — legitimate for personal use, but a strong
# signal of impersonation when the display name claims to be an organization
# (e.g. "PayPal Support" <support@gmail.com>).
FREE_EMAIL_DOMAINS: set[str] = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "aol.com",
    "icloud.com",
    "protonmail.com",
    "mail.com",
    "yandex.com",
    "zoho.com",
    "gmx.com",
}

ORGANIZATION_WORDS: set[str] = {
    "support",
    "service",
    "services",
    "team",
    "security",
    "billing",
    "account",
    "accounts",
    "admin",
    "administrator",
    "helpdesk",
    "notification",
    "notifications",
    "alerts",
    "verify",
    "official",
}


def domain_of(email_address: str) -> str:
    return email_address.rsplit("@", 1)[-1].lower() if "@" in email_address else ""
