# -*- coding: utf-8 -*-
"""
cv_pdf.py
CV ን ወደ ፕሮፌሽናል PDF የሚቀይር እና በ password የሚቆልፍ ሞጁል።
"""

import os
import random
import string

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT

import pikepdf


def generate_password(length: int = 8) -> str:
    """ለ PDF መክፈቻ የሚሆን ራንደም password ይፈጥራል (ቁጥር ብቻ፣ ለተጠቃሚ ቀላል እንዲሆን)."""
    return "".join(random.choices(string.digits, k=length))


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="NameTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=colors.HexColor("#1a2b4c"),
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="ContactInfo",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#444444"),
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.white,
        backColor=colors.HexColor("#1a2b4c"),
        leftIndent=6,
        spaceBefore=10,
        spaceAfter=6,
        borderPadding=(4, 4, 4, 4),
    ))

    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#222222"),
        alignment=TA_LEFT,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="ItemTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#1a2b4c"),
        spaceAfter=1,
    ))

    styles.add(ParagraphStyle(
        name="ItemSub",
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        textColor=colors.HexColor("#666666"),
        spaceAfter=4,
    ))

    return styles


def _section(flowables, styles, title):
    flowables.append(Paragraph(title, styles["SectionHeader"]))
    flowables.append(HRFlowable(width="100%", thickness=1,
                                 color=colors.HexColor("#1a2b4c"),
                                 spaceAfter=6))


def build_unlocked_pdf(data: dict, output_path: str):
    """
    data expected keys:
      full_name, phone, email, address, summary,
      education (str, multi-line, one entry per line as 'ደረጃ | ትምህርት ቤት | ዓመት'),
      experience (str, multi-line as 'ሥራ ድርሻ | ድርጅት | ጊዜ | መግለጫ'),
      skills (str, comma separated),
      languages (str, comma separated)
    """
    styles = _build_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )

    flow = []

    # Header
    flow.append(Paragraph(data.get("full_name", ""), styles["NameTitle"]))
    contact_parts = [p for p in [
        data.get("phone", ""), data.get("email", ""), data.get("address", "")
    ] if p]
    flow.append(Paragraph(" | ".join(contact_parts), styles["ContactInfo"]))
    flow.append(HRFlowable(width="100%", thickness=2,
                            color=colors.HexColor("#1a2b4c"), spaceAfter=10))

    # Summary
    if data.get("summary"):
        _section(flow, styles, "ማጠቃለያ / SUMMARY")
        flow.append(Paragraph(data["summary"], styles["BodyText2"]))

    # Experience
    if data.get("experience"):
        _section(flow, styles, "የሥራ ልምድ / EXPERIENCE")
        for line in data["experience"].split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            title = parts[0] if len(parts) > 0 else ""
            org = parts[1] if len(parts) > 1 else ""
            period = parts[2] if len(parts) > 2 else ""
            desc = parts[3] if len(parts) > 3 else ""
            flow.append(Paragraph(title, styles["ItemTitle"]))
            sub = " - ".join([p for p in [org, period] if p])
            if sub:
                flow.append(Paragraph(sub, styles["ItemSub"]))
            if desc:
                flow.append(Paragraph(desc, styles["BodyText2"]))
            flow.append(Spacer(1, 4))

    # Education
    if data.get("education"):
        _section(flow, styles, "የትምህርት ደረጃ / EDUCATION")
        for line in data["education"].split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            degree = parts[0] if len(parts) > 0 else ""
            school = parts[1] if len(parts) > 1 else ""
            year = parts[2] if len(parts) > 2 else ""
            flow.append(Paragraph(degree, styles["ItemTitle"]))
            sub = " - ".join([p for p in [school, year] if p])
            if sub:
                flow.append(Paragraph(sub, styles["ItemSub"]))
            flow.append(Spacer(1, 2))

    # Skills
    if data.get("skills"):
        _section(flow, styles, "ችሎታዎች / SKILLS")
        skills_list = [s.strip() for s in data["skills"].split(",") if s.strip()]
        flow.append(Paragraph(" • ".join(skills_list), styles["BodyText2"]))

    # Languages
    if data.get("languages"):
        _section(flow, styles, "ቋንቋዎች / LANGUAGES")
        langs_list = [s.strip() for s in data["languages"].split(",") if s.strip()]
        flow.append(Paragraph(" • ".join(langs_list), styles["BodyText2"]))

    doc.build(flow)


def lock_pdf_with_password(input_path: str, output_path: str, password: str):
    """input_path ላይ ያለውን PDF በ password ቆልፎ output_path ላይ ያስቀምጣል።"""
    pdf = pikepdf.open(input_path)
    encryption = pikepdf.Encryption(
        user=password,       # ፒዲኤፉን ለመክፈት የሚያስፈልግ password
        owner=password + "_owner",  # የባለቤትነት password (የተለየ)
        R=4,
    )
    pdf.save(output_path, encryption=encryption)
    pdf.close()


def generate_locked_cv(data: dict, work_dir: str, user_id) -> tuple[str, str]:
    """
    ሙሉ ሂደት: unlocked pdf ይሰራል -> በ password ይቆለፋል -> unlocked ፋይል ይጠፋል.
    Returns: (locked_pdf_path, password)
    """
    os.makedirs(work_dir, exist_ok=True)
    unlocked_path = os.path.join(work_dir, f"cv_{user_id}_unlocked.pdf")
    locked_path = os.path.join(work_dir, f"cv_{user_id}_locked.pdf")

    build_unlocked_pdf(data, unlocked_path)
    password = generate_password(8)
    lock_pdf_with_password(unlocked_path, locked_path, password)

    try:
        os.remove(unlocked_path)
    except OSError:
        pass

    return locked_path, password
