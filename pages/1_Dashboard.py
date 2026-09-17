import streamlit as st
from models.database import get_db, ProcessNote, ValidationRun
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd


from core.ui_utils import inject_custom_css
from core.ui_utils import inject_custom_css


st.title("Process Note Dashboard")

db: Session = next(get_db())

current_role = st.session_state.get("current_user_role", "creator")
current_user_id = st.session_state.get("current_user_id")

@st.cache_data(ttl=60)
def get_dashboard_stats(_db: Session, current_role: str, current_user_id: int):
    if current_role == "admin":
        base_query = _db.query(ProcessNote)
    elif current_role == "reviewer":
        base_query = _db.query(ProcessNote).filter(ProcessNote.status.in_(["UNDER_REVIEW", "APPROVED"]))
    else:
        base_query = _db.query(ProcessNote).filter(ProcessNote.created_by == current_user_id)

    total_notes = base_query.count()
    drafts = base_query.filter(ProcessNote.status == "DRAFT").count()
    needs_revision = base_query.filter(ProcessNote.status == "NEEDS_REVISION").count()
    under_review = base_query.filter(ProcessNote.status == "UNDER_REVIEW").count()
    approved = base_query.filter(ProcessNote.status == "APPROVED").count()

    avg_query = _db.query(func.avg(ValidationRun.overall_score)).join(ProcessNote, ValidationRun.process_note_id == ProcessNote.id)
    if current_role == "admin":
        pass
    elif current_role == "reviewer":
        avg_query = avg_query.filter(ProcessNote.status.in_(["UNDER_REVIEW", "APPROVED"]))
    else:
        avg_query = avg_query.filter(ProcessNote.created_by == current_user_id)
    avg_score = avg_query.scalar() or 0.0
    
    return total_notes, drafts, needs_revision, under_review, approved, avg_score

@st.cache_data(ttl=60)
def get_dashboard_notes(_db: Session, current_role: str, current_user_id: int, status_filter: str):
    if current_role == "admin":
        base_query = _db.query(ProcessNote.id, ProcessNote.process_name, ProcessNote.version, ProcessNote.team, ProcessNote.status, ProcessNote.updated_at)
    elif current_role == "reviewer":
        base_query = _db.query(ProcessNote.id, ProcessNote.process_name, ProcessNote.version, ProcessNote.team, ProcessNote.status, ProcessNote.updated_at).filter(ProcessNote.status.in_(["UNDER_REVIEW", "APPROVED"]))
    else:
        base_query = _db.query(ProcessNote.id, ProcessNote.process_name, ProcessNote.version, ProcessNote.team, ProcessNote.status, ProcessNote.updated_at).filter(ProcessNote.created_by == current_user_id)
        
    if status_filter != "All":
        base_query = base_query.filter(ProcessNote.status == status_filter)
        
    notes = base_query.order_by(ProcessNote.updated_at.desc()).all()
    return [{"id": n.id, "process_name": n.process_name, "version": n.version, "team": n.team, "status": n.status, "updated_at": n.updated_at} for n in notes]

@st.cache_data(ttl=60)
def get_dashboard_users(_db: Session):
    from models.database import User
    users = _db.query(User.id, User.email, User.role).all()
    return [{"id": u.id, "email": u.email, "role": u.role} for u in users]

total_notes, drafts, needs_revision, under_review, approved, avg_score = get_dashboard_stats(db, current_role, current_user_id)

query_status = st.query_params.get("status", "All")
status_options = ["All", "DRAFT", "UNDER_REVIEW", "APPROVED", "NEEDS_REVISION"]
if current_role == "reviewer":
    status_options = ["All", "UNDER_REVIEW", "APPROVED"]

default_idx = status_options.index(query_status) if query_status in status_options else 0

st.markdown("<br>", unsafe_allow_html=True)

