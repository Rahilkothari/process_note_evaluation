import os
import streamlit as st
from supabase import create_client, Client
from models.database import get_db, User
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(supabase_url, supabase_key)

supabase: Client = init_supabase()

def is_authorized_email(email: str) -> bool:
    email = email.lower()
    if email.endswith("@kotakeducationfoundation.org") or email.endswith("@gmail.com"):
        return True
    if email in ["rahilkothari99@gmail.com", "rahillkk07@gmail.com"]:
        return True
    return False

def get_role_for_email(email: str) -> str:
    email = email.lower()
    if email == "rahillkk07@gmail.com":
        return "admin"
    # Default roles
    return "creator"

def sync_user_to_db(email: str, name: str = None):
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    role = get_role_for_email(email)
    
    if not user:
        user = User(name=name or email.split("@")[0], email=email, role=role)
        db.add(user)
        db.commit()
    elif user.role != role:
        # Update role if it changed (e.g. they became admin)
        user.role = role
        db.commit()
    
    st.session_state.current_user_id = user.id
    st.session_state.current_user_role = user.role
    st.session_state.current_user_name = user.name

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is not None and "current_user_name" not in st.session_state:
        try:
            sync_user_to_db(st.session_state.user.email)
        except Exception:
            st.session_state.user = None

    if st.session_state.user is None:
        st.markdown("<h2 style='text-align: center; margin-top: 50px;'>Login Required</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B;'>Please sign in to access the Process Note Validator.</p>", unsafe_allow_html=True)
        
        with st.container():
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
                                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                                st.session_state.user = response.user
                                sync_user_to_db(response.user.email)
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
    st.rerun()
