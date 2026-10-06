import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def build_presentation(output_path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Exact CyberShield System Brand Palette
    WHITE = RGBColor(255, 255, 255)
    NAVY_TITLE = RGBColor(10, 14, 26)       # #0A0E1A (CyberShield Navy-900)
    NAVY_SUB = RGBColor(59, 130, 246)       # #3B82F6 (CyberShield Brand Blue)
    BRAND_CYAN = RGBColor(34, 211, 238)     # #22D3EE (CyberShield Brand Cyan)
    CYAN_DARK = RGBColor(2, 132, 199)       # #0284C7 (Readable Cyan text)
    GOLD_ACCENT = RGBColor(59, 130, 246)    # #3B82F6 (CyberShield Blue accent)
    TEXT_MAIN = RGBColor(15, 23, 42)        # #0F172A (Deep Slate for max readability)
    TEXT_MUTED = RGBColor(100, 116, 139)    # #64748B (Muted Slate)
    CARD_BG = RGBColor(248, 250, 252)       # #F8FAFC (Clean Light Surface)
    CARD_BORDER = RGBColor(226, 232, 240)   # #E2E8F0 (Crisp Border)
    GREEN_SUCCESS = RGBColor(34, 197, 94)   # #22C55E (CyberShield Safe Green)
    DANGER_RED = RGBColor(239, 68, 68)      # #EF4444 (CyberShield Danger Red)

    ICON_DIR = "ppt_assets"

    def add_standard_header(slide, number_str, title_text, icon_name=None):
        # Top formal stripe
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = NAVY_TITLE
        stripe.line.fill.background()

        # Icon if provided
        icon_x = Inches(0.8)
        text_x = Inches(0.8)
        if icon_name and os.path.exists(f"{ICON_DIR}/{icon_name}"):
            slide.shapes.add_picture(f"{ICON_DIR}/{icon_name}", Inches(0.8), Inches(0.4), Inches(0.85), Inches(0.85))
            text_x = Inches(1.8)

        # Header Title
        title_box = slide.shapes.add_textbox(text_x, Inches(0.35), Inches(10.5), Inches(0.95))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.text = f"{number_str}  {title_text}" if number_str else title_text
        p.font.name = "Arial"
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = NAVY_TITLE

        # Subtitle / Department line
        sub_p = tf.add_paragraph()
        sub_p.text = "East Africa University • Department of Computer Science • Final-Year Defense"
        sub_p.font.name = "Arial"
        sub_p.font.size = Pt(10)
        sub_p.font.color.rgb = TEXT_MUTED

        # Elegant gold divider rule
        rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.42), Inches(11.733), Inches(0.025))
        rule.fill.solid()
        rule.fill.fore_color.rgb = GOLD_ACCENT
        rule.line.fill.background()

        # Footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.3))
        ftf = footer_box.text_frame
        ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
        fp = ftf.paragraphs[0]
        fp.text = "CyberShield: Web-Based Phishing Detection System | Candidate: Maryam Abdulkader Hassan Filla (EAUGRW0004981)"
        fp.font.name = "Arial"
        fp.font.size = Pt(9.5)
    add_header = add_standard_header

    # ==========================================
    # SLIDE 1: TITLE SLIDE
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)

    # Top formal bar
    top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_TITLE
    top_bar.line.fill.background()

    # University icon / crest
    if os.path.exists(f"{ICON_DIR}/shield.png"):
        s1.shapes.add_picture(f"{ICON_DIR}/shield.png", Inches(6.066), Inches(0.7), Inches(1.2), Inches(1.2))

    # University Name
    u_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.333), Inches(0.8))
    utf = u_box.text_frame
    up = utf.paragraphs[0]
    up.text = "EAST AFRICA UNIVERSITY"
    up.alignment = PP_ALIGN.CENTER
    up.font.name = "Arial"
    up.font.size = Pt(17)
    up.font.bold = True
    up.font.color.rgb = NAVY_TITLE

    up2 = utf.add_paragraph()
    up2.text = "FACULTY OF TECHNOLOGY & ENGINEERING • DEPARTMENT OF COMPUTER SCIENCE"
    up2.alignment = PP_ALIGN.CENTER
    up2.font.name = "Arial"
    up2.font.size = Pt(11)
    up2.font.bold = True
    up2.font.color.rgb = GOLD_ACCENT

    # Main Project Title Box
    t_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.95), Inches(11.333), Inches(1.8))
    ttf = t_box.text_frame
    ttf.word_wrap = True
    tp1 = ttf.paragraphs[0]
    tp1.text = "Design and Implementation of a\nWeb-Based Phishing Detection System"
    tp1.alignment = PP_ALIGN.CENTER
    tp1.font.name = "Arial"
    tp1.font.size = Pt(32)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY_TITLE

    tp2 = ttf.add_paragraph()
    tp2.text = "CyberShield Platform"
    tp2.alignment = PP_ALIGN.CENTER
    tp2.font.name = "Arial"
    tp2.font.size = Pt(15)
    tp2.font.bold = True
    tp2.font.color.rgb = NAVY_SUB

    # Student metadata card
    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.2), Inches(4.9), Inches(6.933), Inches(1.7))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = CARD_BORDER
    card.line.width = Pt(1.2)

    ctf = card.text_frame
    ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
    cp1 = ctf.paragraphs[0]
    cp1.text = "Bachelor of Computer Science — Final-Year Thesis Defense"
    cp1.alignment = PP_ALIGN.CENTER
    cp1.font.name = "Arial"
    cp1.font.size = Pt(12)
    cp1.font.bold = True
    cp1.font.color.rgb = GOLD_ACCENT

    cp2 = ctf.add_paragraph()
    cp2.text = "Candidate: Maryam Abdulkader Hassan Filla"
    cp2.alignment = PP_ALIGN.CENTER
    cp2.font.name = "Arial"
    cp2.font.size = Pt(14)
    cp2.font.bold = True
    cp2.font.color.rgb = TEXT_MAIN

    cp3 = ctf.add_paragraph()
    cp3.text = "Student ID: EAUGRW0004981   •   Academic Year: October 2026"
    cp3.alignment = PP_ALIGN.CENTER
    cp3.font.name = "Arial"
    cp3.font.size = Pt(11)
    cp3.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 2: PRESENTATION OUTLINE
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "", "Presentation Outline", "book.png")

    items_col1 = [
        ("1", "Introduction / Background"),
        ("2", "Problem Statement"),
        ("3", "Objectives of the Study"),
        ("4", "Literature Review"),
        ("5", "Methodology")
    ]
    items_col2 = [
        ("6", "System Design"),
        ("7", "Implementation"),
        ("8", "Testing & Results"),
        ("9", "Discussion"),
        ("10", "Conclusion & Recommendations")
    ]

    for i, (num, text) in enumerate(items_col1):
        y = Inches(1.9 + i * 0.95)
        # badge
        b = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.4), y, Inches(0.65), Inches(0.65))
        b.fill.solid()
        b.fill.fore_color.rgb = NAVY_TITLE
        b.line.fill.background()
        btf = b.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]
        bp.text = num
        bp.alignment = PP_ALIGN.CENTER
        bp.font.name = "Arial"
        bp.font.size = Pt(15)
        bp.font.bold = True
        bp.font.color.rgb = WHITE

        tb = s2.shapes.add_textbox(Inches(2.25), y + Inches(0.08), Inches(4.5), Inches(0.55))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = "Arial"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN

    for i, (num, text) in enumerate(items_col2):
        y = Inches(1.9 + i * 0.95)
        # badge
        b = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.4), y, Inches(0.65), Inches(0.65))
        b.fill.solid()
        b.fill.fore_color.rgb = GOLD_ACCENT
        b.line.fill.background()
        btf = b.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]
        bp.text = num
        bp.alignment = PP_ALIGN.CENTER
        bp.font.name = "Arial"
        bp.font.size = Pt(15)
        bp.font.bold = True
        bp.font.color.rgb = WHITE

        tb = s2.shapes.add_textbox(Inches(8.25), y + Inches(0.08), Inches(4.5), Inches(0.55))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = "Arial"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 3: 1. INTRODUCTION / BACKGROUND
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "1.", "Introduction / Background", "shield.png")

    intro_points = [
        ("The Phishing Landscape", "Phishing remains the #1 initial attack vector worldwide. Over 94% of organizational data breaches originate through deceptive communications, credential harvesting links, and social engineering."),
        ("Multi-Vector Threat Evolution", "Modern attacks have expanded beyond basic email spam to deceptive URLs and QR code phishing (Quishing) designed to bypass traditional perimeter security controls."),
        ("Accessible Protection Need", "There is a pressing demand for an accessible, transparent, and multi-channel security platform that protects individuals, students, and small enterprises with real-time heuristic inspection.")
    ]

    for i, (title, desc) in enumerate(intro_points):
        x = Inches(0.8 + i * 3.95)
        card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.9), Inches(3.75), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.2)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.3)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(16)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_TITLE

        p2 = ctf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.name = "Arial"
        p2.font.size = Pt(13)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 4: 2. PROBLEM STATEMENT
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "2.", "Problem Statement", "alert.png")

    # Left: Empirical Statistic Box
    stat_card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(4.3), Inches(4.7))
    stat_card.fill.solid()
    stat_card.fill.fore_color.rgb = CARD_BG
    stat_card.line.color.rgb = CARD_BORDER
    stat_card.line.width = Pt(1.2)

    stf = stat_card.text_frame
    stf.word_wrap = True
    stf.margin_left = stf.margin_right = stf.margin_top = Inches(0.35)

    sp1 = stf.paragraphs[0]
    sp1.text = "CRITICAL THREAT SCALE"
    sp1.font.name = "Arial"
    sp1.font.size = Pt(12)
    sp1.font.bold = True
    sp1.font.color.rgb = GOLD_ACCENT

    sp2 = stf.add_paragraph()
    sp2.text = "971,181"
    sp2.font.name = "Arial"
    sp2.font.size = Pt(44)
    sp2.font.bold = True
    sp2.font.color.rgb = NAVY_TITLE

    sp3 = stf.add_paragraph()
    sp3.text = "Confirmed phishing attacks recorded by APWG in a single quarter — up 13.8%."
    sp3.font.name = "Arial"
    sp3.font.size = Pt(12)
    sp3.font.color.rgb = TEXT_MUTED

    sp4 = stf.add_paragraph()
    sp4.text = "\nCore Reality:\nPhishing detection technology exists, but accessible, automated, and explainable phishing protection does not."
    sp4.font.name = "Arial"
    sp4.font.size = Pt(12.5)
    sp4.font.bold = True
    sp4.font.color.rgb = NAVY_SUB

    # Right: Limitations & The Gap
    gap_card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.4), Inches(1.9), Inches(7.133), Inches(4.7))
    gap_card.fill.solid()
    gap_card.fill.fore_color.rgb = WHITE
    gap_card.line.color.rgb = CARD_BORDER
    gap_card.line.width = Pt(1.2)

    gtf = gap_card.text_frame
    gtf.word_wrap = True
    gtf.margin_left = gtf.margin_right = gtf.margin_top = Inches(0.35)

    gp1 = gtf.paragraphs[0]
    gp1.text = "The Existing Dilemma for Users:"
    gp1.font.name = "Arial"
    gp1.font.size = Pt(17)
    gp1.font.bold = True
    gp1.font.color.rgb = NAVY_TITLE

    prob_items = [
        ("Blacklist-Only Checkers (Reactive Gap):", "Fast and free, but blind to a phishing site in the hours or days before it is publicly reported — precisely the window where most victims are caught."),
        ("Enterprise Software (Accessibility Gap):", "Genuinely proactive, but priced and configured solely for enterprise IT departments — out of reach for individuals, students, and small businesses."),
        ("The Resulting Problem:", "Ordinary users have no transparent, explainable, zero-cost alternative offering multi-channel protection (URL, Email, and QR).")
    ]

    for title, text in prob_items:
        pt = gtf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.name = "Arial"
        pt.font.size = Pt(13)
        pt.font.bold = True
        pt.font.color.rgb = NAVY_SUB
        pd = gtf.add_paragraph()
        pd.text = f"  {text}"
        pd.font.name = "Arial"
        pd.font.size = Pt(12)
        pd.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 5: 3. OBJECTIVES OF THE STUDY
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "3.", "Objectives of the Study", "target.png")

    # General Objective Box
    gen_card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.15))
    gen_card.fill.solid()
    gen_card.fill.fore_color.rgb = CARD_BG
    gen_card.line.color.rgb = GOLD_ACCENT
    gen_card.line.width = Pt(1.5)
    gtf = gen_card.text_frame
    gtf.word_wrap = True
    gtf.margin_left = gtf.margin_right = gtf.margin_top = Inches(0.2)
    gp1 = gtf.paragraphs[0]
    gp1.text = "GENERAL OBJECTIVE"
    gp1.font.name = "Arial"
    gp1.font.size = Pt(11)
    gp1.font.bold = True
    gp1.font.color.rgb = GOLD_ACCENT

    gp2 = gtf.add_paragraph()
    gp2.text = "Design and implement a web-based phishing detection system enabling real-time URL verification, email analysis, QR code inspection, and browser automation."
    gp2.font.name = "Arial"
    gp2.font.size = Pt(13)
    gp2.font.bold = True
    gp2.font.color.rgb = NAVY_TITLE

    # 6 Specific Objectives (3x2 Grid)
    objs = [
        ("1. Review Existing Techniques", "Analyze blacklist, heuristic, and ML-based approaches to identify real-time latency gaps."),
        ("2. Build URL Analysis Engine", "Construct internal blacklist + rule-based heuristic scoring engine (11 rules)."),
        ("3. Secure User Authentication", "Implement registration, JWT sessions, Bcrypt hashing, and role-based access control."),
        ("4. Accuracy Evaluation", "Examine detection behavior, accuracy boundaries, and test suite reliability."),
        ("5. Platform Security Measures", "Incorporate defense-in-depth: Input validation, rate limiting, and SSRF guards."),
        ("6. Browser Extension", "Deploy a Manifest V3 Chromium extension for passive, zero-click browsing protection.")
    ]

    for i, (title, desc) in enumerate(objs):
        row = i // 3
        col = i % 3
        x = Inches(0.8 + col * 3.95)
        y = Inches(3.15 + row * 1.85)

        c = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(3.75), Inches(1.65))
        c.fill.solid()
        c.fill.fore_color.rgb = WHITE
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1.2)

        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.18)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_SUB

        p2 = ctf.add_paragraph()
        p2.text = desc
        p2.font.name = "Arial"
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 6: 4. LITERATURE REVIEW
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "4.", "Literature Review", "book.png")

    # Table comparing the 3 approaches
    table_shape = s6.shapes.add_table(4, 4, Inches(0.8), Inches(1.85), Inches(11.733), Inches(4.8))
    table = table_shape.table

    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(3.1)
    table.columns[2].width = Inches(3.1)
    table.columns[3].width = Inches(3.333)

    hdrs = ["Technique", "Key Strengths", "Critical Weaknesses", "CyberShield Synthesis"]
    for j, h in enumerate(hdrs):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_TITLE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = "Arial"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = WHITE

    rows_data = [
        ("Blacklist-Based\n(e.g. Safe Browsing)", "• Very low false positives\n• Instant hash lookup\n• Low server compute", "• Zero-hour window blindness\n• Ineffective against newly registered domains\n• Delayed crowdsourced reporting", "Incorporated as Phase 2 internal blacklist for known malicious domains."),
        ("Machine Learning\nClassifiers (ML/AI)", "• Generalizes across features\n• Detects novel patterns\n• Adaptive with training", "• Black-box decisions (no explainability)\n• Heavy inference compute overhead\n• Prone to concept drift & evasion", "Identified for future hybrid NLP layer; bypassed for initial sub-second extension response."),
        ("Rule-Based Heuristic\nAnalysis (CyberShield)", "• Sub-second response (<270ms)\n• Full explainability (Named rules)\n• Transparent penalties\n• Zero third-party API lag", "• Requires careful weight calibration\n• Dependent on heuristic rule coverage\n• Potential false alarms on rare TLDs", "Primary detection engine: 29 rules across URL, Email MIME, and QR payload classification.")
    ]

    for i, r in enumerate(rows_data):
        for j, val in enumerate(r):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if i % 2 == 0 else WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = "Arial"
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 7: 5. METHODOLOGY
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "5.", "Research Methodology", "method.png")

    methods = [
        ("Research Design:\nDesign Science Research", "Hevner et al. (2004)\n\nFocuses on building and evaluating an innovative software artefact to solve an explicit problem, rather than population opinion surveys."),
        ("Development Method:\nAgile & Incremental", "Beck et al. (2001)\n\nArchitected across 8 modular development increments (Phases 1–8). Each engine, database schema, and interface was built and verified iteratively."),
        ("Requirements &\nGap Analysis", "Specification Instrument\n\nRequirements synthesized from literature review gap analysis and Anti-Phishing Working Group (APWG) threat landscape telemetry."),
        ("Evaluation &\nVerification Strategy", "Automated Test Harness\n\nEvaluated using a 562-test automated suite (Pytest + Vitest) alongside live accumulated platform usage telemetry across multiple users.")
    ]

    for i, (title, desc) in enumerate(methods):
        x = Inches(0.8 + i * 2.98)
        card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.9), Inches(2.8), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.2)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.25)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_TITLE

        p2 = ctf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.name = "Arial"
        p2.font.size = Pt(11.5)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 8: 6. SYSTEM DESIGN
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "6.", "System Design", "layers.png")

    layers = [
        ("1. Client Layer (Presentation)", "React 18 Single Page Application (Vite + TypeScript) + Chromium Manifest V3 Browser Extension.\nProvides real-time scan interfaces, full-page blocking overlays, and unified Scan Center dashboards."),
        ("2. Application Layer (Logic & Auth)", "Python Flask REST API (/api/v1). Manages routing, rate limiting (Flask-Limiter), JWT access/refresh lifecycles,\nand Role-Based Access Control (RBAC) permission matrices."),
        ("3. Detection Engine Layer (Core Logic)", "Modular heuristic inspection engines: URL Scanner (11 rules), Email Analyzer (10 rules for SPF/DKIM/MIME),\nand QR Decoder (8 payload handlers). Shared core prevents code duplication."),
        ("4. Data Layer (Persistence)", "PostgreSQL 16 relational database (14 production tables) ensuring ACID compliance and scan indexing,\nwith SQLite in-memory database used for deterministic automated testing.")
    ]

    for i, (title, body) in enumerate(layers):
        y = Inches(1.85 + i * 1.25)
        card = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.733), Inches(1.15))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.2)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = Inches(0.3)
        ctf.margin_top = Inches(0.12)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_TITLE

        p2 = ctf.add_paragraph()
        p2.text = body
        p2.font.name = "Arial"
        p2.font.size = Pt(11.5)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 9: 7. IMPLEMENTATION
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "7.", "System Implementation", "code.png")

    # Formula Box across top
    f_box = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.05))
    f_box.fill.solid()
    f_box.fill.fore_color.rgb = NAVY_TITLE
    f_box.line.fill.background()
    ftf = f_box.text_frame
    ftf.word_wrap = True
    fp1 = ftf.paragraphs[0]
    fp1.text = "Core Scoring Formula:  Trust Score = 100 + Σ (rule impacts)  [Clamped: 0 – 100]"
    fp1.alignment = PP_ALIGN.CENTER
    fp1.font.name = "Arial"
    fp1.font.size = Pt(14)
    fp1.font.bold = True
    fp1.font.color.rgb = WHITE

    fp2 = ftf.add_paragraph()
    fp2.text = "Risk Categories: Safe (90–100)  |  Low Risk (70–89)  |  Suspicious (40–69)  |  Dangerous (0–39)"
    fp2.alignment = PP_ALIGN.CENTER
    fp2.font.name = "Arial"
    fp2.font.size = Pt(11.5)
    fp2.font.bold = True
    fp2.font.color.rgb = GOLD_ACCENT

    # 3 Implementation Pillars
    impls = [
        ("Three Detection Channels", "• URL Scanner (11 Rules):\n  IP hosts, typosquatting, TLS check,\n  domain age, suspicious TLDs.\n• Email Scanner (10 Rules):\n  SPF/DKIM headers, sender spoofing,\n  urgency keywords, attachments.\n• QR Scanner (8 Handlers):\n  Matrix decoding piped into URL engine."),
        ("Browser Extension (MV3)", "• Zero-Effort Automation:\n  Intercepts page visits automatically.\n• Sub-Second Speed:\n  267ms average latency stops user before\n  credentials can be typed.\n• Full-Page Overlay:\n  Blocks dangerous sites physically.\n• Privacy Mode: In-memory evaluation."),
        ("Enterprise Administration", "• Role-Based Access Control (RBAC):\n  Strict Admin vs User permissions.\n• Dynamic Rule Toggling:\n  Enable/disable rules without redeploying.\n• Immutable Audit Logging:\n  Non-repudiation logging with IPs.\n• Security by Design:\n  Bcrypt, Rate Limiting, CSRF & SSRF.")
    ]

    for i, (title, content) in enumerate(impls):
        x = Inches(0.8 + i * 3.95)
        c = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.05), Inches(3.75), Inches(3.7))
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1.2)

        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.2)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_SUB

        p2 = ctf.add_paragraph()
        p2.text = f"\n{content}"
        p2.font.name = "Arial"
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 10: 8. TESTING & RESULTS
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "8.", "Testing & Results", "test.png")

    # Left: Automated Testing Results
    t_box = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(5.6), Inches(4.8))
    t_box.fill.solid()
    t_box.fill.fore_color.rgb = CARD_BG
    t_box.line.color.rgb = CARD_BORDER
    t_box.line.width = Pt(1.2)
    ttf = t_box.text_frame
    ttf.word_wrap = True
    ttf.margin_left = ttf.margin_right = ttf.margin_top = Inches(0.3)

    tp1 = ttf.paragraphs[0]
    tp1.text = "Automated Test Suite Verification"
    tp1.font.name = "Arial"
    tp1.font.size = Pt(15)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY_TITLE

    tp2 = ttf.add_paragraph()
    tp2.text = "562 of 562 Tests Passed (100%)"
    tp2.font.name = "Arial"
    tp2.font.size = Pt(20)
    tp2.font.bold = True
    tp2.font.color.rgb = GREEN_SUCCESS

    tp3 = ttf.add_paragraph()
    tp3.text = "\n• Backend Pytest Suite: 473 tests\n  Exercises API routes, authentication, rate limiting, and rules.\n• Browser Vitest Suite: 89 tests\n  Verifies extension lifecycle, message passing, and caching.\n\nWorked Example:\nURL: http://45.33.32.156/paypal-verify-account\nResult: 31 / 100 (DANGEROUS)\nRules: Raw IP host (-25), Brand impersonation (-30), Plain HTTP (-15)."
    tp3.font.name = "Arial"
    tp3.font.size = Pt(11.5)
    tp3.font.color.rgb = TEXT_MAIN

    # Right: Live Platform Telemetry
    p_box = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.9), Inches(5.633), Inches(4.8))
    p_box.fill.solid()
    p_box.fill.fore_color.rgb = CARD_BG
    p_box.line.color.rgb = CARD_BORDER
    p_box.line.width = Pt(1.2)
    ptf = p_box.text_frame
    ptf.word_wrap = True
    ptf.margin_left = ptf.margin_right = ptf.margin_top = Inches(0.3)

    pp1 = ptf.paragraphs[0]
    pp1.text = "Live Platform Usage Telemetry"
    pp1.font.name = "Arial"
    pp1.font.size = Pt(15)
    pp1.font.bold = True
    pp1.font.color.rgb = NAVY_TITLE

    pp2 = ptf.add_paragraph()
    pp2.text = "472 Real Accumulated Scans"
    pp2.font.name = "Arial"
    pp2.font.size = Pt(20)
    pp2.font.bold = True
    pp2.font.color.rgb = NAVY_SUB

    pp3 = ptf.add_paragraph()
    pp3.text = "\n• Automatic Detection: 448 / 472 (95%)\n  Scans originated passively via browser extension.\n• Performance Latency: 267.79 ms\n  Sub-second API response time preserves browsing speed.\n• Mean Trust Score: 90.8 across live evaluation.\n• Classification: 261 Safe, 194 Low Risk, 11 Suspicious, 6 Dangerous.\n• Platform Deployment: 31 registered users, 2 admins, 16 blocked attacks."
    pp3.font.name = "Arial"
    pp3.font.size = Pt(11.5)
    pp3.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 11: 9. DISCUSSION
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "9.", "Discussion", "discuss.png")

    discussions = [
        ("Objectives Evaluation (5 of 6 Met)", "Five of the six specific research objectives were fully achieved. Objective 4 (accuracy benchmarking against a static labelled dataset) was not met because no fixed ground-truth dataset was compiled; reliability was measured via 562 automated tests instead. Reliability and accuracy represent distinct properties."),
        ("Empirical Validation of Automation", "The observation that 95% of scans originated via the browser extension confirms the central hypothesis: end-user cybersecurity must be automated. Users rarely copy-paste links manually into checkers during fast-paced browsing."),
        ("Explainability as a Security Core", "By implementing traceable rule penalties, verdicts provide clear justifications ('Raw IP host', 'Sender mismatch') rather than opaque black-box scores, directly improving user security awareness."),
        ("Identified System Limitations", "Current heuristics inspect static patterns and headers. They do not execute obfuscated JavaScript in an isolated virtual sandbox, and password-protected archives cannot be decrypted without user keys.")
    ]

    for i, (title, body) in enumerate(discussions):
        row = i // 2
        col = i % 2
        x = Inches(0.8 + col * 5.95)
        y = Inches(1.9 + row * 2.45)

        card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.75), Inches(2.25))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.2)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.2)
        cp1 = ctf.paragraphs[0]
        cp1.text = title
        cp1.font.name = "Arial"
        cp1.font.size = Pt(14)
        cp1.font.bold = True
        cp1.font.color.rgb = NAVY_TITLE

        cp2 = ctf.add_paragraph()
        cp2.text = f"\n{body}"
        cp2.font.name = "Arial"
        cp2.font.size = Pt(11)
        cp2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 12: 10. CONCLUSION & RECOMMENDATIONS
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "10.", "Conclusion & Recommendations", "grad.png")

    # Conclusion Card
    conc_card = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(11.733), Inches(1.8))
    conc_card.fill.solid()
    conc_card.fill.fore_color.rgb = CARD_BG
    conc_card.line.color.rgb = NAVY_TITLE
    conc_card.line.width = Pt(1.5)
    ctf = conc_card.text_frame
    ctf.word_wrap = True
    ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.25)

    cp1 = ctf.paragraphs[0]
    cp1.text = "RESEARCH CONCLUSION"
    cp1.font.name = "Arial"
    cp1.font.size = Pt(13)
    cp1.font.bold = True
    cp1.font.color.rgb = NAVY_TITLE

    cp2 = ctf.add_paragraph()
    cp2.text = "CyberShield demonstrates that transparent, explainable, and multi-vector phishing protection is achievable without enterprise licensing barriers. The system operates reliably, passes 100% of its 562 automated tests, and delivers accessible security across Web, Email, QR, and Browser Extension channels."
    cp2.font.name = "Arial"
    cp2.font.size = Pt(12)
    cp2.font.color.rgb = TEXT_MAIN

    # 3 Future Recommendations
    recs = [
        ("1. Benchmark Accuracy Evaluation", "Conduct evaluation against balanced PhishTank and verified legitimate datasets to compute formal Precision, Recall, and False Positive rates."),
        ("2. Hybrid NLP Model Integration", "Integrate a lightweight NLP classifier to detect semantic spear-phishing cues alongside heuristic rules without sacrificing sub-second latency."),
        ("3. Dynamic Sandboxing & Mobile Apps", "Incorporate headless browser execution for DOM inspection and publish dedicated mobile browser extensions and apps.")
    ]

    for i, (title, desc) in enumerate(recs):
        x = Inches(0.8 + i * 3.95)
        c = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.9), Inches(3.75), Inches(2.8))
        c.fill.solid()
        c.fill.fore_color.rgb = WHITE
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1.2)

        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.2)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = GOLD_ACCENT

        p2 = ctf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.name = "Arial"
        p2.font.size = Pt(11.5)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 13: THANK YOU / Q&A
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)

    top_bar = s13.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_TITLE
    top_bar.line.fill.background()

    card_ty = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(2.5), Inches(1.6), Inches(8.333), Inches(4.5))
    card_ty.fill.solid()
    card_ty.fill.fore_color.rgb = CARD_BG
    card_ty.line.color.rgb = CARD_BORDER
    card_ty.line.width = Pt(1.5)

    tytf = card_ty.text_frame
    tytf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tp1 = tytf.paragraphs[0]
    tp1.text = "Thank You!"
    tp1.alignment = PP_ALIGN.CENTER
    tp1.font.name = "Arial"
    tp1.font.size = Pt(38)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY_TITLE

    tp2 = tytf.add_paragraph()
    tp2.text = "Questions & Answers (Q&A)"
    tp2.alignment = PP_ALIGN.CENTER
    tp2.font.name = "Arial"
    tp2.font.size = Pt(18)
    tp2.font.bold = True
    tp2.font.color.rgb = GOLD_ACCENT

    tp3 = tytf.add_paragraph()
    tp3.text = "\nCyberShield: Design and Implementation of a Web-Based Phishing Detection System\nCandidate: Maryam Abdulkader Hassan Filla • ID: EAUGRW0004981\nEast Africa University — Faculty of Technology & Engineering"
    tp3.alignment = PP_ALIGN.CENTER
    tp3.font.name = "Arial"
    tp3.font.size = Pt(12.5)
    tp3.font.color.rgb = TEXT_MUTED

    prs.save(output_path)
    print(f"Presentation successfully updated and saved to: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "CyberShield_Thesis_Defense.pptx"
    build_presentation(out)
