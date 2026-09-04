import os
import streamlit as st
from supabase import create_client, Client
from models.database import get_db, User
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

from supabase.client import ClientOptions
import httpx

@st.cache_resource
def init_supabase() -> Client:
    options = ClientOptions(
        httpx_client=httpx.Client(timeout=60.0)
    )
    return create_client(supabase_url, supabase_key, options=options)

supabase: Client = init_supabase()

def is_authorized_email(email: str) -> bool:
    return True

def get_role_for_email(email: str) -> str:
    email = email.lower()
    if email == "rahillkk07@gmail.com":
        return "admin"
    # Default roles
    return "creator"

def sync_user_to_db(email: str, name: str = None, requested_role: str = None):
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        role = requested_role if requested_role else get_role_for_email(email)
        user = User(name=name or email.split("@")[0], email=email, role=role)
        db.add(user)
        db.commit()
    elif requested_role and user.role != requested_role:
        # Update role for MVP demo purposes
        user.role = requested_role
        db.commit()
    
    st.session_state.current_user_id = user.id
    st.session_state.current_user_role = user.role
    st.session_state.current_user_name = user.name

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    # Auto-login workaround for page refreshes
    if st.session_state.user is None and "session_email" in st.query_params:
        cached_email = st.query_params["session_email"]
        if is_authorized_email(cached_email):
            class MockUser:
                def __init__(self, e):
                    self.email = e
            st.session_state.user = MockUser(cached_email)

    if st.session_state.user is not None and "current_user_name" not in st.session_state:
        try:
            sync_user_to_db(st.session_state.user.email)
        except Exception:
            st.session_state.user = None

    if st.session_state.user is not None:
        # Render the logout button on the sidebar for EVERY page
        with st.sidebar:
            st.markdown("---")
            display_name = st.session_state.current_user_name.title() if "current_user_name" in st.session_state and st.session_state.current_user_name else ""
            st.markdown(f"Logged in as: **{display_name}**")
            if st.button("Log Out", key="global_logout"):
                logout()
            st.markdown("---")

    if st.session_state.user is None:
        st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; margin-top: 50px;'>Login Required</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B;'>Please sign in to access the Process Note Validator.</p>", unsafe_allow_html=True)
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("login_form"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    login_role = st.selectbox("Log in as", ["Normal User", "Reviewer"], help="Select your role for this session.")
                    
                    submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                    
                    if submit:
                        if not is_authorized_email(email):
                            st.error("Unauthorized email domain. Access denied.")
                        else:
                            try:
                                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                                st.session_state.user = response.user
                                st.query_params["session_email"] = response.user.email
                                db_role = "admin" if login_role == "Reviewer" else "creator"
                                sync_user_to_db(response.user.email, requested_role=db_role)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Login failed: {str(e)}")
                                
                with st.expander("Need an account? Sign Up"):
                    with st.form("signup_form"):
                        new_email = st.text_input("New Email")
                        new_password = st.text_input("New Password", type="password")
                        signup_submit = st.form_submit_button("Sign Up", type="secondary", use_container_width=True)
                        
                        if signup_submit:
                            if not is_authorized_email(new_email):
                                st.error("Unauthorized email domain. Access denied.")
                            else:
                                try:
                                    response = supabase.auth.sign_up({"email": new_email, "password": new_password})
                                    st.success("Account created successfully! You can now log in.")
                                except Exception as e:
                                    st.error(f"Sign up failed: {str(e)}")
        
        st.stop() # Halts execution of the rest of the app until logged in

def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    if "current_user_id" in st.session_state:
        del st.session_state.current_user_id
    st.query_params.clear()
    st.rerun()
