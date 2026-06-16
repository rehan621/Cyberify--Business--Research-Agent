from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime, timezone, timedelta
import re
 

from ..database.connection import get_db
from ..database.models import ResearchHistory, User
from ..auth.jwt_handler import get_current_user

router = APIRouter(prefix="/api/export", tags=["Export"])


def markdown_to_pdf(report_text: str, query: str, confidence: float, sources: list) -> BytesIO:
    """Convert a structural Markdown report string into a professional A4 PDF binary stream."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        HRFlowable, Table, TableStyle
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    # Colors
    purple     = HexColor("#6C63FF")
    dark_bg    = HexColor("#1A1A2E")
    light_text = HexColor("#E8E8F0")
    gray       = HexColor("#6B7280")
    green      = HexColor("#34D399")

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22, textColor=purple,
        spaceAfter=6, fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    h1_style = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=16, textColor=purple,
        spaceBefore=16, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, textColor=HexColor("#8B5CF6"),
        spaceBefore=12, spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#374151"),
        spaceAfter=6, leading=16,
        alignment=TA_JUSTIFY,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#374151"),
        spaceAfter=4, leading=14,
        leftIndent=20, bulletIndent=10,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=9, textColor=gray,
        spaceAfter=4,
    )

    story = []

    # ── Header ──
    story.append(Paragraph("🔬 Cyberify Research Agent", ParagraphStyle(
        "Brand", parent=styles["Normal"],
        fontSize=11, textColor=purple, fontName="Helvetica-Bold"
    )))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=2, color=purple))
    story.append(Spacer(1, 12))

    # Title
    story.append(Paragraph(f"Research Report", title_style))
    story.append(Paragraph(f'<i>Query: {query[:100]}</i>', meta_style))
    story.append(Spacer(1, 8))

    # Meta info table
    meta_data = [
    ["Generated", datetime.now(timezone(timedelta(hours=5))).strftime("%B %d, %Y %H:%M PKT")],
    ["Confidence Score", f"{confidence:.0%}"],
]
    
    meta_table = Table(meta_data, colWidths=[4*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), HexColor("#F3F4F6")),
        ("TEXTCOLOR",   (0, 0), (0, -1), gray),
        ("TEXTCOLOR",   (1, 0), (1, -1), HexColor("#374151")),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("PADDING",     (0, 0), (-1, -1), 6),
        ("GRID",        (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, HexColor("#FAFAFA")]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#E5E7EB")))
    story.append(Spacer(1, 12))

    # ── Report Content ──
    lines = report_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue

        if line.startswith("# "):
            story.append(Paragraph(line[2:], h1_style))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], h2_style))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], ParagraphStyle(
                "H3", parent=styles["Normal"],
                fontSize=11, textColor=HexColor("#4B5563"),
                spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold",
            )))
        elif line.startswith("- ") or line.startswith("* "):
            text = line[2:]
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph(f"• {text}", bullet_style))
        elif line.startswith("**") and line.endswith("**"):
            story.append(Paragraph(f"<b>{line[2:-2]}</b>", body_style))
        else:
            # Inline bold transformation
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            text = re.sub(r'\*(.*?)\*',     r'<i>\1</i>', text)
            story.append(Paragraph(text, body_style))

    # ── Sources ──
    if sources:
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#E5E7EB")))
        story.append(Spacer(1, 8))
        story.append(Paragraph("References & Sources", h2_style))
        for i, src in enumerate(sources[:15], 1):
            story.append(Paragraph(
                f'{i}. <link href="{src}">{src[:80]}...</link>' if len(src) > 80 else f'{i}. {src}',
                ParagraphStyle("Source", parent=styles["Normal"],
                               fontSize=8, textColor=HexColor("#6B7280"), spaceAfter=3)
            ))

    # ── Footer ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=purple))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Generated by Cyberify Research Agent | {datetime.utcnow().strftime('%Y')} | Powered by LangGraph + OpenAI",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=gray, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/pdf/{research_id}")
def export_pdf(
    research_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export the finalized research report into a professional PDF asset stream.
    Validates ownership status and processing execution states beforehand.
    """
    record = db.query(ResearchHistory).filter(
        ResearchHistory.id == research_id,
        ResearchHistory.user_id == current_user.id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Research not found")
    if record.status != "completed":
        raise HTTPException(status_code=400, detail="Research processing has not completed yet.")
    if not record.report:
        raise HTTPException(status_code=400, detail="Report documentation content is unavailable.")

    pdf_buffer = markdown_to_pdf(
        report_text=record.report,
        query=record.query,
        confidence=record.confidence_score or 0.0,
        sources=record.sources or [],
    )

    safe_name = record.query[:30].strip().replace(" ", "_").replace("/", "-")
    filename = f"{safe_name}_{research_id}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/markdown/{research_id}")
def export_markdown(
    research_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export the targeted raw research report documentation compiled using standard Markdown structure."""
    record = db.query(ResearchHistory).filter(
        ResearchHistory.id == research_id,
        ResearchHistory.user_id == current_user.id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Research not found")
    if not record.report:
        raise HTTPException(status_code=400, detail="Report documentation content is unavailable.")

    # Inject analytical metadata headers into the Markdown file layout
    md_content = f"""---
title: Cyberify Research Report
query: {record.query}
confidence: {(record.confidence_score or 0):.0%}
generated_at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
sources_count: {len(record.sources or [])}
---

{record.report}

---

## Sources
{chr(10).join([f"{i+1}. {src}" for i, src in enumerate(record.sources or [])])}

---
*Generated by Cyberify Research Agent — Powered by LangGraph + OpenAI*
"""

    safe_name = record.query[:30].strip().replace(" ", "_").replace("/", "-")
    filename = f"{safe_name}_{research_id}.md"
    return StreamingResponse(
        iter([md_content]),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )