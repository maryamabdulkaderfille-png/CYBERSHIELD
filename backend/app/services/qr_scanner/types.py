from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.constants import RiskLevel

__all__ = [
    "RiskLevel",
    "Severity",
    "ContentType",
    "RuleResult",
    "QRContext",
    "QRReport",
]


class Severity:
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentType:
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WIFI = "wifi"
    CRYPTO = "crypto"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"
    ALL = (URL, EMAIL, PHONE, SMS, WIFI, CRYPTO, PLAIN_TEXT, UNKNOWN)


@dataclass
class RuleResult:
    """Mirrors url_scanner/email_scanner's RuleResult — kept as its own
    independent dataclass so the QR scanner has no structural dependency on
    either of the other two scanners' internal types, only on their public
    functions (`scan_url`, `analyze_email`, etc.)."""

    rule: str
    label: str
    triggered: bool
    impact: int
    severity: str
    message: str
    detail: Optional[str] = None


@dataclass
class QRContext:
    raw_content: str
    content_type: str
    parsed_fields: dict = field(default_factory=dict)


@dataclass
class QRReport:
    content_type: str
    raw_content: str
    parsed_fields: dict
    trust_score: int
    risk_level: str
    reasons: list[str]
    recommendations: list[str]
    rule_results: list[RuleResult]
    scanned_at: datetime
