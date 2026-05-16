import streamlit as st

def render_tab3(chat_function):
    """Render the HR Buddy chat tab, routing user messages through the supplied chat_function(question, history_text) callback."""
    st.header("💬 Ask HR Anything")
    st.caption("Your AI-powered HR assistant — available 24/7")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_display" not in st.session_state:
        st.session_state.chat_display = []

    # Display chat history
    for message in st.session_state.chat_display:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask me anything about HR policies...")

    if user_input:
        # Show user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_display.append({
            "role": "user",
            "content": user_input
        })

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history_text = "\n".join([
                    f"{m['role']}: {m['content']}"
                    for m in st.session_state.chat_display[:-1]
                ])
                response = chat_function(user_input, history_text)
                st.markdown(response)

        st.session_state.chat_display.append({
            "role": "assistant",
            "content": response
        })