"""Bundle a saved onboarding session into a downloadable artifact — Markdown for raw text, or a styled PDF for handoff."""

import re
import unicodedata
from datetime import datetime

from fpdf import FPDF

from utils.progress import strip_task_syntax


def build_export_markdown(session: dict) -> str:
    """Render the full session (profile, provisioning, learning plan, chat log) as a single Markdown string.

    Args:
        session: The orchestrator's session dict, containing ``profile``, ``agent1_output``,
            ``agent2_output``, ``chat_history``, ``progress``, and ``handbook`` keys.

    Returns:
        A Markdown document suitable for ``.md`` download. Task syntax is left intact so
        the original ``[x]`` / ``[ ]`` markers remain readable in source form.
    """
    profile = session.get("profile", {})
    name = profile.get("name", "Unknown")
    role = profile.get("role", "")
    dept = profile.get("department", "")

    a1 = session.get("agent1_output", {}).get("summary_md", "").strip()
    a2 = session.get("agent2_output", {}).get("summary_md", "").strip()
    chat = session.get("chat_history", [])
    handbook = session.get("handbook", {})

    progress = session.get("progress", {})
    progress_summary = ""
    if progress:
        done = sum(1 for v in progress.values() if v)
        total = len(progress)
        progress_summary = f"\n**Progress tracked:** {done} / {total} items checked off.\n"

    parts = [
        f"# Onboarding Pack — {name}",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        f"**Role:** {role}  ",
        f"**Department:** {dept}  ",
        f"**Handbook:** {handbook.get('filename') or 'default sample'}",
        progress_summary,
        "---",
        "",
        "# 1. Provisioning Plan",
        a1 or "_No provisioning output._",
        "",
        "---",
        "",
        "# 2. Learning Path",
        a2 or "_No learning plan output._",
        "",
        "---",
        "",
        "# 3. HR Buddy Chat Log",
    ]

    if not chat:
        parts.append("_No conversation yet._")
    else:
        for turn in chat:
            label = "**You**" if turn.get("role") == "user" else "**HR Buddy**"
            parts.append(f"\n{label}: {turn.get('content', '').strip()}")

    return "\n".join(parts)


# fpdf2's built-in Helvetica is Latin-1 only, so unicode chars must be normalized
# (or stripped) before reaching the PDF writer. Common typographic chars get nice
# replacements; everything else falls back to NFKD decomposition.
_UNICODE_REPLACEMENTS = {
    "—": "-",  # em dash
    "–": "-",  # en dash
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "•": "*",  # bullet
    "…": "...",  # ellipsis
    " ": " ",  # nbsp
    "₹": "Rs.",  # rupee
}


def _to_latin1(text: str) -> str:
    """Convert a unicode string into a Latin-1 compatible string by substituting common chars and stripping emojis.

    Args:
        text: Arbitrary unicode source text.

    Returns:
        A string containing only Latin-1 (``ord < 256``) code points. Non-Latin-1
        characters are first run through NFKD decomposition to recover ASCII letters
        from accented forms; un-recoverable characters (most emojis) are dropped.
    """
    for src, dst in _UNICODE_REPLACEMENTS.items():
        text = text.replace(src, dst)
    out: list[str] = []
    for ch in text:
        if ord(ch) < 256:
            out.append(ch)
            continue
        decomposed = unicodedata.normalize("NFKD", ch)
        ascii_eq = "".join(c for c in decomposed if ord(c) < 128)
        out.append(ascii_eq)
    return "".join(out)


class _OnboardingPDF(FPDF):
    """FPDF subclass that draws a centered page-number footer on every page."""

    def footer(self) -> None:
        """Render a small muted ``Page N`` label 14mm from the bottom of every page (called by fpdf2 on each page break)."""
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 150)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


# Theme colors matched to the Streamlit UI's indigo/violet accent.
_ACCENT = (99, 102, 241)
_DARK = (30, 41, 59)
_BODY = (40, 40, 48)
_MUTED = (130, 130, 145)


def _section_header(pdf: FPDF, title: str) -> None:
    """Render a styled section title with an underline rule using the app's accent color.

    Args:
        pdf: The PDF object being built.
        title: Heading text to render (e.g. ``"1. Provisioning Plan"``).
    """
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*_ACCENT)
    pdf.cell(0, 9, _to_latin1(title), ln=1)
    pdf.set_draw_color(*_ACCENT)
    pdf.set_line_width(0.6)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(3)


