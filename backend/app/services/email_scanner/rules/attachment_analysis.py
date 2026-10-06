"""Flags dangerous attachment file types and double-extension tricks
(e.g. `invoice.pdf.exe`, `image.jpg.scr` — the visible "safe" extension is
fake; the real, executed extension is the last one)."""

from app.services.email_scanner.types import AttachmentFinding, EmailContext, RuleResult, Severity

DANGEROUS_EXTENSIONS = {
    ".exe",
    ".js",
    ".scr",
    ".vbs",
    ".bat",
    ".cmd",
    ".jar",
    ".ps1",
    ".msi",
    ".com",
    ".pif",
    ".hta",
    ".wsf",
}

SAFE_LOOKING_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".txt", ".zip"}


def classify_attachment(filename: str) -> AttachmentFinding:
    lower = filename.lower().strip()
    parts = lower.rsplit(".", 2)  # up to two suffixes, e.g. ["invoice", "pdf", "exe"]

    if len(parts) == 3 and f".{parts[1]}" in SAFE_LOOKING_EXTENSIONS and f".{parts[2]}" in DANGEROUS_EXTENSIONS:
        return AttachmentFinding(
            filename=filename,
            is_dangerous=True,
            reason=f"Double extension disguises a dangerous '.{parts[2]}' file as '.{parts[1]}'.",
        )

    for ext in DANGEROUS_EXTENSIONS:
        if lower.endswith(ext):
            return AttachmentFinding(
                filename=filename, is_dangerous=True, reason=f"Dangerous attachment type ({ext})."
            )

    return AttachmentFinding(filename=filename, is_dangerous=False, reason=None)


def evaluate(ctx: EmailContext, findings: list[AttachmentFinding] | None = None) -> RuleResult:
    """`findings` lets the engine pass in an already-computed classification
    instead of classifying every attachment twice. Falls back to computing
    them when called standalone (e.g. in tests)."""
    if not ctx.attachments:
        return RuleResult(
            rule="attachment_analysis",
            label="Attachment Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No attachments found.",
        )

    if findings is None:
        findings = [classify_attachment(a.filename) for a in ctx.attachments]
    dangerous = [f for f in findings if f.is_dangerous]

    if not dangerous:
        return RuleResult(
            rule="attachment_analysis",
            label="Attachment Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message=f"{len(findings)} attachment(s) found, none with dangerous extensions.",
        )

    names = ", ".join(f.filename for f in dangerous)
    reasons = "; ".join(f.reason for f in dangerous if f.reason)
    return RuleResult(
        rule="attachment_analysis",
        label="Attachment Analysis",
        triggered=True,
        impact=-35,
        severity=Severity.CRITICAL,
        message=f"Dangerous attachment(s) found: {reasons}",
        detail=names,
    )
