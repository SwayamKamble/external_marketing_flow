from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
INPUT_MD = ROOT / "docs" / "PROJECT_DOCUMENTATION.md"
OUTPUT_PDF = ROOT / "docs" / "PROJECT_DOCUMENTATION.pdf"


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def paragraph_for_line(line: str, styles: dict[str, ParagraphStyle]) -> Paragraph | Spacer | None:
    stripped = line.rstrip("\n")
    if not stripped.strip():
        return Spacer(1, 4)

    if stripped.startswith("---"):
        return Spacer(1, 8)

    if stripped.startswith("### "):
        return Paragraph(escape_html(stripped[4:]), styles["h3"])
    if stripped.startswith("## "):
        return Paragraph(escape_html(stripped[3:]), styles["h2"])
    if stripped.startswith("# "):
        return Paragraph(escape_html(stripped[2:]), styles["h1"])

    if stripped.startswith("- "):
        text = escape_html(stripped[2:])
        return Paragraph(f"&bull;&nbsp;{text}", styles["bullet"])

    if stripped.startswith("1. ") or stripped.startswith("2. ") or stripped.startswith("3. ") or stripped[:2].isdigit():
        return Paragraph(escape_html(stripped), styles["body"])

    return Paragraph(escape_html(stripped), styles["body"])


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#111827"),
            spaceAfter=3,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            leftIndent=12,
            bulletIndent=0,
            textColor=colors.HexColor("#111827"),
            spaceAfter=2,
        ),
    }


def main() -> None:
    if not INPUT_MD.exists():
        raise FileNotFoundError(f"Markdown file not found: {INPUT_MD}")

    styles = build_styles()
    story: list[Paragraph | Spacer] = []

    for line in INPUT_MD.read_text(encoding="utf-8").splitlines():
        item = paragraph_for_line(line, styles)
        if item is not None:
            story.append(item)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="ContentForge Project Documentation",
        author="ContentForge",
    )
    doc.build(story)
    print(f"Generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
