"""
Builds a professional PDF report from the structured research JSON.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", fontSize=20, leading=24,
        textColor=colors.HexColor("#1a1a2e"), spaceAfter=6, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=13, leading=16,
        textColor=colors.HexColor("#0f3460"), spaceBefore=14, spaceAfter=6,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="Body", fontSize=10.5, leading=15, textColor=colors.HexColor("#333333")
    ))
    return styles


def generate_pdf(research: dict) -> str:
    """
    research keys expected:
      company_name, website, phone, address,
      products_services (list), pain_points (list),
      competitors (list of {name, website})
    Returns the file path of the generated PDF.
    """
    styles = _styles()
    safe_name = "".join(c for c in research.get("company_name", "company") if c.isalnum() or c in " _-").strip()
    filename = f"{safe_name or 'company'}_research_report.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm
    )

    story = []
    story.append(Paragraph(f"Company Research Report", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}", styles["Body"]
    ))
    story.append(Spacer(1, 14))

    # --- Company Information ---
    story.append(Paragraph("Company Information", styles["SectionHeading"]))
    info_rows = [
        ["Company Name", research.get("company_name") or "N/A"],
        ["Website", research.get("website") or "N/A"],
        ["Phone", research.get("phone") or "N/A"],
        ["Address", research.get("address") or "N/A"],
    ]
    table = Table(info_rows, colWidths=[4 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#333333")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    # --- Summary ---
    if research.get("summary"):
        story.append(Paragraph("Company Summary", styles["SectionHeading"]))
        story.append(Paragraph(research["summary"], styles["Body"]))

    # --- Products / Services ---
    products = research.get("products_services") or []
    if products:
        story.append(Paragraph("Products / Services", styles["SectionHeading"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(p, styles["Body"])) for p in products],
            bulletType="bullet"
        ))

    # --- Pain Points ---
    pains = research.get("pain_points") or []
    if pains:
        story.append(Paragraph("AI-Generated Pain Points", styles["SectionHeading"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(p, styles["Body"])) for p in pains],
            bulletType="bullet"
        ))

    # --- Competitors ---
    competitors = research.get("competitors") or []
    if competitors:
        story.append(Paragraph("Competitor Analysis", styles["SectionHeading"]))
        comp_rows = [["Competitor Name", "Website"]]
        for c in competitors:
            comp_rows.append([c.get("name", "N/A"), c.get("website", "N/A")])
        comp_table = Table(comp_rows, colWidths=[7 * cm, 8 * cm])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(comp_table)

    doc.build(story)
    return filepath
