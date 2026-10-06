from dataclasses import dataclass, field
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Optional
from urllib.parse import ParseResult

from app.constants import RiskLevel

__all__ = [
    "RiskLevel",
    "Severity",
    "RuleResult",
    "ScanContext",
    "ScanReport",
]


class Severity:
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RuleResult:
    """The outcome of a single detection rule.

    `impact` is the amount added to the trust score (negative for risk
    signals, zero or positive for reassuring signals). `triggered` marks
    whether this rule found something worth surfacing to the user.
    """

    rule: str
    label: str
    triggered: bool
    impact: int
    severity: str
    message: str
    detail: Optional[str] = None


@dataclass
class ScanContext:
    """Everything the rules need, parsed/resolved once and shared.

    Building this once and passing it to every rule avoids each rule
    re-parsing the URL or re-resolving DNS independently.
    """

    raw_url: str
    parsed: ParseResult
    hostname: str
    resolved_ips: list[IPv4Address | IPv6Address] = field(default_factory=list)
    dns_resolved: bool = False
    is_ip_host: bool = False


@dataclass
class ScanReport:
    trust_score: int
    risk_level: str
    reasons: list[str]
    recommendations: list[str]
    rule_results: list[RuleResult]
    scanned_at: datetime
