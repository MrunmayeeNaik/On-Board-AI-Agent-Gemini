import streamlit as st

from agents.orchestrator import run_intake, run_chat, load_session
from ui.tab1_setup import render_tab1
from ui.tab2_learning import render_tab2
from ui.tab3_chat import render_tab3


def _has_session() -> bool:
    """Return True when an onboarding session has been generated in this Streamlit run."""
    return st.session_state.get("session") is not None


def _chat_callback(question: str, _history_text: str) -> str:
    """Bridge tab3's (question, history_text) callback to the orchestrator's run_chat using the active profile."""
    profile = st.session_state["session"]["profile"]
    result = run_chat(
        name=profile["name"],
        role=profile["role"],
        question=question,
    )
    st.session_state["session"]["chat_history"] = result["chat_history"]
    return result["summary_md"]


def main() -> None:
    """Configure the Streamlit page and mount the three onboarding tabs."""
    st.set_page_config(
        page_title="On-Board AI Agent",
        page_icon="🤝",
        layout="wide",
    )

    st.title("🤝 On-Board AI Agent")
    st.caption("A multi-agent onboarding assistant powered by Gemini 2.0 Flash")

    if "session" not in st.session_state:
        st.session_state["session"] = None

    tab1, tab2, tab3 = st.tabs(
        ["1. Setup", "2. Learning Path", "3. HR Buddy"]
    )

    with tab1:
        name, role, department, generate = render_tab1()
        if generate:
            if not name or not role:
                st.error("Please enter both a name and a role before generating.")
            else:
                with st.spinner("Provisioning tools and building learning path..."):
                    session = run_intake(
                        name=name, role=role, department=department
                    )
                st.session_state["session"] = session
                st.session_state["chat_display"] = []
                st.success(
                    f"Onboarding plan ready for {name}. Open the Learning Path and HR Buddy tabs."
                )

        if _has_session():
            st.divider()
            st.subheader("📋 Provisioning Summary")
            st.markdown(
                st.session_state["session"]["agent1_output"]["summary_md"]
            )

    with tab2:
        if _has_session():
            render_tab2(
                agent2_output=st.session_state["session"]["agent2_output"]["summary_md"]
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
