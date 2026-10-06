"""Global curated whitelist of verified legitimate domains.

Prevents false positives on well-known, high-reputation domains (e.g.,
Google, Microsoft, Apple, GitHub, PayPal) when URLs contain normal
authentication paths ("login", "verify", "password") or lengthy OAuth
parameters.
"""

from app.services.url_scanner.domain_utils import registrable_domain

# Curated list of verified official root domains
GLOBAL_WHITELIST: dict[str, str] = {
    # Tech & Cloud
    "google.com": "Google",
    "microsoft.com": "Microsoft",
    "apple.com": "Apple",
    "github.com": "GitHub",
    "amazon.com": "Amazon",
    "cloudflare.com": "Cloudflare",
    "mozilla.org": "Mozilla",
    "docker.com": "Docker",
    "openai.com": "OpenAI",
    "gitlab.com": "GitLab",
    "digitalocean.com": "DigitalOcean",
    "stackoverflow.com": "Stack Overflow",
    # Social & Communications
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "twitter.com": "Twitter",
    "x.com": "X (Twitter)",
    "linkedin.com": "LinkedIn",
    "whatsapp.com": "WhatsApp",
    "telegram.org": "Telegram",
    "slack.com": "Slack",
    "zoom.us": "Zoom",
    "reddit.com": "Reddit",
    "discord.com": "Discord",
    # Financial & Payments
    "paypal.com": "PayPal",
    "stripe.com": "Stripe",
    "visa.com": "Visa",
    "mastercard.com": "Mastercard",
    "chase.com": "Chase",
    "bankofamerica.com": "Bank of America",
    "wellsfargo.com": "Wells Fargo",
    "americanexpress.com": "American Express",
    # Media & Knowledge
    "netflix.com": "Netflix",
    "youtube.com": "YouTube",
    "spotify.com": "Spotify",
    "steamcommunity.com": "Steam",
    "steampowered.com": "Steam",
    "wikipedia.org": "Wikipedia",
    "wikimedia.org": "Wikimedia",
}


def is_whitelisted_domain(hostname: str | None) -> tuple[bool, str | None]:
    """Checks if a given hostname belongs to the global whitelist.

    Returns (True, BrandName) if verified, or (False, None) otherwise.
    Properly matches root domains and all legitimate subdomains
    (e.g., 'accounts.google.com' -> True, 'google.com' -> True,
    'evil-google.com' -> False).
    """
    if not hostname:
        return False, None

    cleaned_host = hostname.strip().lower()
    # Strip trailing dot if present (FQDN)
    if cleaned_host.endswith("."):
        cleaned_host = cleaned_host[:-1]

    reg_domain = registrable_domain(cleaned_host)
    if reg_domain in GLOBAL_WHITELIST:
        # Double check hostname is exact domain or ends with '.{reg_domain}'
        if cleaned_host == reg_domain or cleaned_host.endswith(f".{reg_domain}"):
            return True, GLOBAL_WHITELIST[reg_domain]

    return False, None
