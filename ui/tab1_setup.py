import streamlit as st

def render_tab1():
    st.header("🔧 Employee Setup")
    st.caption("Fill in the new employee details to generate their onboarding plan")

    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name", placeholder="e.g. Arjun Mehta")
        role = st.text_input("Role", placeholder="e.g. Backend Engineer")
    
    with col2:
        department = st.selectbox(
            "Department",
            ["Engineering", "Marketing", "Sales", "HR"]
        )
        
    st.divider()
    
    generate = st.button("🚀 Generate Onboarding Plan", use_container_width=True)
    
    return name, role, department, generate