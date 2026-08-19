import streamlit as st
from models.database import get_db, ProcessNote, ValidationRun
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

st.set_page_config(page_title="Dashboard", layout="wide")
from core.ui_utils import inject_custom_css
from core.auth import require_login
inject_custom_css()
require_login()

st.title("Process Note Dashboard")

db: Session = next(get_db())

# Fetch metrics
total_notes = db.query(ProcessNote).count()
drafts = db.query(ProcessNote).filter(ProcessNote.status == "DRAFT").count()
needs_revision = db.query(ProcessNote).filter(ProcessNote.status == "NEEDS_REVISION").count()
under_review = db.query(ProcessNote).filter(ProcessNote.status == "UNDER_REVIEW").count()
approved = db.query(ProcessNote).filter(ProcessNote.status == "APPROVED").count()

avg_score = db.query(func.avg(ValidationRun.overall_score)).scalar() or 0.0

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Notes", total_notes)
    st.metric("Approved", approved)
with col2:
    st.metric("Drafts", drafts)
    st.metric("Needs Revision", needs_revision)
with col3:
    st.metric("Under Review", under_review)
    st.metric("Average Quality Score", f"{avg_score:.1f}%")

st.markdown("<br><hr><br>", unsafe_allow_html=True)
st.subheader("Recent Process Notes")

recent_notes = db.query(ProcessNote).order_by(ProcessNote.updated_at.desc()).limit(5).all()

if recent_notes:
    # Table Header
    hcol1, hcol2, hcol3, hcol4 = st.columns([3, 2, 2, 2])
    with hcol1: st.markdown("**Process Name**")
    with hcol2: st.markdown("**Team**")
    with hcol3: st.markdown("**Status**")
    with hcol4: st.markdown("**Last Updated**")
    st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)

    # Table Rows
    for note in recent_notes:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            if st.button(f"{note.process_name} (v{note.version})", key=f"btn_{note.id}", use_container_width=True):
                st.session_state.selected_note_id = note.id
                st.switch_page("pages/5_view_all_notes.py")
        with col2: 
            st.markdown(f"<div style='padding-top: 8px;'>{note.team}</div>", unsafe_allow_html=True)
        with col3: 
            st.markdown(f"<div style='padding-top: 8px;'>{note.status.replace('_', ' ')}</div>", unsafe_allow_html=True)
        with col4: 
            st.markdown(f"<div style='padding-top: 8px;'>{note.updated_at.strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.5em 0; border-color: #F1F5F9;'>", unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 48px; background-color: #FFFFFF; border-radius: 12px; border: 1px dashed #CBD5E1; margin-top: 24px;">
        <h3 style="color: #64748B; margin-bottom: 8px;">No Process Notes Found</h3>
        <p style="color: #94A3B8; font-size: 15px; margin-bottom: 24px;">It looks like your team hasn't created any process documentation yet.</p>
        <p style="color: #1E293B; font-weight: 500;">Navigate to <b>Create Process</b> in the sidebar to draft your first note.</p>
    </div>
    """, unsafe_allow_html=True)
