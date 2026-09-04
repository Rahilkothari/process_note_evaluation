import streamlit as st
st.set_page_config(
    page_title="Process Note Validator",
    layout="wide",
    initial_sidebar_state="expanded",
)
import os
from models.database import init_db
from core.auth import require_login, logout
from core.ui_utils import inject_custom_css

inject_custom_css()

def main():
    # Always init DB to ensure tables exist in PostgreSQL
    init_db()
    
    # Enforce authentication
    require_login()

    st.sidebar.title("Process Validator")

    role = st.session_state.get("current_user_role", "creator")

    dashboard_page = st.Page("pages/1_dashboard.py", title="Dashboard")
    create_page = st.Page("pages/2_create_process.py", title="Create Process")
    validation_page = st.Page("pages/3_validation.py", title="Validation")
    review_page = st.Page("pages/4_review.py", title="Review")
    view_all_page = st.Page("pages/5_view_all_notes.py", title="View All Notes")

    pg = st.navigation([dashboard_page, create_page, validation_page, review_page, view_all_page])

    from core.notifications import render_notifications_sidebar
    render_notifications_sidebar()

    pg.run()

if __name__ == "__main__":
    main()
