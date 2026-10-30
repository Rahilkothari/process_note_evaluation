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
            logo_b64 = get_kef_logo_base64()
            if logo_b64:
                st.markdown(f"""
                <div style="text-align: center; margin-bottom: 12px;">
                    <img src="data:image/png;base64,{logo_b64}" alt="Kotak Education Foundation" style="max-width: 175px; width: 85%; height: auto;" />
                </div>
                """, unsafe_allow_html=True)
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
            </style>
            """, unsafe_allow_html=True)
            
            logo_b64 = get_kef_logo_base64()
            if logo_b64:
                st.markdown(f"""
                <div style="text-align: center; margin-top: 36px; margin-bottom: 16px;">
                    <img src="data:image/png;base64,{logo_b64}" alt="Kotak Education Foundation" style="max-width: 290px; width: 80%; height: auto;" />
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<h2 style='text-align: center; margin-top: 0px; margin-bottom: 6px; color: #0F172A; font-weight: 700;'>Login Required</h2>", unsafe_allow_html=True)
            else:
                st.markdown("<h2 style='text-align: center; margin-top: 50px; color: #0F172A; font-weight: 700;'>Login Required</h2>", unsafe_allow_html=True)
            
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

                                login_container.empty()
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
