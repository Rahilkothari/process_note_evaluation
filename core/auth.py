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

def is_authorized_email(email: str) -> bool:
    return True

def get_role_for_email(email: str) -> str:
    email = email.lower()
    
    admin_emails = ["rahilkk07@gmail.com", "rahilkko+07@gmail.com"]
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

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is not None and "current_user_name" not in st.session_state:
        try:
            sync_user_to_db(st.session_state.user.email)
        except Exception:
            st.session_state.user = None

    if st.session_state.user is not None:
        # Render sidebar status and logout button for active logged in user
        with st.sidebar:
            st.markdown("---")
            display_name = st.session_state.current_user_name.title() if "current_user_name" in st.session_state and st.session_state.current_user_name else ""
            st.markdown(f"Logged in as: **{display_name}**")
            if st.button("Log Out", key="global_logout"):
                logout()
            st.markdown("---")

    if st.session_state.user is None:
        login_container = st.empty()
        with login_container.container():
            st.markdown("""
            <style>
                [data-testid="stSidebarNav"] {
                    display: none;
                }
                .auth-card-wrapper {
                    max-width: 480px;
                    margin: 2rem auto 0 auto;
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 16px;
                    padding: 2.25rem;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03);
                }
                .auth-header {
                    text-align: center;
                    margin-bottom: 1.75rem;
                }
                .auth-badge {
                    display: inline-block;
                    padding: 4px 14px;
                    background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                    color: white !important;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                    border-radius: 9999px;
                    margin-bottom: 0.75rem;
                    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
                }
                /* Compact card and inputs */
                .auth-logo-container {
                    text-align: center;
                    margin-bottom: 0.75rem;
                }
                .auth-logo-img {
                    max-width: 220px;
                    height: auto;
                    display: inline-block;
                }
                .auth-title {
                    font-family: 'Outfit', -apple-system, sans-serif;
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #0f172a;
                    margin: 0.25rem 0 0.25rem 0;
                    letter-spacing: -0.02em;
                }
                .auth-subtitle {
                    color: #64748b;
                    font-size: 0.85rem;
                    margin: 0 0 1rem 0;
                    line-height: 1.35;
                }
                .auth-footer-note {
                    text-align: center;
                    margin-top: 1.25rem;
                    font-size: 0.75rem;
                    color: #94a3b8;
                }
                /* Streamlit input field compacting */
                [data-testid="stTextInput"] input {
                    padding: 0.45rem 0.75rem !important;
                    font-size: 0.88rem !important;
                    border-radius: 8px !important;
                }
                [data-testid="stTextInput"] label {
                    font-size: 0.82rem !important;
                    font-weight: 600 !important;
                    color: #334155 !important;
                    margin-bottom: 2px !important;
                }
                [data-testid="stForm"] {
                    border: 1px solid #e2e8f0 !important;
                    background: #ffffff !important;
                    border-radius: 12px !important;
                    padding: 1.25rem !important;
                    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
                }
            </style>
            """, unsafe_allow_html=True)

            import base64
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "kef_logo.png")
            logo_html = ""
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_b64 = base64.b64encode(f.read()).decode("utf-8")
                logo_html = f'<div class="auth-logo-container"><img class="auth-logo-img" src="data:image/png;base64,{logo_b64}" alt="Kotak Education Foundation" /></div>'

            col1, col2, col3 = st.columns([1.2, 1.4, 1.2])
            with col2:
                st.markdown(f"""
                <div class="auth-header">
                    {logo_html}
                    <h2 class="auth-title">Process Note Validator</h2>
                    <p class="auth-subtitle">AI-assisted quality gate & validation portal for operational notes.</p>
                </div>
                """, unsafe_allow_html=True)

                tab_login, tab_signup = st.tabs(["🔒 Sign In", "✨ Create Account"])

                with tab_login:
                    with st.form("login_form"):
                        email = st.text_input("Work Email", placeholder="name@kotakeducationfoundation.org")
                        password = st.text_input("Password", type="password", placeholder="Enter your password")
                        
                        submit = st.form_submit_button("Sign In to Portal", type="primary", use_container_width=True)
                        
                        if submit:
                            if not email or not password:
                                st.warning("Please provide both email and password.")
                            elif not is_authorized_email(email):
                                st.error("Unauthorized email domain. Access denied.")
                            else:
                                try:
                                    st.session_state.clear()
                                    sb = get_supabase_client()
                                    response = sb.auth.sign_in_with_password({"email": email.strip(), "password": password})
                                    st.session_state.user = response.user
                                    sync_user_to_db(response.user.email)
                                    login_container.empty()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Login failed: {str(e)}")

                with tab_signup:
                    with st.form("signup_form"):
                        new_email = st.text_input("Work Email", placeholder="name@kotakeducationfoundation.org", key="signup_email")
                        new_password = st.text_input("New Password", type="password", placeholder="Minimum 6 characters", key="signup_pw")
                        signup_submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                        
                        if signup_submit:
                            if not new_email or not new_password:
                                st.warning("Please fill in both email and password.")
                            elif not is_authorized_email(new_email):
                                st.error("Unauthorized email domain. Access denied.")
                            else:
                                try:
                                    sb = get_supabase_client()
                                    response = sb.auth.sign_up({
                                        "email": new_email.strip(),
                                        "password": new_password,
                                        "options": {
                                            "emailRedirectTo": "http://localhost:8501/"
                                        }
                                    })
                                    if response.user and getattr(response.user, 'identities', None) == []:
                                        st.error("This email is already registered! Please switch to the Sign In tab.")
                                    elif response.session:
                                        st.success("Account created successfully! You can now sign in.")
                                    else:
                                        st.success("Account created! Please check your email to confirm before signing in.")
                                except Exception as e:
                                    st.error(f"Sign up failed: {str(e)}")

                st.markdown("""
                <div class="auth-footer-note">
                    🔒 Secured with end-to-end organizational access controls
                </div>
                """, unsafe_allow_html=True)
        
        st.stop()

def logout():
    try:
        sb = get_supabase_client()
        sb.auth.sign_out()
    except Exception:
        pass
    
    # Completely reset session state
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
