"""Analyzes HTML email bodies for classic phishing techniques: hidden
content, embedded scripts, credential-harvesting forms, and obfuscation.

Uses Python's stdlib `html.parser.HTMLParser` to walk tags safely — the HTML
is only ever inspected as text, never rendered or executed.
"""

import re

from app.services.email_scanner.types import EmailContext, RuleResult, Severity

_HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0\b", re.IGNORECASE)
_NUMERIC_ENTITY_RE = re.compile(r"&#x?[0-9a-fA-F]+;")


class _HtmlSignalScanner:
    def __init__(self):
        self.has_script = False
        self.has_form = False
        self.hidden_element_count = 0
        self.external_resource_count = 0

    def scan(self, html_content: str) -> None:
        parser = self._build_parser()
        try:
            parser.feed(html_content)
        except Exception:
            pass

    def _build_parser(self):
        from html.parser import HTMLParser

        outer = self

        class _Parser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                tag_lower = tag.lower()

                if tag_lower == "script":
                    outer.has_script = True
                elif tag_lower == "form":
                    outer.has_form = True

                style = attrs_dict.get("style", "") or ""
                if _HIDDEN_STYLE_RE.search(style):
                    outer.hidden_element_count += 1

                if tag_lower in {"img", "iframe"} and attrs_dict.get("src", "").startswith(("http://", "https://")):
                    outer.external_resource_count += 1

        return _Parser()


def evaluate(ctx: EmailContext) -> RuleResult:
    if not ctx.body_html:
        return RuleResult(
            rule="html_analysis",
            label="HTML Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Email has no HTML content to analyze.",
        )

    scanner = _HtmlSignalScanner()
    scanner.scan(ctx.body_html)

    findings: list[str] = []
    impact = 0
    severity = Severity.INFO

    if scanner.has_script:
        findings.append("contains embedded JavaScript")
        impact -= 25
        severity = Severity.CRITICAL

    if scanner.has_form:
        findings.append("contains an embedded form (possible credential harvesting)")
        impact -= 20
        severity = Severity.CRITICAL if severity != Severity.CRITICAL else severity

    if scanner.hidden_element_count:
        findings.append(f"contains {scanner.hidden_element_count} hidden/invisible element(s)")
        impact -= 12
        if severity not in {Severity.CRITICAL}:
            severity = Severity.HIGH

    if scanner.external_resource_count >= 3:
        findings.append(f"loads {scanner.external_resource_count} external resources (possible tracking)")
        impact -= 6
        if severity == Severity.INFO:
            severity = Severity.LOW

    numeric_entities = len(_NUMERIC_ENTITY_RE.findall(ctx.body_html))
    if numeric_entities >= 20:
        findings.append("text appears obfuscated with excessive character encoding")
        impact -= 10
        if severity == Severity.INFO:
            severity = Severity.MEDIUM

    if not findings:
        return RuleResult(
            rule="html_analysis",
            label="HTML Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="HTML content does not contain suspicious patterns.",
        )

    return RuleResult(
        rule="html_analysis",
        label="HTML Analysis",
        triggered=True,
        impact=impact,
        severity=severity,
        message="Suspicious HTML: " + "; ".join(findings) + ".",
    )
