def render_sidebar_user_profile():
    if "user" not in st.session_state or st.session_state.user is None:
        return

    raw_name = st.session_state.get("current_user_name", "") or ""
    user_email = getattr(st.session_state.user, "email", "") if st.session_state.user else ""
    if not raw_name and user_email:
        raw_name = user_email.split("@")[0]

    display_name = raw_name.title() if raw_name else "Team Member"
    role = (st.session_state.get("current_user_role", "creator") or "creator").upper()

    parts = display_name.split()
    if len(parts) >= 2:
        initials = (parts[0][0] + parts[1][0]).upper()
    elif len(display_name) >= 2:
        initials = display_name[:2].upper()
    else:
        initials = "U"

    if role == "REVIEWER":
        role_bg = "#FAF5FF"
        role_color = "#7E22CE"
        role_border = "#E9D5FF"
        avatar_bg = "linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)"
        avatar_shadow = "rgba(109, 40, 217, 0.25)"
    else:
        role_bg = "#EEF2FF"
        role_color = "#4338CA"
        role_border = "#C7D2FE"
        avatar_bg = "linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)"
        avatar_shadow = "rgba(29, 78, 216, 0.25)"

    with st.sidebar:
        st.markdown("<hr style='margin: 16px 0 12px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        st.markdown(
            f'''
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: {avatar_bg}; color: #FFFFFF; font-weight: 700; font-size: 13.5px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 6px {avatar_shadow};">
                        {initials}
                    </div>
                    <div style="overflow: hidden; flex: 1;">
                        <div style="font-weight: 700; font-size: 13.5px; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;">
                            {display_name}
                        </div>
                        <div style="font-size: 11px; color: #64748B; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">
                            {user_email}
                        </div>
                        <div style="margin-top: 5px;">
                            <span style="font-size: 10px; font-weight: 700; background: {role_bg}; color: {role_color}; border: 1px solid {role_border}; padding: 2px 8px; border-radius: 6px; letter-spacing: 0.04em;">
                                {role}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        if st.button("🚪 Sign Out", key="global_logout", use_container_width=True, help="Sign out of your session"):
            logout()

import os
import streamlit as st
from supabase import create_client, Client
from supabase.client import ClientOptions
import httpx
from models.database import SessionLocal, User
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

def get_supabase_client() -> Client:
    """Create an un-cached, isolated Supabase client per request to guarantee user isolation."""
    options = ClientOptions(
        httpx_client=httpx.Client(timeout=60.0)
    )
    return create_client(supabase_url, supabase_key, options=options)

@st.cache_data
def get_kef_logo_base64() -> str:
    import base64
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, "assets", "kef_logo.png")
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

def is_authorized_email(email: str) -> bool:
    return True

def get_role_for_email(email: str) -> str:
    email = (email or "").lower().strip()

    reviewer_emails = [
        "rahilkk07@gmail.com",
        "rahilkko+07@gmail.com",
        "jayati.kapadia@kotakeducationfoundation.org",
        "tanvi.parulekar@kotakeducationfoundation.org",
        "karishma.agrawal@kotakeducationfoundation.org"
    ]

    if email in reviewer_emails:
        return "reviewer"

    return "creator"

def sync_user_to_db(email: str, name: str = None):
    db = SessionLocal()
    try:
        email_clean = (email or "").lower().strip()
        user = db.query(User).filter(User.email == email_clean).first()
        expected_role = get_role_for_email(email_clean)

        if not user:
            user = User(name=name or email_clean.split("@")[0], email=email_clean, role=expected_role)
            db.add(user)
            db.commit()
        else:
            # Strictly synchronize role with role policy (ensures creators are never mistakenly reviewers)
            if user.role != expected_role:
                user.role = expected_role
                db.commit()

        st.session_state.current_user_id = user.id
        st.session_state.current_user_role = user.role
        st.session_state.current_user_name = user.name
    finally:
        db.close()

def render_login_page():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_kef_logo_base64()
    if logo_b64:
        st.markdown(f"""
        <div style="text-align: center; margin-top: 35px; margin-bottom: 16px;">
            <img src="data:image/png;base64,{logo_b64}" alt="Kotak Education Foundation" style="max-width: 270px; width: 68%; height: auto;" />
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; margin-bottom: 22px;'>
        <h2 style='margin: 0; color: #0F172A; font-weight: 800; font-size: 24px; letter-spacing: -0.02em;'>Process Note Review Hub</h2>
        <p style='color: #64748B; font-size: 14px; margin-top: 5px; margin-bottom: 0;'>Institutional SOP Governance, Quality Validation & Managerial Sign-Off</p>
    </div>
    """, unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "Sign In"

    col1, col2, col3 = st.columns([1, 1.7, 1])
    with col2:
        # Segmented Tabs for Clean Switch Between Login & Registration
        tab_col1, tab_col2 = st.columns(2)
        with tab_col1:
            if st.button("🔑 Sign In", key="btn_nav_signin", type="primary" if st.session_state.auth_mode == "Sign In" else "secondary", use_container_width=True):
                st.session_state.auth_mode = "Sign In"
                st.rerun()
        with tab_col2:
            if st.button("✨ Create Account", key="btn_nav_signup", type="primary" if st.session_state.auth_mode == "Create Account" else "secondary", use_container_width=True):
                st.session_state.auth_mode = "Create Account"
                st.rerun()

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        # ---------------------------------------------
        # VIEW 1: SIGN IN
        # ---------------------------------------------
        if st.session_state.auth_mode == "Sign In":
            # Display prominent green message if user just completed registration
            if st.session_state.get("show_signup_success"):
                st.markdown("""
                <div style="background: #ECFDF5; border: 1.5px solid #10B981; border-radius: 9px; padding: 14px 18px; margin-bottom: 16px; color: #065F46; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.08);">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14.5px; margin-bottom: 4px;">
                        <span>🎉</span> Account Created Successfully!
                    </div>
                    <div style="font-size: 13.5px; line-height: 1.5; color: #047857;">
                        <b>You can now proceed with the login.</b> Please enter your password below to sign in to the platform.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with st.form("login_form"):
                prefill = st.session_state.get("just_signed_up_email", "")
                email = st.text_input("Work Email Address", value=prefill, placeholder="e.g. name@kotakeducationfoundation.org")
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                submit = st.form_submit_button("🚀 Sign In", type="primary", use_container_width=True)

                if submit:
                    clean_login_email = (email or "").strip().lower()
                    if not clean_login_email or not password:
                        st.error("Please enter both email address and password.")
                    elif not is_authorized_email(clean_login_email):
                        st.error("Unauthorized email domain. Access denied.")
                    else:
                        try:
                            # Clean user state before login without breaking Streamlit SessionInfo
                            for k in ["user", "current_user_id", "current_user_role", "current_user_name"]:
                                st.session_state.pop(k, None)

                            sb = get_supabase_client()
                            response = sb.auth.sign_in_with_password({"email": clean_login_email, "password": password})
                            st.session_state.user = response.user
                            sync_user_to_db(response.user.email)
                            st.session_state.pop("show_signup_success", None)
                            st.session_state.pop("just_signed_up_email", None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")

            # Helpful switch link
            st.markdown("""
            <div style="text-align: center; margin-top: 14px; font-size: 13px; color: #64748B;">
                Don't have an account yet?
            </div>
            """, unsafe_allow_html=True)
            if st.button("✨ Register / Create New Account", key="goto_signup_btn", use_container_width=True):
                st.session_state.auth_mode = "Create Account"
                st.rerun()

        # ---------------------------------------------
        # VIEW 2: CREATE ACCOUNT (SIGN UP)
        # ---------------------------------------------
        else:
            with st.form("signup_form"):
                st.markdown("""
                <div style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">
                    📝 Register New Team Member Account:
                </div>
                """, unsafe_allow_html=True)

                full_name = st.text_input("Full Name", placeholder="e.g. Priya Sharma")
                new_email = st.text_input("Work Email Address", placeholder="e.g. priya.sharma@kotakeducationfoundation.org")
                new_password = st.text_input("Create Password", type="password", placeholder="At least 6 characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")

                signup_submit = st.form_submit_button("✨ Register & Create Account", type="primary", use_container_width=True)

                if signup_submit:
                    clean_name = (full_name or "").strip()
                    clean_email = (new_email or "").strip().lower()
                    if not clean_email or not new_password:
                        st.error("Please enter both email address and password.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match. Please re-enter your password.")
                    elif not is_authorized_email(clean_email):
                        st.error("Unauthorized email domain. Access denied.")
                    else:
                        try:
                            sb = get_supabase_client()
                            response = sb.auth.sign_up({
                                "email": clean_email,
                                "password": new_password,
                                "options": {
                                    "emailRedirectTo": "http://localhost:8501/",
                                    "data": {
                                        "full_name": clean_name
                                    }
                                }
                            })

                            if response.user and getattr(response.user, 'identities', None) == []:
                                st.warning("ℹ️ This email is already registered! You can proceed with the login directly.")
                                st.session_state.just_signed_up_email = clean_email
                                st.session_state.auth_mode = "Sign In"
                                st.rerun()
                            else:
                                try:
                                    sync_user_to_db(clean_email, name=clean_name)
                                except Exception:
                                    pass

                                st.session_state.just_signed_up_email = clean_email
                                st.session_state.show_signup_success = True
                                st.session_state.auth_mode = "Sign In"
                                st.rerun()
                        except Exception as e:
                            err_msg = str(e)
                            if "already registered" in err_msg.lower():
                                st.warning("ℹ️ This email is already registered! You can proceed with the login directly.")
                                st.session_state.just_signed_up_email = clean_email
                                st.session_state.auth_mode = "Sign In"
                                st.rerun()
                            else:
                                st.error(f"Sign up failed: {err_msg}")

            # Helpful switch link
            st.markdown("""
            <div style="text-align: center; margin-top: 14px; font-size: 13px; color: #64748B;">
                Already have an account?
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔑 Proceed to Sign In", key="goto_signin_btn", use_container_width=True):
                st.session_state.auth_mode = "Sign In"
                st.rerun()

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is not None and "current_user_name" not in st.session_state:
        try:
            sync_user_to_db(st.session_state.user.email)
        except Exception:
            st.session_state.user = None

    if st.session_state.user is None:
        render_login_page()
        st.stop()

def logout():
    try:
        sb = get_supabase_client()
        sb.auth.sign_out()
    except Exception:
        pass

    # Reset app state safely without destroying Streamlit SessionInfo
    for k in list(st.session_state.keys()):
        if not k.startswith("_"):
            st.session_state.pop(k, None)
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()