def clickable_metric(title, value, status):
    import urllib.parse
    params = dict(st.query_params)
    params["status"] = status
    query_string = urllib.parse.urlencode(params)
    url = f"/?{query_string}"
    
    html = f"""
    <a href="{url}" target="_self" style="text-decoration: none; color: inherit; display: block;">
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px 24px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02); display: flex; flex-direction: column; justify-content: center; cursor: pointer; transition: all 0.2s ease;" onmouseover="this.style.borderColor='#4F46E5'; this.style.boxShadow='0 10px 15px -3px rgba(0, 0, 0, 0.08)';" onmouseout="this.style.borderColor='#E2E8F0'; this.style.boxShadow='0 4px 6px -1px rgba(0, 0, 0, 0.02)';">
            <div style="color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Inter', sans-serif;">{title}</div>
            <div style="color: #0F172A; font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 32px; margin-top: 4px;">{value}</div>
        </div>
    </a>
    """
    st.markdown(html, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    clickable_metric("Total Notes", total_notes, "All")
    st.markdown("<br>", unsafe_allow_html=True)
    clickable_metric("Approved", approved, "APPROVED")
with col2:
    if current_role == "creator":
        clickable_metric("Drafts", drafts, "DRAFT")
        st.markdown("<br>", unsafe_allow_html=True)
        clickable_metric("Needs Revision", needs_revision, "NEEDS_REVISION")
with col3:
    clickable_metric("Under Review", under_review, "UNDER_REVIEW")
    st.markdown("<br>", unsafe_allow_html=True)
    clickable_metric("Average Quality Score", f"{avg_score:.1f}%", "All")

st.markdown("<br><hr><br>", unsafe_allow_html=True)
col_title, col_filter = st.columns([1, 1])
with col_title:
    st.subheader("Process Notes")
with col_filter:
    status_filter = st.selectbox("Filter by Status", status_options, index=default_idx, label_visibility="collapsed")

recent_notes = get_dashboard_notes(db, current_role, current_user_id, status_filter)

if recent_notes:
    hcol1, hcol2, hcol3, hcol4 = st.columns([3, 2, 2, 2])
    with hcol1: st.markdown("**Process Name**")
    with hcol2: st.markdown("**Team**")
    with hcol3: st.markdown("**Status**")
    with hcol4: st.markdown("**Last Updated**")
    st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)

    for note in recent_notes:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            if st.button(f"{note['process_name']} (v{note['version']})", key=f"btn_{note['id']}", use_container_width=True):
                st.session_state.selected_note_id = note['id']
                if current_role == "creator" and note['status'] in ["DRAFT", "NEEDS_REVISION"]:
                    st.switch_page("pages/3_Validation.py")
                elif current_role in ["reviewer", "admin"] and note['status'] == "UNDER_REVIEW":
                    st.switch_page("pages/4_Review.py")
                else:
                    st.switch_page("pages/5_View_All_Notes.py")
        with col2: 
            st.markdown(f"<div style='padding-top: 8px;'>{note['team']}</div>", unsafe_allow_html=True)
        with col3: 
            st.markdown(f"<div style='padding-top: 8px;'>{note['status'].replace('_', ' ')}</div>", unsafe_allow_html=True)
        with col4: 
            st.markdown(f"<div style='padding-top: 8px;'>{note['updated_at'].strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.5em 0; border-color: #F1F5F9;'>", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="text-align: center; padding: 48px; background-color: #FFFFFF; border-radius: 12px; border: 1px dashed #CBD5E1; margin-top: 24px;">
        <h3 style="color: #64748B; margin-bottom: 8px;">No Process Notes Found</h3>
        <p style="color: #94A3B8; font-size: 15px; margin-bottom: 24px;">No process notes match the selected filter ({status_filter}).</p>
    </div>
    """, unsafe_allow_html=True)

if current_role == "admin":
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.subheader("Admin: User Management")
    from models.database import User
    users_meta = get_dashboard_users(db)
    user_options = {f"{u['email']} ({u['role']})": u['id'] for u in users_meta}
    selected_user_key = st.selectbox("Select User", list(user_options.keys()))
    new_role = st.selectbox("New Role", ["creator", "reviewer", "admin"])
    if st.button("Update Role"):
        target_user = db.query(User).filter(User.id == user_options[selected_user_key]).first()
        if target_user:
            target_user.role = new_role
            db.commit()
            st.cache_data.clear()
            st.success(f"Updated {target_user.email} to {new_role}")
