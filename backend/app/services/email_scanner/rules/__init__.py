from app.services.email_scanner.rules import (
    attachment_analysis,
    display_name_impersonation,
    grammar_heuristics,
    greeting_analysis,
    html_analysis,
    link_analysis,
    sender_analysis,
    subject_analysis,
    threat_language,
    urgency_detection,
)

# Order controls the order reasons appear in for the user-facing report.
RULES = [
    sender_analysis,
    display_name_impersonation,
    subject_analysis,
    greeting_analysis,
    urgency_detection,
    threat_language,
    link_analysis,
    attachment_analysis,
    html_analysis,
    grammar_heuristics,
]
