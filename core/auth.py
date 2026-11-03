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

    if role == "ADMIN":
        role_bg = "#ECFDF5"
        role_color = "#065F46"
        role_border = "#A7F3D0"
        avatar_bg = "linear-gradient(135deg, #059669 0%, #047857 100%)"
        avatar_shadow = "rgba(4, 120, 87, 0.25)"
    elif role == "REVIEWER":
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
    email = email.lower()
    
    admin_emails = ["rahilkk07@gmail.com", "rahilkko+07@gmail.com", "rahilkothari99@gmail.com"]
    reviewer_emails = [
        "jayati.kapadia@kotakeducationfoundation.org", 
        "tanvi.parulekar@kotakeducationfoundation.org",
        "karishma.agrawal@kotakeducationfoundation.org",
        "gopi.naik@kotakeducationfoundation.org"
    ]
    
    if email in admin_emails:
        return "admin"
    elif email in reviewer_emails:
        return "reviewer"
        
    return "creator"

def sync_user_to_db(email: str, name: str = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            role = get_role_for_email(email)
            user = User(name=name or email.split("@")[0], email=email, role=role)
            db.add(user)
            db.commit()
        else:
            expected_role = get_role_for_email(email)
            if expected_role == "admin" and user.role != "admin":
                user.role = "admin"
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
        <div style="text-align: center; margin-top: 45px; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_b64}" alt="Kotak Education Foundation" style="max-width: 290px; width: 75%; height: auto;" />
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; margin-top: 0px; margin-bottom: 6px; color: #0F172A; font-weight: 700;'>Login Required</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 14.5px; margin-top: 0; margin-bottom: 24px;'>Please sign in to access the Process Note Validator.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            
            if submit:
                if not is_authorized_email(email):
                    st.error("Unauthorized email domain. Access denied.")
                else:
                    try:
                        # Clean user state before login without breaking Streamlit SessionInfo
                        for k in ["user", "current_user_id", "current_user_role", "current_user_name"]:
                            st.session_state.pop(k, None)

                        sb = get_supabase_client()
                        response = sb.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = response.user
                        sync_user_to_db(response.user.email)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
                        
        with st.expander("Need an account? Sign Up"):
            with st.form("signup_form"):
                new_email = st.text_input("Email Address")
                new_password = st.text_input("Password", type="password")
                signup_submit = st.form_submit_button("Sign Up", type="secondary", use_container_width=True)
                
                if signup_submit:
                    if not is_authorized_email(new_email):
                        st.error("Unauthorized email domain. Access denied.")
                    else:
                        try:
                            sb = get_supabase_client()
                            response = sb.auth.sign_up({
                                "email": new_email,
                                "password": new_password,
                                "options": {
                                    "emailRedirectTo": "http://localhost:8501/"
                                }
                            })
                            if response.user and getattr(response.user, 'identities', None) == []:
                                st.error("This email is already registered! Please check your inbox for a previous confirmation email or try logging in.")
                            elif response.session:
                                st.success("Account created successfully! You can now log in immediately.")
                            else:
                                st.success("Account created successfully! Please check your email and click the confirmation link before logging in.")
                        except Exception as e:
                            st.error(f"Sign up failed: {str(e)}")

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
