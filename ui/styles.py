"""Custom CSS injection and small render helpers (hero banner, metric tiles) used to dress up the default Streamlit chrome."""

import streamlit as st

CUSTOM_CSS = """
<style>
:root {
    --accent-from: #6366F1;
    --accent-to: #8B5CF6;
    --accent-soft: rgba(99, 102, 241, 0.12);
    --card-bg: #1E293B;
    --card-border: rgba(148, 163, 184, 0.15);
    --muted: #94A3B8;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
}

/* Hide default Streamlit chrome */
#MainMenu, footer {visibility: hidden;}

/* Hero header */
.hero {
    background: linear-gradient(135deg, var(--accent-from) 0%, var(--accent-to) 100%);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.25);
    color: white;
}
.hero h1 {
    margin: 0;
    font-size: 2.0rem;
    font-weight: 700;
    color: white !important;
}
.hero p {
    margin: 6px 0 0 0;
    color: rgba(255, 255, 255, 0.85);
    font-size: 1.0rem;
}
.hero .badges {margin-top: 14px;}
.hero .badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.18);
    color: white;
    font-size: 0.78rem;
    margin-right: 8px;
    backdrop-filter: blur(6px);
}

/* Section card */
.card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 14px;
}

/* Metric tiles */
.metric-row {display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px;}
.metric {
    flex: 1;
    min-width: 140px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 14px 16px;
}
.metric .label {
    color: var(--muted);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.metric .value {
    font-size: 1.55rem;
    font-weight: 700;
    margin-top: 4px;
    background: linear-gradient(135deg, var(--accent-from), var(--accent-to));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid var(--card-border);
    font-weight: 600;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(99, 102, 241, 0.25);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-from), var(--accent-to));
    border: none;
    color: white;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--card-bg);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid var(--card-border);
}
.stTabs [data-baseweb="tab"] {
    height: 42px;
    padding: 0 18px;
    border-radius: 9px;
    color: var(--muted);
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent-from), var(--accent-to)) !important;
    color: white !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0B1220;
    border-right: 1px solid var(--card-border);
}
[data-testid="stSidebar"] h3 {
    color: var(--muted);
    text-transform: uppercase;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    margin-top: 16px;
}

/* Chat */
[data-testid="stChatMessage"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 8px 14px;
    margin-bottom: 8px;
}

/* Progress bar accent */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent-from), var(--accent-to)) !important;
}

/* Section heading helper */
.section-eyebrow {
    color: var(--muted);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: -4px;
}

/* Suggested-question chips */
.chip-row {display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;}

/* Inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 10px !important;
}
</style>
"""


def inject_css() -> None:
    """Inject the project's custom CSS into the current Streamlit page.

    Call once at the top of :func:`app.main`, after :func:`st.set_page_config`.
    Streamlit's ``unsafe_allow_html=True`` is required to render the ``<style>`` block.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, badges: list[str] | None = None) -> None:
    """Render a gradient hero banner with title, subtitle, and optional pill badges.

    Args:
        title: Main headline text (one line).
        subtitle: Smaller supporting text shown below the title.
        badges: Optional list of short labels rendered as rounded pills.
    """
    badge_html = ""
    if badges:
        spans = "".join(f"<span class='badge'>{b}</span>" for b in badges)
        badge_html = f"<div class='badges'>{spans}</div>"
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_tiles(items: list[tuple[str, str]]) -> None:
    """Render a horizontal row of (label, value) metric tiles with gradient-styled values.

    Args:
        items: List of ``(label, value)`` pairs. The label is rendered as a small uppercase
            caption; the value is rendered larger with the app's accent gradient applied.
    """
    tiles = "".join(
        f"<div class='metric'><div class='label'>{label}</div><div class='value'>{value}</div></div>"
        for label, value in items
    )
    st.markdown(f"<div class='metric-row'>{tiles}</div>", unsafe_allow_html=True)
