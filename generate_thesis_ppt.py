import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation(output_path):
    prs = Presentation()
    # 16:9 Widescreen standard
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Academic Palette (Clean, Formal, Human - No AI neon glow)
    BG_COLOR = RGBColor(255, 255, 255)         # Pure White
    NAVY_PRIMARY = RGBColor(15, 41, 66)        # Deep Academic Navy #0F2942
    NAVY_ACCENT = RGBColor(30, 58, 138)        # Classic Blue #1E3A8A
    GOLD_ACCENT = RGBColor(194, 120, 3)        # Academic Gold/Amber #C27803
    TEXT_DARK = RGBColor(30, 41, 59)           # Charcoal Slate #1E293B
    TEXT_MUTED = RGBColor(100, 116, 139)       # Neutral Gray #64748B
    CARD_BG = RGBColor(248, 250, 252)          # Very light slate/gray #F8FAFC
    CARD_BORDER = RGBColor(226, 232, 240)      # Border #E2E8F0
    BORDER_LIGHT = RGBColor(203, 213, 225)

    def add_header(slide, number_str, title_text, category_str=None):
        # Header background banner
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_cat = tf.paragraphs[0]
        if category_str:
            p_cat.text = category_str.upper()
            p_cat.font.name = "Arial"
            p_cat.font.size = Pt(10)
            p_cat.font.bold = True
            p_cat.font.color.rgb = GOLD_ACCENT
            p_title = tf.add_paragraph()
        else:
            p_title = p_cat

        p_title.text = f"{number_str}  {title_text}" if number_str else title_text
        p_title.font.name = "Arial"
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY_PRIMARY

        # Subtle gold divider rule under header
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(0.03)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = GOLD_ACCENT
        line.line.color.rgb = GOLD_ACCENT

        # Footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.35))
        ftf = footer_box.text_frame
        ftf.word_wrap = True
        ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
        fp = ftf.paragraphs[0]
        fp.text = "CyberShield: Web-Based Phishing Detection System | East Africa University — Thesis Defense"
        fp.font.name = "Arial"
        fp.font.size = Pt(9)
        fp.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 1: TITLE SLIDE
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    
    # Top decorative colored bar
    top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_PRIMARY
    top_bar.line.fill.background()

    # University header
    u_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.333), Inches(0.8))
    utf = u_box.text_frame
    up = utf.paragraphs[0]
    up.text = "EAST AFRICA UNIVERSITY"
    up.alignment = PP_ALIGN.CENTER
    up.font.name = "Arial"
    up.font.size = Pt(16)
    up.font.bold = True
    up.font.color.rgb = NAVY_PRIMARY

    up2 = utf.add_paragraph()
    up2.text = "Faculty of Technology & Engineering • Department of Computer Science"
    up2.alignment = PP_ALIGN.CENTER
    up2.font.name = "Arial"
    up2.font.size = Pt(12)
    up2.font.color.rgb = TEXT_MUTED

    # Gold divider line
    div1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.5), Inches(2.0), Inches(4.333), Inches(0.04))
    div1.fill.solid()
    div1.fill.fore_color.rgb = GOLD_ACCENT
    div1.line.fill.background()

    # Main Project Title Box
    title_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(11.333), Inches(2.2))
    ttf = title_box.text_frame
    ttf.word_wrap = True
    tp1 = ttf.paragraphs[0]
    tp1.text = "Design and Implementation of a\nWeb-Based Phishing Detection System"
    tp1.alignment = PP_ALIGN.CENTER
    tp1.font.name = "Arial"
    tp1.font.size = Pt(30)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY_PRIMARY

    tp2 = ttf.add_paragraph()
    tp2.text = "PROJECT: CYBERSHIELD"
    tp2.alignment = PP_ALIGN.CENTER
    tp2.font.name = "Arial"
    tp2.font.size = Pt(15)
    tp2.font.bold = True
    tp2.font.color.rgb = GOLD_ACCENT

    # Student metadata card
    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.2), Inches(4.7), Inches(6.933), Inches(1.8))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = CARD_BORDER
    card.line.width = Pt(1)

    ctf = card.text_frame
    ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
    cp1 = ctf.paragraphs[0]
    cp1.text = "Bachelor of Computer Science — Final-Year Thesis Defense"
    cp1.alignment = PP_ALIGN.CENTER
    cp1.font.name = "Arial"
    cp1.font.size = Pt(12)
    cp1.font.bold = True
    cp1.font.color.rgb = NAVY_ACCENT

    cp2 = ctf.add_paragraph()
    cp2.text = "Candidate: Maryam Abdulkader Hassan Filla"
    cp2.alignment = PP_ALIGN.CENTER
    cp2.font.name = "Arial"
    cp2.font.size = Pt(13)
    cp2.font.bold = True
    cp2.font.color.rgb = TEXT_DARK

    cp3 = ctf.add_paragraph()
    cp3.text = "Student ID: EAUGRW0004981   •   Academic Year: October 2026"
    cp3.alignment = PP_ALIGN.CENTER
    cp3.font.name = "Arial"
    cp3.font.size = Pt(11)
    cp3.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 2: PRESENTATION OUTLINE (MATCHING PHOTO)
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "", "Presentation Outline", "Table of Contents")

    # 2-column layout for the 10 points
    col1_items = [
        ("1", "Introduction / Background"),
        ("2", "Problem Statement"),
        ("3", "Objectives of the Study"),
        ("4", "Literature Review"),
        ("5", "Methodology")
    ]
    col2_items = [
        ("6", "System Design"),
        ("7", "Implementation"),
        ("8", "Testing & Results"),
        ("9", "Discussion"),
        ("10", "Conclusion & Recommendations")
    ]

    for i, (num, text) in enumerate(col1_items):
        y_pos = Inches(2.0 + i * 0.95)
        # Number badge
        badge = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), y_pos, Inches(0.65), Inches(0.65))
        badge.fill.solid()
        badge.fill.fore_color.rgb = NAVY_PRIMARY
        badge.line.fill.background()
        btf = badge.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]
        bp.text = num
        bp.alignment = PP_ALIGN.CENTER
        bp.font.name = "Arial"
        bp.font.size = Pt(14)
        bp.font.bold = True
        bp.font.color.rgb = RGBColor(255, 255, 255)

        # Text box
        tb = s2.shapes.add_textbox(Inches(2.05), y_pos + Inches(0.08), Inches(4.5), Inches(0.55))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = "Arial"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = TEXT_DARK

    for i, (num, text) in enumerate(col2_items):
        y_pos = Inches(2.0 + i * 0.95)
        # Number badge
        badge = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.2), y_pos, Inches(0.65), Inches(0.65))
        badge.fill.solid()
        badge.fill.fore_color.rgb = GOLD_ACCENT
        badge.line.fill.background()
        btf = badge.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]
        bp.text = num
        bp.alignment = PP_ALIGN.CENTER
        bp.font.name = "Arial"
        bp.font.size = Pt(14)
        bp.font.bold = True
        bp.font.color.rgb = RGBColor(255, 255, 255)

        # Text box
        tb = s2.shapes.add_textbox(Inches(8.05), y_pos + Inches(0.08), Inches(4.5), Inches(0.55))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = "Arial"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 3: 1. INTRODUCTION / BACKGROUND
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "1.", "Introduction & Background", "Overview")

    # 3 structured cards
    intro_cards = [
        ("The Phishing Landscape", "Phishing remains the primary vector for cyber attacks worldwide. Over 94% of organizational data breaches originate through deceptive communications, credential harvesting links, and spoofed domains targeting human trust."),
        ("Multi-Channel Attack Evolution", "Modern phishing has advanced beyond basic email attachments. Attackers heavily utilize deceptive URLs, spear-phishing emails, and increasingly QR codes (Quishing) to bypass traditional gateway security filters."),
        ("Research Motivation", "There is a critical need for an accessible, transparent, and proactive security platform that safeguards everyday users and educational institutions through real-time heuristic inspection rather than delayed blacklists.")
    ]

    for i, (title, body) in enumerate(intro_cards):
        x = Inches(0.8 + i * 3.95)
        c = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.0), Inches(3.75), Inches(4.5))
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1)

        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_top = Inches(0.3)
        ctf.margin_left = ctf.margin_right = Inches(0.3)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_PRIMARY

        p2 = ctf.add_paragraph()
        p2.text = body
        p2.font.name = "Arial"
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 4: 2. PROBLEM STATEMENT
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "2.", "Problem Statement", "The Research Gap")

    # Left: Empirical Stat Box
    sb = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(4.2), Inches(4.5))
    sb.fill.solid()
    sb.fill.fore_color.rgb = CARD_BG
    sb.line.color.rgb = CARD_BORDER
    sbtf = sb.text_frame
    sbtf.word_wrap = True
    sbtf.margin_left = sbtf.margin_right = sbtf.margin_top = Inches(0.4)

    sp1 = sbtf.paragraphs[0]
    sp1.text = "Global Threat Scale"
    sp1.font.name = "Arial"
    sp1.font.size = Pt(13)
    sp1.font.bold = True
    sp1.font.color.rgb = GOLD_ACCENT

    sp2 = sbtf.add_paragraph()
    sp2.text = "971,181"
    sp2.font.name = "Arial"
    sp2.font.size = Pt(38)
    sp2.font.bold = True
    sp2.font.color.rgb = NAVY_PRIMARY

    sp3 = sbtf.add_paragraph()
    sp3.text = "Confirmed phishing attacks reported by the Anti-Phishing Working Group (APWG) in a single quarter."
    sp3.font.name = "Arial"
    sp3.font.size = Pt(12)
    sp3.font.color.rgb = TEXT_MUTED

    sp4 = sbtf.add_paragraph()
    sp4.text = "\nCore Problem: While detection technology exists, accessible and transparent real-time protection does not exist for ordinary internet users."
    sp4.font.name = "Arial"
    sp4.font.size = Pt(12)
    sp4.font.bold = True
    sp4.font.color.rgb = TEXT_DARK

    # Right: The Two Imperfect Options & The Result
    gap_box = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.3), Inches(2.0), Inches(7.2), Inches(4.5))
    gap_box.fill.solid()
    gap_box.fill.fore_color.rgb = RGBColor(255, 255, 255)
    gap_box.line.color.rgb = CARD_BORDER
    gtf = gap_box.text_frame
    gtf.word_wrap = True
    gtf.margin_left = gtf.margin_right = gtf.margin_top = Inches(0.4)

    gp1 = gtf.paragraphs[0]
    gp1.text = "Current Limitations in Existing Solutions:"
    gp1.font.name = "Arial"
    gp1.font.size = Pt(15)
    gp1.font.bold = True
    gp1.font.color.rgb = NAVY_PRIMARY

    items = [
        ("Blacklist-Only Checkers (Reactive):", "Fast and free, but blind to new zero-hour phishing sites during the critical hours or days before manual crowdsourced reporting."),
        ("Enterprise Security Software (Inaccessible):", "Genuinely proactive, but prohibitively expensive, complex, and restricted to institutional SOC environments."),
        ("The Resulting Gap:", "Ordinary students and small businesses are left unprotected with no explainable, automated, and free multi-vector defense platform.")
    ]
    for h, d in items:
        p_h = gtf.add_paragraph()
        p_h.text = f"• {h} "
        p_h.font.name = "Arial"
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = NAVY_ACCENT
        p_d = gtf.add_paragraph()
        p_d.text = f"  {d}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 5: 3. OBJECTIVES OF THE STUDY
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "3.", "Objectives of the Study", "Goals & Targets")

    # General Objective Box across top
    gen_box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.2))
    gen_box.fill.solid()
    gen_box.fill.fore_color.rgb = CARD_BG
    gen_box.line.color.rgb = GOLD_ACCENT
    gen_box.line.width = Pt(1.5)
    gtf = gen_box.text_frame
    gtf.word_wrap = True
    gtf.margin_left = gtf.margin_right = gtf.margin_top = Inches(0.2)
    gp1 = gtf.paragraphs[0]
    gp1.text = "GENERAL OBJECTIVE"
    gp1.font.name = "Arial"
    gp1.font.size = Pt(11)
    gp1.font.bold = True
    gp1.font.color.rgb = GOLD_ACCENT

    gp2 = gtf.add_paragraph()
    gp2.text = "To design and implement a web-based phishing detection system enabling real-time URL verification, email analysis, QR code inspection, and automated browser protection."
    gp2.font.name = "Arial"
    gp2.font.size = Pt(13)
    gp2.font.bold = True
    gp2.font.color.rgb = NAVY_PRIMARY

    # 6 Specific Objectives Grid (3x2)
    spec_objs = [
        ("Obj 1: Literature Review", "Review existing blacklist, heuristic, and machine learning phishing detection techniques."),
        ("Obj 2: URL Analysis Engine", "Build a modular heuristic scoring engine evaluating URL syntax, entropy, and domain age."),
        ("Obj 3: Secure Authentication", "Implement a robust authentication system with JWT sessions, Bcrypt hashing, and role access."),
        ("Obj 4: Detection Accuracy Evaluation", "Examine detection behavior, accuracy boundaries, and test suite reliability."),
        ("Obj 5: Platform Security Measures", "Incorporate security by design: Rate limiting, input validation, CSRF, and SSRF guards."),
        ("Obj 6: Browser Extension", "Develop a Manifest V3 browser extension providing passive zero-click protection.")
    ]

    for i, (title, desc) in enumerate(spec_objs):
        row = i // 3
        col = i % 3
        x = Inches(0.8 + col * 3.95)
        y = Inches(3.2 + row * 1.8)

        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(3.75), Inches(1.6))
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(255, 255, 255)
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.15)
        cp1 = ctf.paragraphs[0]
        cp1.text = title
        cp1.font.name = "Arial"
        cp1.font.size = Pt(12)
        cp1.font.bold = True
        cp1.font.color.rgb = NAVY_ACCENT

        cp2 = ctf.add_paragraph()
        cp2.text = desc
        cp2.font.name = "Arial"
        cp2.font.size = Pt(10.5)
        cp2.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 6: 4. LITERATURE REVIEW
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "4.", "Literature Review", "Theoretical Framework")

    # Comparison Table of Detection Techniques
    table_shape = s6.shapes.add_table(4, 4, Inches(0.8), Inches(2.0), Inches(11.733), Inches(4.5))
    table = table_shape.table

    # Column widths
    table.columns[0].width = Inches(2.3)
    table.columns[1].width = Inches(3.1)
    table.columns[2].width = Inches(3.1)
    table.columns[3].width = Inches(3.233)

    headers = ["Technique", "Key Advantages", "Limitations / Vulnerabilities", "CyberShield Approach"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = "Arial"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("Blacklist-Based\n(e.g., Safe Browsing)", "• Low false positives\n• Instant lookup for known sites\n• Minimal server compute", "• Zero-hour window blindness\n• Ineffective against short-lived domains\n• Delayed victim reporting", "Incorporated as Phase 2 internal blacklist for known bad actors."),
        ("Machine Learning\nClassifiers (ML/AI)", "• Generalizes across patterns\n• Detects complex combinations\n• Adapts with retraining", "• Black-box decisions (no explanation)\n• High computational inference overhead\n• Model drift & dataset bias", "Identified for future hybrid integration; avoided for initial sub-second latency."),
        ("Rule-Based Heuristic\nAnalysis (CyberShield)", "• Sub-second response time\n• Full explainability (Named rules)\n• Transparent penalties\n• Zero third-party dependency", "• Requires careful weight calibration\n• Dependent on rule coverage\n• Potential false positives on rare TLDs", "Primary detection core: 29 rules across URL, Email headers, and QR payloads.")
    ]

    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if i % 2 == 0 else RGBColor(255, 255, 255)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = "Arial"
            p.font.size = Pt(10.5)
            p.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 7: 5. METHODOLOGY
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "5.", "Research Methodology", "Design Science Research")

    # 4 Pillars
    method_pillars = [
        ("Research Design:\nDesign Science Research", "Hevner et al. (2004) Framework\n\nFocuses on building and evaluating a functional software artefact to solve an identified business & security problem, rather than conducting sample/population opinion surveys."),
        ("Development Method:\nAgile & Incremental", "Beck et al. (2001) Agile Model\n\nThe platform was architected across modular increments (Phases 1 through 8), enabling each scanner engine, database model, and API endpoint to be built, tested, and refined independently."),
        ("Requirements &\nData Instrument", "Specification & Gap Analysis\n\nSystem functional and non-functional requirements were established from empirical literature gap analysis and APWG threat telemetry specifications."),
        ("Evaluation &\nVerification Strategy", "Deterministic Test Harness\n\nEvaluation conducted through a 562-test automated test suite (Pytest + Vitest) plus real-world accumulated platform usage logs across multi-user environments.")
    ]

    for i, (title, desc) in enumerate(method_pillars):
        x = Inches(0.8 + i * 2.98)
        card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.0), Inches(2.8), Inches(4.6))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.2)
        cp1 = ctf.paragraphs[0]
        cp1.text = title
        cp1.font.name = "Arial"
        cp1.font.size = Pt(13)
        cp1.font.bold = True
        cp1.font.color.rgb = NAVY_PRIMARY

        cp2 = ctf.add_paragraph()
        cp2.text = f"\n{desc}"
        cp2.font.name = "Arial"
        cp2.font.size = Pt(11)
        cp2.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 8: 6. SYSTEM DESIGN
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "6.", "System Design", "Architecture & Layers")

    layers = [
        ("1. Client Layer (Presentation)", "React 18 Single Page Application (Vite + TypeScript) + Chromium Manifest V3 Browser Extension. Provides real-time user interfaces, blocking overlays, and scan center dashboards."),
        ("2. Application Layer (Logic & Auth)", "Python Flask REST API (/api/v1). Manages routing, rate limiting (Flask-Limiter), JWT access/refresh session lifecycles, and Role-Based Access Control (RBAC)."),
        ("3. Detection Engine Layer (Core Logic)", "Modular heuristic inspection engines: URL Scanner (11 rules), Email Analyzer (10 rules for SPF/DKIM/MIME), and QR Code Decoder (8 payload handlers). Shared core design avoids code duplication."),
        ("4. Data Layer (Persistence)", "PostgreSQL 16 relational database (14 production tables) ensuring ACID compliance and scan indexing, with SQLite in-memory database utilized for deterministic automated testing.")
    ]

    for i, (title, body) in enumerate(layers):
        y = Inches(1.9 + i * 1.22)
        card = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.733), Inches(1.1))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = Inches(0.25)
        ctf.margin_top = Inches(0.12)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_PRIMARY

        p2 = ctf.add_paragraph()
        p2.text = body
        p2.font.name = "Arial"
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 9: 7. IMPLEMENTATION
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "7.", "System Implementation", "Key Features & Stack")

    # Formula Box across top
    f_box = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.0))
    f_box.fill.solid()
    f_box.fill.fore_color.rgb = NAVY_PRIMARY
    ftf = f_box.text_frame
    ftf.word_wrap = True
    fp1 = ftf.paragraphs[0]
    fp1.text = "Core Scoring Formula:  Trust Score = 100 + Σ (rule impacts)  [Clamped: 0 – 100]"
    fp1.alignment = PP_ALIGN.CENTER
    fp1.font.name = "Arial"
    fp1.font.size = Pt(14)
    fp1.font.bold = True
    fp1.font.color.rgb = RGBColor(255, 255, 255)

    fp2 = ftf.add_paragraph()
    fp2.text = "Risk Thresholds: Safe (90–100)  |  Low Risk (70–89)  |  Suspicious (40–69)  |  Dangerous (0–39)"
    fp2.alignment = PP_ALIGN.CENTER
    fp2.font.name = "Arial"
    fp2.font.size = Pt(11)
    fp2.font.color.rgb = GOLD_ACCENT

    # 3 Implementation Pillars
    impl_pillars = [
        ("Three Detection Channels", "• URL Scanner (11 Rules): IP host detection, brand typosquatting, TLS check, domain age, suspicious TLDs.\n• Email Scanner (10 Rules): Header auth (SPF/DKIM/DMARC), sender spoofing, urgency keywords, executable attachments.\n• QR Scanner (8 Handlers): Payload matrix decoding (URL, WiFi, Crypto, Phone) piped into URL engine."),
        ("Browser Extension (MV3)", "• Zero-Effort Automation: Automatically intercepts active tab navigation.\n• Sub-Second Response: 267ms average check prevents user credential entry.\n• Full-Page Warning Overlay: Blurs and intercepts dangerous sites.\n• Privacy Mode: In-memory evaluation without saving browsing history."),
        ("Enterprise Administration", "• Role-Based Access Control (RBAC): User vs Admin permission matrices.\n• Dynamic Rule Toggling: Enable or disable heuristic rules in real-time.\n• Audit Logging: Non-repudiation logging of security events & IP addresses.\n• Security Headers: Strict CSRF, Rate Limiting, SSRF guards, Bcrypt.")
    ]

    for i, (title, content) in enumerate(impl_pillars):
        x = Inches(0.8 + i * 3.95)
        c = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.0), Inches(3.75), Inches(3.7))
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1)

        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.2)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_ACCENT

        p2 = ctf.add_paragraph()
        p2.text = f"\n{content}"
        p2.font.name = "Arial"
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 10: 8. TESTING & RESULTS
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "8.", "Testing & Results", "Verification & Telemetry")

    # Left: Automated Testing Results
    t_box = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.6))
    t_box.fill.solid()
    t_box.fill.fore_color.rgb = CARD_BG
    t_box.line.color.rgb = CARD_BORDER
    ttf = t_box.text_frame
    ttf.word_wrap = True
    ttf.margin_left = ttf.margin_right = ttf.margin_top = Inches(0.3)

    tp1 = ttf.paragraphs[0]
    tp1.text = "Automated Test Suite Verification"
    tp1.font.name = "Arial"
    tp1.font.size = Pt(14)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY_PRIMARY

    tp2 = ttf.add_paragraph()
    tp2.text = "562 of 562 Tests Passed (100%)"
    tp2.font.name = "Arial"
    tp2.font.size = Pt(18)
    tp2.font.bold = True
    tp2.font.color.rgb = RGBColor(22, 101, 52) # Green

    tp3 = ttf.add_paragraph()
    tp3.text = "\n• Backend Suite (Pytest): 473 tests exercising API routes, auth, rate limiting, and heuristic scoring.\n• Extension Suite (Vitest): 89 tests verifying client-side lifecycle and message passing.\n\nWorked Detection Example:\nTarget: http://45.33.32.156/paypal-verify-account\nCalculated Score: 31 / 100 (DANGEROUS)\nTriggered Rules: Raw IP host (-25), Brand impersonation (-30), Plain HTTP (-15)."
    tp3.font.name = "Arial"
    tp3.font.size = Pt(11)
    tp3.font.color.rgb = TEXT_DARK

    # Right: Live Platform Telemetry
    p_box = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(2.0), Inches(5.633), Inches(4.6))
    p_box.fill.solid()
    p_box.fill.fore_color.rgb = CARD_BG
    p_box.line.color.rgb = CARD_BORDER
    ptf = p_box.text_frame
    ptf.word_wrap = True
    ptf.margin_left = ptf.margin_right = ptf.margin_top = Inches(0.3)

    pp1 = ptf.paragraphs[0]
    pp1.text = "Live Platform Usage Telemetry"
    pp1.font.name = "Arial"
    pp1.font.size = Pt(14)
    pp1.font.bold = True
    pp1.font.color.rgb = NAVY_PRIMARY

    pp2 = ptf.add_paragraph()
    pp2.text = "472 Real Accumulated Scans Recorded"
    pp2.font.name = "Arial"
    pp2.font.size = Pt(18)
    pp2.font.bold = True
    pp2.font.color.rgb = NAVY_ACCENT

    pp3 = ptf.add_paragraph()
    pp3.text = "\n• Automatic Scanning: 448 / 472 (95%) originated passively from the browser extension.\n• Performance Latency: 267.79 ms average API response time.\n• Mean Trust Score: 90.8 across live evaluation.\n• Risk Classification: 261 Safe, 194 Low Risk, 11 Suspicious, 6 Dangerous blocked.\n• Platform Deployment: 31 registered users, 2 administrators, 16 blocked attacks."
    pp3.font.name = "Arial"
    pp3.font.size = Pt(11)
    pp3.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 11: 9. DISCUSSION
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "9.", "Discussion", "Critical Analysis")

    discussion_points = [
        ("Objectives Evaluation (5 of 6 Met)", "Five of the six specific research objectives were fully achieved. Objective 4 (accuracy benchmarking against a static labelled dataset) was not met because no fixed ground-truth dataset was compiled; reliability was measured via 562 automated tests instead. Reliability and accuracy represent distinct properties."),
        ("Empirical Validation of Automatic Protection", "The finding that 95% of all scans originated through the browser extension rather than manual web dashboard pasting validates the fundamental research hypothesis: effective end-user cybersecurity must be automated and zero-effort."),
        ("Explainability as an Essential Security Requirement", "By implementing deterministic heuristic penalties, every verdict provides clear, transparent reasons (e.g. 'IP host detected', 'Mismatched sender') rather than opaque machine learning outputs, empowering user awareness and security education."),
        ("System Limitations", "Current heuristics inspect static indicators and headers; they do not perform dynamic JavaScript execution in an isolated virtual sandbox, and password-protected archive attachments cannot be decrypted without user keys.")
    ]

    for i, (title, body) in enumerate(discussion_points):
        row = i // 2
        col = i % 2
        x = Inches(0.8 + col * 5.95)
        y = Inches(2.0 + row * 2.3)

        card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.75), Inches(2.1))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.2)
        cp1 = ctf.paragraphs[0]
        cp1.text = title
        cp1.font.name = "Arial"
        cp1.font.size = Pt(13)
        cp1.font.bold = True
        cp1.font.color.rgb = NAVY_PRIMARY

        cp2 = ctf.add_paragraph()
        cp2.text = f"\n{body}"
        cp2.font.name = "Arial"
        cp2.font.size = Pt(10.5)
        cp2.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 12: 10. CONCLUSION & RECOMMENDATIONS
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "10.", "Conclusion & Recommendations", "Summary & Future Work")

    # Conclusion Card
    conc_card = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(11.733), Inches(1.8))
    conc_card.fill.solid()
    conc_card.fill.fore_color.rgb = CARD_BG
    conc_card.line.color.rgb = NAVY_PRIMARY
    conc_card.line.width = Pt(1.5)
    ctf = conc_card.text_frame
    ctf.word_wrap = True
    ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.25)

    cp1 = ctf.paragraphs[0]
    cp1.text = "RESEARCH CONCLUSION"
    cp1.font.name = "Arial"
    cp1.font.size = Pt(12)
    cp1.font.bold = True
    cp1.font.color.rgb = NAVY_PRIMARY

    cp2 = ctf.add_paragraph()
    cp2.text = "The CyberShield platform successfully demonstrates that transparent, explainable, and multi-channel phishing detection is achievable without costly enterprise licensing. The system runs reliably, passes all 562 automated tests, and provides accessible protection across web, email, QR, and browser extension environments."
    cp2.font.name = "Arial"
    cp2.font.size = Pt(12)
    cp2.font.color.rgb = TEXT_DARK

    # 3 Future Recommendations
    recs = [
        ("1. Benchmark Accuracy Evaluation", "Execute a rigorous accuracy evaluation using balanced feeds from PhishTank and verified legitimate domains to compute precision, recall, and false positive rates."),
        ("2. Hybrid NLP / Machine Learning", "Integrate a lightweight Natural Language Processing (NLP) classifier to detect subtle context-driven spear-phishing messages alongside heuristic rules."),
        ("3. Dynamic Sandboxing & Mobile Apps", "Extend detection through headless browser execution for DOM inspection and publish dedicated mobile browser extensions and apps.")
    ]

    for i, (title, desc) in enumerate(recs):
        x = Inches(0.8 + i * 3.95)
        c = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(4.0), Inches(3.75), Inches(2.7))
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor(255, 255, 255)
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1)

        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = Inches(0.2)
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.name = "Arial"
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = GOLD_ACCENT

        p2 = ctf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.name = "Arial"
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 13: THANK YOU / Q&A
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)
    
    top_bar = s13.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_PRIMARY
    top_bar.line.fill.background()

    card_ty = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(2.5), Inches(1.8), Inches(8.333), Inches(4.2))
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
    tp1.font.size = Pt(36)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY_PRIMARY

    tp2 = tytf.add_paragraph()
    tp2.text = "Questions & Answers (Q&A)"
    tp2.alignment = PP_ALIGN.CENTER
    tp2.font.name = "Arial"
    tp2.font.size = Pt(18)
    tp2.font.bold = True
    tp2.font.color.rgb = GOLD_ACCENT

    tp3 = tytf.add_paragraph()
    tp3.text = "\nCyberShield — Design and Implementation of a Web-Based Phishing Detection System\nCandidate: Maryam Abdulkader Hassan Filla • ID: EAUGRW0004981\nEast Africa University — Faculty of Technology & Engineering"
    tp3.alignment = PP_ALIGN.CENTER
    tp3.font.name = "Arial"
    tp3.font.size = Pt(12)
    tp3.font.color.rgb = TEXT_MUTED

    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "CyberShield_Thesis_Defense.pptx"
    create_presentation(out)
