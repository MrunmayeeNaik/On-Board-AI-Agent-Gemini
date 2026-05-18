"""Setup tab — collects the new-hire profile and (optionally) a custom handbook upload."""

import streamlit as st

from utils.doc_loader import load_handbook

DEPARTMENTS = ["Engineering", "Marketing", "Sales", "HR"]


def render_tab1() -> tuple[str, str, str, str, str, bool]:
    """Render the Employee Setup form (name/role/department + handbook upload) and return its values.

    The function relies on Streamlit widget keys (``tab1_name``, ``tab1_role``, ``tab1_dept``)
    so that the persona-pick handler in ``app.py`` can prefill them by writing directly to
    ``st.session_state``.

    Returns:
        Tuple of ``(name, role, department, handbook_text, handbook_filename, generate_clicked)``.

        - ``handbook_text`` is the extracted PDF text (empty string when nothing uploaded).
        - ``handbook_filename`` is the original filename of the upload (empty string otherwise).
        - ``generate_clicked`` is ``True`` only on the rerun where the user just clicked the primary button.
    """
    st.markdown("<div class='section-eyebrow'>Step 1 of 3</div>", unsafe_allow_html=True)
    st.header("🔧 Employee Setup")
    st.caption("Fill in the new employee details and (optionally) upload your company handbook.")

    st.session_state.setdefault("tab1_name", "")
    st.session_state.setdefault("tab1_role", "")
    st.session_state.setdefault("tab1_dept", DEPARTMENTS[0])

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(
            "Full Name",
            key="tab1_name",
            placeholder="e.g. Arjun Mehta",
        )
        role = st.text_input(
            "Role",
            key="tab1_role",
            placeholder="e.g. Backend Engineer",
        )
    with col2:
        department = st.selectbox("Department", DEPARTMENTS, key="tab1_dept")
        uploaded = st.file_uploader(
            "Company handbook (PDF, optional)",
            type=["pdf"],
            help="If provided, Agent 2 (Learning Path) and Agent 3 (HR Buddy) will ground their answers in this file.",
        )

    handbook_text = ""
    handbook_filename = ""
    if uploaded is not None:
        handbook_text = load_handbook(uploaded_file=uploaded)
        handbook_filename = uploaded.name
        st.success(f"📄 Loaded handbook: **{uploaded.name}** ({len(handbook_text):,} chars)")

    st.divider()

    btn_left, btn_center, btn_right = st.columns([2, 3, 2])
    with btn_center:
        generate = st.button(
            "🚀 Generate Onboarding Plan",
            type="primary",
            use_container_width=True,
        )

    return name, role, department, handbook_text, handbook_filename, generate
