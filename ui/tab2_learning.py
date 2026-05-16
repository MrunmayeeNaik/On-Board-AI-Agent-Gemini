import streamlit as st

def render_tab2(agent2_output: str = None):
    """Render the Learning Path tab, showing Agent 2's markdown plan when available or a setup-required notice otherwise."""
    st.header("📚 Your Learning Path")
    st.caption("Personalized 30-60-90 day growth plan based on your role")

    if agent2_output:
        st.markdown(agent2_output)
    else:
        st.info("Complete Employee Setup in Tab 1 first to generate your learning path.")