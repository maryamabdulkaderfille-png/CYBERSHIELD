"""Report export implementation.

Provides structured PDF report generation using ReportLab, converting
read-only scan reports into executive-ready security assessment documents.
"""

import io
from abc import ABC, abstractmethod

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.utils.errors import APIError


class ReportExporter(ABC):
    @abstractmethod
    def export(self, report: dict) -> bytes: ...


class PdfReportExporter(ReportExporter):
    """Generates a professional, branded PDF security report."""

    def export(self, report: dict) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom typography
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#0284c7"),
            fontName="Helvetica-Bold",
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica",
        )

        bold_style = ParagraphStyle(
            "BodyBold",
            parent=body_style,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0f172a"),
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("CYBERSHIELD SECURITY INTELLIGENCE", subtitle_style))
        story.append(Paragraph("Phishing & Threat Analysis Report", title_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

        # 2. Metadata Grid
        scanner_type = str(report.get("scanner_type", "URL")).upper()
        report_id = str(report.get("report_id", "N/A"))
        scan_date = str(report.get("scan_date", "N/A"))[:19].replace("T", " ")
        target = str(report.get("target", "N/A"))

        meta_data = [
            [
                Paragraph("<b>Report Reference:</b>", bold_style),
                Paragraph(report_id, body_style),
                Paragraph("<b>Scanner Engine:</b>", bold_style),
                Paragraph(scanner_type, body_style),
            ],
            [
                Paragraph("<b>Assessment Date:</b>", bold_style),
                Paragraph(scan_date, body_style),
                Paragraph("<b>Scanned Target:</b>", bold_style),
                Paragraph(target[:45] + ("..." if len(target) > 45 else ""), body_style),
            ],
        ]

        meta_table = Table(meta_data, colWidths=[110, 160, 100, 170])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # 3. Security Score & Risk Classification Callout
        trust_score = int(report.get("trust_score", 0))
        risk_level = str(report.get("risk_level", "Unknown")).title()

        if "Safe" in risk_level:
            score_bg = colors.HexColor("#ecfdf5")
            score_border = colors.HexColor("#059669")
            score_color = colors.HexColor("#047857")
        elif "Low" in risk_level:
            score_bg = colors.HexColor("#eff6ff")
            score_border = colors.HexColor("#3b82f6")
            score_color = colors.HexColor("#1d4ed8")
        elif "Suspicious" in risk_level:
            score_bg = colors.HexColor("#fffbeb")
            score_border = colors.HexColor("#d97706")
            score_color = colors.HexColor("#b45309")
        else:
            score_bg = colors.HexColor("#fef2f2")
            score_border = colors.HexColor("#dc2626")
            score_color = colors.HexColor("#b91c1c")

        score_style = ParagraphStyle(
            "ScoreStyle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=score_color,
            fontName="Helvetica-Bold",
        )

        risk_badge_style = ParagraphStyle(
            "RiskBadge",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=score_color,
            fontName="Helvetica-Bold",
        )

        summary_text = report.get("summary", "No summary provided.")

        score_table_data = [
            [
                Paragraph(f"{trust_score}/100", score_style),
                Paragraph(f"<b>RISK LEVEL: {risk_level.upper()}</b><br/>{summary_text}", body_style),
            ]
        ]
        score_table = Table(score_table_data, colWidths=[120, 420])
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), score_bg),
                    ("BOX", (0, 0), (-1, -1), 1.5, score_border),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(score_table)
        story.append(Spacer(1, 14))

        # 4. Key Triggered Reasons / Threat Indicators
        findings = report.get("findings", {})
        reasons = findings.get("reasons", [])

        story.append(Paragraph("Security Assessment Summary", section_heading))
        if reasons:
            for r in reasons:
                story.append(
                    Paragraph(
                        f"• {r.lstrip('✔ ').lstrip('✖ ')}",
                        body_style,
                    )
                )
                story.append(Spacer(1, 3))
        else:
            story.append(Paragraph("No negative security indicators triggered during evaluation.", body_style))

        story.append(Spacer(1, 12))

        # 5. Technical Rule Heuristics Breakdown
        rules = findings.get("rules", [])
        if rules:
            story.append(Paragraph("Detailed Detection Rule Evaluation", section_heading))
            rule_rows = [
                [
                    Paragraph("<b>Rule / Inspection</b>", bold_style),
                    Paragraph("<b>Status</b>", bold_style),
                    Paragraph("<b>Severity</b>", bold_style),
                    Paragraph("<b>Findings & Diagnostics</b>", bold_style),
                ]
            ]
            for r in rules[:15]:
                triggered = r.get("triggered", False)
                status_str = "FLAGGED" if triggered else "PASS"
                status_color = colors.HexColor("#dc2626") if triggered else colors.HexColor("#16a34a")
                row_status_style = ParagraphStyle(
                    "RowStatus",
                    parent=body_style,
                    fontName="Helvetica-Bold",
                    textColor=status_color,
                )

                rule_rows.append(
                    [
                        Paragraph(r.get("label", r.get("rule", "")), bold_style),
                        Paragraph(status_str, row_status_style),
                        Paragraph(str(r.get("severity", "INFO")).upper(), body_style),
                        Paragraph(r.get("message", ""), body_style),
                    ]
                )

            rules_table = Table(rule_rows, colWidths=[120, 65, 65, 290])
            rules_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#cbd5e1")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(rules_table)
            story.append(Spacer(1, 14))

        # 6. Actionable Security Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            story.append(Paragraph("Actionable Recommendations", section_heading))
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 10))

        # 7. Footer / Disclaimer
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=8))
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748b"),
            alignment=1,  # Center
        )
        story.append(
            Paragraph(
                "This report was automatically compiled by the CyberShield Threat Intelligence Platform.<br/>"
                "Intended strictly for authorized cybersecurity monitoring and fraud prevention purposes.",
                footer_style,
            )
        )

        doc.build(story)
        buf.seek(0)
        return buf.getvalue()


_SUPPORTED_FORMATS = ("pdf",)


def get_exporter(export_format: str) -> ReportExporter:
    if export_format == "pdf":
        return PdfReportExporter()
    raise APIError(f"Unsupported export format: {export_format}", 422)
