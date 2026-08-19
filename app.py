import streamlit as st
import os
from models.database import init_db
from core.auth import require_login, logout
from core.ui_utils import inject_custom_css

st.set_page_config(
    page_title="Process Note Validator",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()

def main():
    # Always init DB to ensure tables exist in PostgreSQL
    init_db()
    
    # Enforce authentication
    require_login()

    st.sidebar.title("Process Validator")
    st.sidebar.markdown(f"Logged in as: **{st.session_state.current_user_name}**")
    if st.sidebar.button("Log Out"):
        logout()
        
    st.sidebar.markdown("---")

    st.title("Process Note Validator")
    st.markdown("""
    This application acts as an AI-assisted quality gate before manual review.
    
    Please select a module from the sidebar to begin:
    - **Dashboard:** View overall metrics and recent process notes.
    - **Create Process:** Draft a new process note.
    - **Validation:** Run AI validation on a drafted note.
    - **Review:** Manual reviewer dashboard.
    """)
    
    st.info("Current AI Provider Mode: " + os.getenv("LLM_PROVIDER", "mock").upper())

if __name__ == "__main__":
    main()
