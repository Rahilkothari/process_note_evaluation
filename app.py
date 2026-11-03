import streamlit as st
import os

st.set_page_config(
    page_title="Process Note Validator",
    layout="wide",
    initial_sidebar_state="expanded",
)

from models.database import init_db
from core.auth import render_login_page, logout, render_sidebar_user_profile, sync_user_to_db
from core.ui_utils import inject_custom_css
from core.notifications import render_notifications_sidebar

inject_custom_css()

@st.cache_resource(show_spinner=False)
def cached_init_db():
    init_db()

def main():
    # 1. Initialize DB tables
    cached_init_db()

    # 2. Configure Brand Logo in Sidebar Header
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "kef_logo.png")
    if os.path.exists(logo_path):
        try:
            st.logo(logo_path, size="large")
        except Exception:
            pass

    # 3. Handle unauthenticated state using st.navigation so pages/ is NEVER auto-discovered
    if "user" not in st.session_state or st.session_state.user is None:
        login_page = st.Page(render_login_page, title="Sign In", icon="🔒")
        pg = st.navigation([login_page], position="hidden")
        pg.run()
        return

    # Ensure authenticated user metadata is synced
    if "current_user_name" not in st.session_state and st.session_state.user:
        try:
            sync_user_to_db(st.session_state.user.email)
        except Exception:
            st.session_state.user = None
            st.rerun()

    role = st.session_state.get("current_user_role", "creator")

    # 4. Standardized Pages Definition with explicit icons and url_paths
    dashboard_page = st.Page("views/1_Dashboard.py", title="Dashboard", icon="📊", url_path="Dashboard", default=True)
    create_page = st.Page("views/2_Create_Process.py", title="Create/Edit Process Note", icon="📝", url_path="Create_Process")
    validation_page = st.Page("views/3_Validation.py", title="Validation & Audit", icon="🛡️", url_path="Validation")
    review_page = st.Page("views/4_Review.py", title="Review & Sign-Off", icon="📋", url_path="Review")
    view_all_page = st.Page("views/5_View_All_Notes.py", title="View All Notes", icon="📚", url_path="View_All_Notes")
    version_history_page = st.Page("views/6_Version_History.py", title="Version History", icon="🕒", url_path="Version_History")

    # 5. Executive Enterprise Grouping (Dictionary prevents default "app" label)
    if role == "creator":
        pages = {
            "Process Workspace": [dashboard_page, create_page, validation_page],
            "Institutional Repository": [view_all_page, version_history_page],
        }
    elif role == "reviewer":
        pages = {
            "Governance Hub": [dashboard_page, review_page],
            "Institutional Repository": [view_all_page, version_history_page],
        }
    else:  # admin has full access to both Creator and Reviewer suites
        pages = {
            "Process Workspace": [dashboard_page, create_page, validation_page],
            "Governance & Review": [review_page],
            "Institutional Repository": [view_all_page, version_history_page],
        }

    pg = st.navigation(pages, position="sidebar")

    # 6. Sidebar Drawers: Notifications & User Profile Card
    render_notifications_sidebar()
    render_sidebar_user_profile()

    # 7. Execute Router
    pg.run()

if __name__ == "__main__":
    main()