def _render_markdown_into_pdf(pdf: FPDF, markdown: str) -> None:
    """Walk Markdown line-by-line and render headings, task items, bullets, and paragraphs into the PDF.

    Args:
        pdf: The PDF object being built.
        markdown: Markdown source. Task syntax is rendered with ``[x]`` / ``[ ]`` markers;
            apply :func:`utils.progress.strip_task_syntax` first if plain bullets are desired.
    """
    for raw_line in markdown.splitlines():
        # Reset X to the left margin in case a previous block left the cursor mid-line.
        pdf.set_x(pdf.l_margin)
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            pdf.ln(2)
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            if level <= 2:
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(*_DARK)
            else:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(*_ACCENT)
            pdf.multi_cell(0, 6, _to_latin1(text))
            pdf.ln(1)
            continue

        task = re.match(r"^\s*[-*]\s*\[([ xX])\]\s*(.+)$", line)
        if task:
            checked = task.group(1).strip().lower() == "x"
            text = task.group(2)
            marker = "[x]" if checked else "[ ]"
            pdf.set_font("Helvetica", "B" if checked else "", 11)
            pdf.set_text_color(*_BODY)
            pdf.multi_cell(0, 5.5, _to_latin1(f"  {marker}  {text}"))
            continue

        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet:
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(*_BODY)
            pdf.multi_cell(0, 5.5, _to_latin1(f"  -  {bullet.group(1)}"))
            continue

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*_BODY)
        pdf.multi_cell(0, 5.5, _to_latin1(stripped))


def build_export_pdf(session: dict) -> bytes:
    """Render the full session (profile, provisioning, learning plan, chat log) as a styled PDF and return the raw bytes.

    Args:
        session: The orchestrator's session dict (same shape as :func:`build_export_markdown`).

    Returns:
        Raw PDF bytes ready to hand to a Streamlit ``st.download_button``. Task syntax is
        stripped from the agents' output so the printed document shows clean bullets.
    """
    profile = session.get("profile", {})
    name = profile.get("name", "Unknown")
    role = profile.get("role", "")
    dept = profile.get("department", "")
    handbook = session.get("handbook", {})
    progress = session.get("progress", {})

    pdf = _OnboardingPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(left=18, top=18, right=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*_ACCENT)
    pdf.cell(0, 12, _to_latin1(f"Onboarding Pack — {name}"), ln=1)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*_MUTED)
    pdf.cell(
        0,
        5,
        _to_latin1(f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
        ln=1,
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*_BODY)
    meta_lines = [
        ("Role", role),
        ("Department", dept),
        ("Handbook", handbook.get("filename") or "default sample"),
    ]
    if progress:
        done = sum(1 for v in progress.values() if v)
        total = len(progress)
        meta_lines.append(("Progress", f"{done} / {total} items checked off"))

    for label, value in meta_lines:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*_DARK)
        pdf.write(6, _to_latin1(f"{label}: "))
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*_BODY)
        pdf.write(6, _to_latin1(str(value)))
        pdf.ln(6)

    _section_header(pdf, "1. Provisioning Plan")
    a1 = session.get("agent1_output", {}).get("summary_md", "").strip()
    _render_markdown_into_pdf(pdf, strip_task_syntax(a1) if a1 else "_No provisioning output._")

    _section_header(pdf, "2. Learning Path")
    a2 = session.get("agent2_output", {}).get("summary_md", "").strip()
    _render_markdown_into_pdf(pdf, strip_task_syntax(a2) if a2 else "_No learning plan output._")

    _section_header(pdf, "3. HR Buddy Chat Log")
    chat = session.get("chat_history", [])
    if not chat:
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(*_MUTED)
        pdf.multi_cell(0, 6, _to_latin1("No conversation yet."))
    else:
        for turn in chat:
            label = "You" if turn.get("role") == "user" else "HR Buddy"
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*_ACCENT if label == "HR Buddy" else _DARK)
            pdf.cell(0, 6, _to_latin1(f"{label}:"), ln=1)
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(*_BODY)
            pdf.multi_cell(0, 6, _to_latin1(turn.get("content", "").strip()))
            pdf.ln(1)

    return bytes(pdf.output())
