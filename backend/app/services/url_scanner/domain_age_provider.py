"""Domain registration age lookup.

Structured as a swappable provider so a different data source (a paid
WHOIS API, a local RDAP cache, etc.) can be dropped in later without
touching the rule that consumes it. `RdapDomainAgeProvider` makes a
best-effort live lookup against the public RDAP bootstrap service and
degrades to "unknown" on any failure (unsupported TLD, timeout, no
registration event) rather than blocking the scan.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

RDAP_TIMEOUT_SECONDS = 4


@dataclass
class DomainAgeResult:
    status: str  # "recently_registered" | "moderately_aged" | "established" | "unknown"
    registered_on: str | None = None
    age_days: int | None = None


class DomainAgeProvider(ABC):
    @abstractmethod
    def lookup(self, registrable_domain: str) -> DomainAgeResult: ...


class RdapDomainAgeProvider(DomainAgeProvider):
    def lookup(self, registrable_domain: str) -> DomainAgeResult:
        try:
            response = requests.get(
                f"https://rdap.org/domain/{registrable_domain}",
                timeout=RDAP_TIMEOUT_SECONDS,
                headers={"Accept": "application/rdap+json", "User-Agent": "CyberShield-URLScanner/1.0"},
            )
            if response.status_code != 200:
                return DomainAgeResult(status="unknown")

            data = response.json()
            registration_event = next(
                (e for e in data.get("events", []) if e.get("eventAction") == "registration"),
                None,
            )
            if not registration_event or not registration_event.get("eventDate"):
                return DomainAgeResult(status="unknown")

            registered_at = datetime.fromisoformat(registration_event["eventDate"].replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - registered_at).days

            if age_days < 180:
                status = "recently_registered"
            elif age_days < 730:
                status = "moderately_aged"
            else:
                status = "established"

            return DomainAgeResult(
                status=status, registered_on=registered_at.date().isoformat(), age_days=age_days
            )
        except (requests.RequestException, ValueError, KeyError):
            return DomainAgeResult(status="unknown")


def get_domain_age_provider() -> DomainAgeProvider:
    return RdapDomainAgeProvider()
