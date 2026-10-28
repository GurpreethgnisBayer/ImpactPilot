"""PDF impact brief rendered with fpdf2 (pure Python, no system libraries)."""

from __future__ import annotations

from pathlib import Path

from impactpilot.domain.models import InitiativeRecord
from impactpilot.export.brief_content import BriefContent, build_brief_content

INK = (11, 18, 32)
INDIGO = (79, 70, 229)
SLATE = (71, 85, 105)
MUTED = (148, 163, 184)
SURFACE = (247, 248, 251)
LINE = (226, 232, 240)
AMBER = (180, 83, 9)
AMBER_BG = (254, 243, 199)
GREEN = (4, 120, 87)

# Unicode TTFs, tried in order; core Helvetica (Latin-1 only) is the fallback.
_FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
]

_LATIN1 = str.maketrans(
    {"–": "-", "—": "-", "·": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "…": "...", "€": "EUR", "≤": "<=", "≥": ">="}
)


def build_pdf_bytes(record: InitiativeRecord) -> bytes:
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
        from fpdf.fonts import FontFace
    except ImportError as exc:
        raise RuntimeError("PDF export requires the fpdf2 package") from exc

    c = build_brief_content(record)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(16, 16, 16)
    family = _register_font(pdf)
    unicode_ok = family != "Helvetica"

    def t(value: str) -> str:
        value = value or ""
        return value if unicode_ok else value.translate(_LATIN1).encode("latin-1", "replace").decode("latin-1")

    def font(size: float, bold: bool = False, color=INK) -> None:
        pdf.set_font(family, "B" if bold else "", size)
        pdf.set_text_color(*color)

    def para(value: str, size: float = 10, color=SLATE, bold: bool = False, h: float = 5) -> None:
        font(size, bold, color)
        pdf.multi_cell(0, h, t(value), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def section(title: str) -> None:
        pdf.ln(4)
        font(9, True, INDIGO)
        pdf.cell(0, 5, t(title.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(*LINE)
        pdf.line(pdf.l_margin, pdf.get_y() + 0.5, pdf.w - pdf.r_margin, pdf.get_y() + 0.5)
        pdf.ln(2.5)

    def bullets(items: list[str]) -> None:
        for item in items:
            font(10, False, SLATE)
            pdf.multi_cell(
                0, 5, t(f"•  {item}" if unicode_ok else f"-  {item}"), align="L",
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )

    pdf.add_page()
    _header_band(pdf, c, family, t)
    if c.status == "draft":
        _draft_watermark(pdf, family)

    if c.draft_note:
        pdf.set_fill_color(*AMBER_BG)
        font(9, True, AMBER)
        pdf.multi_cell(
            0, 5, t(f"{c.draft_note} ({c.unconfirmed_count} unconfirmed)"), fill=True, padding=(2.5, 3), align="L",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.ln(2)

    section("Impact statement")
    para(c.statement or c.summary or "Not generated yet.", 11.5, INK, h=6)
    if c.score_rationale:
        para(c.score_rationale, 9, MUTED)

    section("At a glance")
    _facts_grid(pdf, c, font, t)

    if c.effects:
        section("Expected effects")
        if c.exploratory_note:
            para(c.exploratory_note, 9, MUTED)
            pdf.ln(1)
        font(9)
        pdf.set_draw_color(*LINE)
        with pdf.table(
            col_widths=(30, 22, 62, 22, 24, 18),
            line_height=5,
            text_align="LEFT",
            headings_style=FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=INK),
            cell_fill_color=SURFACE,
            cell_fill_mode="ROWS",
            borders_layout="HORIZONTAL_LINES",
            padding=1.5,
        ) as table:
            head = table.row()
            for h in ("Dimension", "Direction", "Range", "Confidence", "Status", "Sources"):
                head.cell(h)
            for e in c.effects:
                row = table.row()
                row.cell(t(e.dimension), style=FontFace(emphasis="BOLD"))
                row.cell(t(e.direction))
                row.cell(t(e.range_text))
                row.cell(t(e.confidence))
                row.cell(
                    "Confirmed" if e.confirmed else "Unconfirmed",
                    style=FontFace(emphasis="BOLD", color=GREEN if e.confirmed else AMBER),
                )
                row.cell(t(e.citations or "-"))

    if c.summary and c.statement:
        section("Evidence summary")
        para(c.summary)
    if c.findings:
        section("Key findings")
        bullets(c.findings)
    if c.money or c.tco:
        section("Value and cost")
        bullets(c.money + ([f"TCO: {c.tco}"] if c.tco else []))
    if c.kpis:
        section("How we will measure it")
        bullets([f"{n}: {d}" for n, d in c.kpis])
    if c.risks:
        section("Risks and caveats")
        bullets(c.risks)
    if c.open_questions:
        section("Open questions")
        bullets(c.open_questions)
    if c.references:
        section(f"References ({len(c.references)})")
        for i, ref in enumerate(c.references, 1):
            para(f"{i}. {ref}", 8.5, SLATE, h=4.3)

    pdf.ln(4)
    para(c.disclaimer, 7.5, MUTED, h=3.8)
    return bytes(pdf.output())


def _register_font(pdf) -> str:
    for regular, bold in _FONT_CANDIDATES:
        if Path(regular).exists() and Path(bold).exists():
            try:
                pdf.add_font("Brief", "", regular)
                pdf.add_font("Brief", "B", bold)
                return "Brief"
            except Exception:  # noqa: BLE001
                continue
    return "Helvetica"


def _header_band(pdf, c: BriefContent, family: str, t) -> None:
    from fpdf.enums import XPos, YPos

    pdf.set_fill_color(*INK)
    pdf.rect(0, 0, pdf.w, 38, style="F")
    pdf.set_fill_color(*INDIGO)
    pdf.rect(0, 38, pdf.w, 1.2, style="F")
    pdf.set_xy(16, 9)
    pdf.set_font(family, "B", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 4, "IMPACTPILOT  ·  IMPACT BRIEF" if family != "Helvetica" else "IMPACTPILOT - IMPACT BRIEF",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(16)
    pdf.set_font(family, "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(pdf.w - 70, 8, t(c.title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if c.score_line:
        pdf.set_x(16)
        pdf.set_font(family, "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, t(f"Impact score {c.score_line}"))
    tag, fg, bg = ("DRAFT", AMBER, AMBER_BG) if c.status == "draft" else ("CONFIRMED", GREEN, (209, 250, 229))
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*fg)
    pdf.set_font(family, "B", 9)
    pdf.set_xy(pdf.w - 16 - 30, 11)
    pdf.cell(30, 8, tag, align="C", fill=True)
    pdf.set_xy(16, 46)


def _draft_watermark(pdf, family: str) -> None:
    with pdf.local_context(fill_opacity=0.06, text_color=AMBER):
        pdf.set_font(family, "B", 90)
        with pdf.rotation(35, pdf.w / 2, pdf.h / 2):
            pdf.text(pdf.w / 2 - 62, pdf.h / 2 + 12, "DRAFT")
    pdf.set_xy(16, 46)


def _facts_grid(pdf, c: BriefContent, font, t) -> None:
    from fpdf.enums import XPos, YPos

    col_w = (pdf.w - pdf.l_margin - pdf.r_margin - 6) / 2
    x0, y = pdf.l_margin, pdf.get_y()
    for i, (label, value) in enumerate(c.facts):
        x = x0 + (i % 2) * (col_w + 6)
        if i % 2 == 0 and i:
            y += 13
        pdf.set_fill_color(*SURFACE)
        pdf.rect(x, y, col_w, 11.5, style="F")
        pdf.set_xy(x + 3, y + 1.5)
        font(7, True, MUTED)
        pdf.cell(col_w - 6, 3.5, t(label.upper()), new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.set_x(x + 3)
        font(10, True, INK)
        pdf.cell(col_w - 6, 5, t(value)[:60])
    pdf.set_xy(pdf.l_margin, y + 14)
