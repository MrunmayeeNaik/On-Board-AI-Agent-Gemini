"""Learning Path tab — renders Agent 2's Markdown with the ``- [ ]`` task items as interactive checkboxes and persists progress."""

import streamlit as st

from agents.orchestrator import save_progress
from utils.progress import parse_blocks


def _render_tracked_markdown(
    markdown: str,
    progress: dict,
    state_key: str,
) -> dict:
    """Render Markdown with ``- [ ]`` task items as interactive Streamlit checkboxes, returning the up-to-date progress dict.

    Args:
        markdown: Source Markdown (typically Agent 2's output).
        progress: ``{task_id: bool}`` map persisted from the session JSON. Used to seed
            widget state on first render.
        state_key: Namespace prefix for widget keys (e.g. ``"a2"``) — prevents collisions
            if multiple tracked sections are ever rendered on the same page.

    Returns:
        Updated ``{task_id: bool}`` map reflecting the live checkbox state for the parsed
        tasks. Caller is responsible for diffing this against the input and persisting.
    """
    blocks = parse_blocks(markdown)

    for block in blocks:
        if block["type"] == "task":
            cb_key = f"{state_key}_{block['id']}"
            if cb_key not in st.session_state:
                st.session_state[cb_key] = bool(progress.get(block["id"], False))

    # Reserve a slot for the progress bar so we can render it ABOVE the checkboxes
    # but populate it AFTER reading their live state — otherwise the bar lags by one rerun.
    progress_placeholder = st.empty()

    updated = dict(progress)
    for block in blocks:
        if block["type"] == "md":
            text = block["text"].strip()
            if text:
                st.markdown(text)
        else:
            cb_key = f"{state_key}_{block['id']}"
            checked = st.checkbox(block["text"], key=cb_key)
            updated[block["id"]] = checked

    task_blocks = [b for b in blocks if b["type"] == "task"]
    total = len(task_blocks)
    done = sum(1 for b in task_blocks if updated.get(b["id"]))
    if total:
        pct = done / total
        progress_placeholder.progress(pct, text=f"Progress: {done}/{total} ({int(pct * 100)}%)")

    return updated


def render_tab2(
    agent2_output: str | None,
    progress: dict | None = None,
    profile: dict | None = None,
) -> None:
    """Render the Learning Path tab: interactive 30-60-90 day plan with checkable items, persisting progress on each toggle.

    Args:
        agent2_output: Agent 2's Markdown summary. When ``None``, an info banner is shown
            prompting the user to complete Setup first.
        progress: Persisted ``{task_id: bool}`` map (seeds the checkboxes).
        profile: Session profile dict — when present, progress changes are written to disk
            via :func:`agents.orchestrator.save_progress`.
    """
    st.markdown("<div class='section-eyebrow'>Step 2 of 3</div>", unsafe_allow_html=True)
    st.header("📚 Your Learning Path")
    st.caption("Personalized 30-60-90 day growth plan — check items off as you complete them.")

    if not agent2_output:
        st.info("Complete Employee Setup in Tab 1 first to generate your learning path.")
        return

    progress = dict(progress or {})
    updated = _render_tracked_markdown(agent2_output, progress, state_key="a2")

    if profile and updated != progress:
        save_progress(profile["name"], profile["role"], updated)
        st.session_state["session"]["progress"] = updated
