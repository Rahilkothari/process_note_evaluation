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

@st.cache_resource(show_spinner=False)
def cached_init_db():
    init_db()

def main():
    # Always init DB to ensure tables exist in PostgreSQL
    cached_init_db()
    
    # Enforce authentication
    require_login()

    st.sidebar.title("Process Validator")

    role = st.session_state.get("current_user_role", "creator")

    dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard")
    create_page = st.Page("pages/2_Create_Process.py", title="Create Process")
    validation_page = st.Page("pages/3_Validation.py", title="Validation")
    review_page = st.Page("pages/4_Review.py", title="Review")
    view_all_page = st.Page("pages/5_View_All_Notes.py", title="View All Notes")
    version_history_page = st.Page("pages/6_Version_History.py", title="Version History")

    if role == "creator":
        pages = [dashboard_page, create_page, validation_page, view_all_page, version_history_page]
    else:
        pages = [dashboard_page, review_page, view_all_page, version_history_page]
        
    pg = st.navigation(pages)

    from core.notifications import render_notifications_sidebar
    render_notifications_sidebar()

    pg.run()

if __name__ == "__main__":
    main()
