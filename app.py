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

    from core.auth import get_kef_logo_base64
    logo_b64 = get_kef_logo_base64()
    if logo_b64:
        st.sidebar.markdown(f"""
        <div style="display: flex; justify-content: flex-start; align-items: center; padding: 4px 0 12px 0;">
            <img src="data:image/png;base64,{logo_b64}" alt="Kotak Education Foundation" style="max-width: 175px; width: 85%; height: auto;" />
        </div>
        """, unsafe_allow_html=True)

    st.sidebar.title("Process Validator")

    role = st.session_state.get("current_user_role", "creator")

    dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard")
    create_page = st.Page("pages/2_Create_Process.py", title="Create/Edit Process Note")
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

    # Brand header on top left of the main page canvas
    if logo_b64:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; align-items: center; padding-top: 2px; margin-bottom: 14px;">
            <img src="data:image/png;base64,{logo_b64}" alt="Kotak Education Foundation" style="max-height: 44px; width: auto;" />
        </div>
        """, unsafe_allow_html=True)

    pg.run()

if __name__ == "__main__":
    main()
