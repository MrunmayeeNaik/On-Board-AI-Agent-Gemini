"""HR Buddy chat tab — multi-turn conversation with Agent 3, including suggested-question chips for the empty state."""

import streamlit as st

SUGGESTED_QUESTIONS = [
    "How many leave days do I have?",
    "What's the work-from-home policy?",
    "When is my probation review?",
    "How do I file expenses?",
]


def _process_turn(user_input: str, chat_function) -> None:
    """Append the user message, call the chat function for a reply, and append the assistant message to the displayed history.

    Args:
        user_input: The user's question text.
        chat_function: Callback ``(question, history_text) -> assistant_markdown`` provided
            by ``app.py``. It is responsible for routing to the orchestrator and persisting
            chat history on the session.
    """
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    st.session_state.chat_display.append({"role": "user", "content": user_input})

    with (
        st.chat_message("assistant", avatar="🤖"),
        st.spinner("Looking that up in the handbook..."),
    ):
        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in st.session_state.chat_display[:-1]
        )
        response = chat_function(user_input, history_text)
        st.markdown(response)

    st.session_state.chat_display.append({"role": "assistant", "content": response})


def render_tab3(chat_function) -> None:
    """Render the HR Buddy chat tab with suggested-question chips and handbook-cited replies.

    Args:
        chat_function: Callback ``(question, history_text) -> assistant_markdown``.
            Same shape as in :func:`_process_turn`.
    """
    st.markdown("<div class='section-eyebrow'>Step 3 of 3</div>", unsafe_allow_html=True)
    st.header("💬 Ask HR Anything")
    st.caption("Your AI HR buddy — grounded in the company handbook, available 24/7.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_display" not in st.session_state:
        st.session_state.chat_display = []

    if not st.session_state.chat_display:
        st.markdown("**Try one of these to get started:**")
        cols = st.columns(len(SUGGESTED_QUESTIONS))
        for col, q in zip(cols, SUGGESTED_QUESTIONS, strict=True):
            with col:
                if st.button(q, key=f"suggest_{q}", use_container_width=True):
                    # Stash the chip's text and rerun so the regular chat path picks it up.
                    st.session_state["_pending_question"] = q
                    st.rerun()

    for message in st.session_state.chat_display:
        avatar = "🧑" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    pending = st.session_state.pop("_pending_question", None)
    user_input = st.chat_input("Ask me anything about HR policies...")
    if pending and not user_input:
        user_input = pending

    if user_input:
        _process_turn(user_input, chat_function)
