"""Left sidebar rendering: persona quick-load, saved-session browser, progress snapshot, and PDF export button."""

import json
import os
from collections.abc import Callable

import streamlit as st

from agents.orchestrator import list_sessions, load_session

PERSONAS_DIR = os.path.join("data", "personas")


def _load_personas() -> list[dict]:
    """Read every JSON file in ``data/personas/`` and return them as a list of profile dicts.

    Returns:
        List of ``{"name", "role", "department"}`` dicts, sorted by filename. Files that
        fail to parse are silently skipped.
    """
    if not os.path.isdir(PERSONAS_DIR):
        return []
    out: list[dict] = []
    for fname in sorted(os.listdir(PERSONAS_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(PERSONAS_DIR, fname)) as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


def render_sidebar(
    on_persona_pick: Callable[[dict], None],
    on_session_resume: Callable[[dict], None],
) -> None:
    """Render the left sidebar — current-session card, persona presets, saved sessions, and PDF export.

    Args:
        on_persona_pick: Callback fired when a persona button is clicked. Receives the
            persona dict and should populate ``st.session_state`` to prefill the Setup form.
        on_session_resume: Callback fired when a saved-session button is clicked. Receives
            the loaded session dict and should restore it into ``st.session_state``.
    """
    with st.sidebar:
        st.markdown(
            "<div style='font-weight:700;font-size:1.1rem;margin-bottom:6px;'>🤝 On-Board AI</div>"
            "<div style='color:#94A3B8;font-size:0.85rem;margin-bottom:14px;'>Multi-agent onboarding assistant</div>",
            unsafe_allow_html=True,
        )

        session = st.session_state.get("session")
        if session:
            profile = session.get("profile", {})
            progress = session.get("progress", {})
            done = sum(1 for v in progress.values() if v)
            total = len(progress) or 0
            st.markdown("### Current Session")
            st.markdown(
                f"**{profile.get('name', '')}**  \n"
                f"{profile.get('role', '')} · {profile.get('department', '')}"
            )
            if total:
                st.progress(min(done / total, 1.0), text=f"{done}/{total} items complete")
            else:
                st.caption("No tracked items yet — open the Learning Path tab to track progress.")
            if st.button("🔄 Reset session", use_container_width=True):
                st.session_state["session"] = None
                st.session_state["chat_display"] = []
                st.rerun()

        st.markdown("### Personas")
        personas = _load_personas()
        if not personas:
            st.caption("No personas found in data/personas/")
        else:
            for p in personas:
                label = f"👤 {p.get('name', '?')} — {p.get('role', '')}"
                if st.button(
                    label,
                    key=f"persona_{p.get('name', '')}_{p.get('role', '')}",
                    use_container_width=True,
                ):
                    on_persona_pick(p)
                    st.rerun()

        st.markdown("### Saved Sessions")
        sessions = list_sessions()
        if not sessions:
            st.caption("No saved sessions yet.")
        else:
            for s in sessions[:8]:
                label = f"📂 {s['name']} — {s['role']}"
                if st.button(label, key=f"resume_{s['slug']}", use_container_width=True):
                    loaded = load_session(s["name"], s["role"])
                    if loaded is not None:
                        on_session_resume(loaded)
                        st.rerun()

        st.markdown("### Export")
        if session:
            # Lazy-import keeps Streamlit's reload faster on first paint when no session exists.
            from utils.export import build_export_pdf

            pdf_bytes = build_export_pdf(session)
            fname = f"{profile.get('name', 'session').lower().replace(' ', '_')}_onboarding.pdf"
            st.download_button(
                "⬇️ Download onboarding pack (PDF)",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.caption("Generate a plan to enable export.")
