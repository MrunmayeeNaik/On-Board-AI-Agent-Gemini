"""Streamlit entrypoint. Mounts the custom CSS, sidebar, and the three onboarding tabs (Setup → Learning Path → HR Buddy)."""

import streamlit as st

from agents.orchestrator import run_chat, run_intake, save_progress
from ui.sidebar import render_sidebar
from ui.styles import hero, inject_css, metric_tiles
from ui.tab1_setup import render_tab1
from ui.tab2_learning import render_tab2
from ui.tab3_chat import render_tab3
from utils.progress import compute_live_progress, strip_task_syntax


def _has_session() -> bool:
    """Return ``True`` when an onboarding session has been generated in this Streamlit run.

    Returns:
        ``True`` if ``st.session_state["session"]`` holds a session dict, else ``False``.
    """
    return st.session_state.get("session") is not None


def _extract_contacts(agent1_md: str) -> str:
    """Extract the ``Key Contacts`` section text from Agent 1's Markdown so it can be passed to Agent 3 for escalation.

    The function captures every line between the first H2 heading containing the word
    ``contact`` and the next H2 heading.

    Args:
        agent1_md: Agent 1's full Markdown output.

    Returns:
        The captured section's text (without the heading itself), or an empty string when
        no matching section is found.
    """
    if not agent1_md:
        return ""
    lines = agent1_md.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("## "):
            if capturing:
                break
            if "contact" in stripped.lower():
                capturing = True
                continue
        if capturing:
            out.append(line)
    return "\n".join(out).strip()


def _chat_callback(question: str, _history_text: str) -> str:
    """Bridge tab 3's ``(question, history_text)`` callback to the orchestrator's ``run_chat`` using the active profile and handbook.

    Args:
        question: The user's current question.
        _history_text: History string built by the chat tab — unused here because the
            orchestrator rebuilds it from the persisted session.

    Returns:
        The assistant's Markdown response.
    """
    session = st.session_state["session"]
    profile = session["profile"]
    handbook_text = session.get("handbook", {}).get("text", "")
    contacts_text = _extract_contacts(session.get("agent1_output", {}).get("summary_md", ""))

    result = run_chat(
        name=profile["name"],
        role=profile["role"],
        question=question,
        handbook_text=handbook_text,
        contacts_text=contacts_text,
    )
    st.session_state["session"]["chat_history"] = result["chat_history"]
    return result["summary_md"]


def _on_persona_pick(profile: dict) -> None:
    """Push a selected persona's name/role/department into Tab 1's widget state so the form prefills on the next render.

    Args:
        profile: Persona dict from ``data/personas/*.json``, typically containing
            ``name``, ``role``, ``department``.
    """
    st.session_state["tab1_name"] = profile.get("name", "")
    st.session_state["tab1_role"] = profile.get("role", "")
    dept = profile.get("department", "Engineering")
    st.session_state["tab1_dept"] = (
        dept if dept in {"Engineering", "Marketing", "Sales", "HR"} else "Engineering"
    )


def _on_session_resume(session: dict) -> None:
    """Restore a saved session into ``st.session_state``, including replaying chat history into the display buffer.

    Args:
        session: The session dict loaded from disk by the orchestrator.
    """
    st.session_state["session"] = session
    st.session_state["chat_display"] = list(session.get("chat_history", []))


def main() -> None:
    """Configure the Streamlit page, inject custom styling, and mount the sidebar plus three onboarding tabs.

    This is the only function Streamlit invokes when the app starts. It runs top-to-bottom
    on every rerun, which is why progress is recomputed from widget state at the top of the
    function rather than from disk.
    """
    st.set_page_config(
        page_title="On-Board AI Agent",
        page_icon="🤝",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    if "session" not in st.session_state:
        st.session_state["session"] = None
    if "chat_display" not in st.session_state:
        st.session_state["chat_display"] = []

    session = st.session_state.get("session")
    if session:
        # Recompute progress from live checkbox widget state so the sidebar/hero/metrics
        # render with the same numbers the user just clicked into. Persist to disk when
        # the live state diverges from the on-disk dict.
        prev_progress = session.get("progress", {})
        done, total, live_progress = compute_live_progress(
            sections=[
                (session["agent2_output"]["summary_md"], "a2"),
            ],
            base_progress=prev_progress,
        )
        if live_progress != prev_progress:
            profile = session["profile"]
            save_progress(profile["name"], profile["role"], live_progress)
        session["progress"] = live_progress

    render_sidebar(on_persona_pick=_on_persona_pick, on_session_resume=_on_session_resume)

    if session:
        profile = session["profile"]
        handbook_name = session.get("handbook", {}).get("filename") or "Default sample"
        hero(
            f"Welcome, {profile['name']} 👋",
            f"Your AI-generated onboarding plan for {profile['role']} in {profile['department']}.",
            badges=[
                f"📘 Handbook: {handbook_name}",
                f"✅ {done}/{total} items done" if total else "🆕 Plan ready",
                "🤖 Gemini-powered",
            ],
        )
        metric_tiles(
            [
                ("Department", profile["department"]),
                ("Role", profile["role"]),
                ("Progress", f"{(done / total * 100):.0f}%" if total else "—"),
                ("Chat turns", str(len(session.get("chat_history", [])) // 2)),
            ]
        )
    else:
        hero(
            "On-Board AI Agent",
            "A multi-agent onboarding assistant powered by Gemini 2.0 Flash.",
            badges=["🛠️ Provisioning", "📚 Learning Path", "💬 HR Buddy"],
        )

    tab1, tab2, tab3 = st.tabs(["1. Setup", "2. Learning Path", "3. HR Buddy"])

    with tab1:
        name, role, department, handbook_text, handbook_filename, generate = render_tab1()
        if generate:
            if not name or not role:
                st.error("Please enter both a name and a role before generating.")
            else:
                with st.spinner("Provisioning tools and building learning path..."):
                    new_session = run_intake(
                        name=name,
                        role=role,
                        department=department,
                        handbook_text=handbook_text,
                        handbook_filename=handbook_filename,
                    )
                st.session_state["session"] = new_session
                st.session_state["chat_display"] = []
                st.success(
                    f"Onboarding plan ready for {name}. Open the Learning Path and HR Buddy tabs."
                )
                st.rerun()

        if _has_session():
            st.divider()
            st.subheader("📋 Provisioning Summary")
            st.markdown(
                strip_task_syntax(st.session_state["session"]["agent1_output"]["summary_md"])
            )

    with tab2:
        if _has_session():
            render_tab2(
                agent2_output=st.session_state["session"]["agent2_output"]["summary_md"],
                progress=st.session_state["session"].get("progress", {}),
                profile=st.session_state["session"]["profile"],
            )
        else:
            render_tab2(agent2_output=None)

    with tab3:
        if _has_session():
            render_tab3(chat_function=_chat_callback)
        else:
            st.header("💬 Ask HR Anything")
            st.info("Complete Employee Setup in Tab 1 first to start chatting.")


if __name__ == "__main__":
    main()
