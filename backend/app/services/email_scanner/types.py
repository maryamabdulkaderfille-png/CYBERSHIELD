from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.constants import RiskLevel

__all__ = ["RiskLevel", "Severity", "RuleResult", "EmailAttachment", "EmailContext", "LinkFinding", "AttachmentFinding", "EmailReport"]


class Severity:
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RuleResult:
    """The outcome of a single detection rule. Mirrors
    app.services.url_scanner.types.RuleResult — kept as a separate,
    independent dataclass (rather than importing the URL scanner's) so the
    email scanner has no structural dependency on the URL scanner's internal
    types, only on its public `quick_classify` function."""

    rule: str
    label: str
    triggered: bool
    impact: int
    severity: str
    message: str
    detail: Optional[str] = None


@dataclass
class EmailAttachment:
    filename: str
    content_type: str | None = None


@dataclass
class EmailContext:
    """Everything the rules need, parsed once and shared."""

    sender_display_name: str | None
    sender_email: str | None
    subject: str | None
    body_text: str
    body_html: str | None
    links: list[str] = field(default_factory=list)
    attachments: list[EmailAttachment] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    parse_defects: list[str] = field(default_factory=list)


@dataclass
class LinkFinding:
    url: str
    trust_score: int
    risk: str


@dataclass
class AttachmentFinding:
    filename: str
    is_dangerous: bool
    reason: str | None


@dataclass
class EmailReport:
    trust_score: int
    risk_level: str
    reasons: list[str]
    recommendations: list[str]
    rule_results: list[RuleResult]
    links: list[LinkFinding]
    attachments: list[AttachmentFinding]
    sender_display_name: str | None
    sender_email: str | None
    subject: str | None
    scanned_at: datetime
