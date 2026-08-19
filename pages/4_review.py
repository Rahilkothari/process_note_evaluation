import streamlit as st
from models.database import get_db, ProcessNote, ValidationRun, ValidationFinding
from sqlalchemy.orm import Session
import pandas as pd
from services.export_service import ExportService

st.set_page_config(page_title="Review Process Notes", layout="wide")
from core.ui_utils import inject_custom_css
from core.auth import require_login
inject_custom_css()
require_login()

st.title("Reviewer Dashboard")

db: Session = next(get_db())

notes = db.query(ProcessNote).filter(ProcessNote.status.in_(["UNDER_REVIEW", "APPROVED"])).all()
if not notes:
    st.info("No process notes pending review.")
    st.stop()

note_options = {f"[{n.id}] {n.process_name} (v{n.version}) - {n.status.replace('_', ' ')}": n for n in notes}
selected = st.selectbox("Select Process Note", list(note_options.keys()))
current_note = note_options[selected]

status_class = "badge-review"
if current_note.status == "APPROVED": status_class = "badge-pass"
st.markdown(f"**Current Status:** <span class='badge {status_class}'>{current_note.status.replace('_', ' ')}</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Action", "AI Validation Findings", "Full Document Data"])

with tab1:
    if current_note.status == "UNDER_REVIEW":
        with st.form("review_form"):
            decision = st.radio("Decision", ["Approve", "Send Back for Revision"])
            comments = st.text_area("Reviewer Comments (Optional)")
            
            if st.form_submit_button("Submit Decision", type="primary"):
                if decision == "Approve":
                    current_note.status = "APPROVED"
                    st.success("Note has been approved!")
                else:
                    current_note.status = "NEEDS_REVISION"
                    st.warning("Note sent back for revision.")
                db.commit()
                st.rerun()
    elif current_note.status == "APPROVED":
        st.success("This Process Note has been approved.")
        if st.button("Export to Docx", type="primary"):
            filename = ExportService.export_to_docx(current_note)
            st.success(f"Generated {filename}")
            with open(filename, "rb") as f:
                st.download_button("Download Docx", f, file_name=filename)

with tab2:
    latest_run = db.query(ValidationRun).filter(ValidationRun.process_note_id == current_note.id).order_by(ValidationRun.timestamp.desc()).first()
    if latest_run:
        status_cls = "badge-pass" if latest_run.status == "PASS" else ("badge-warning" if latest_run.status == "WARNING" else "badge-fail")
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border-radius: 8px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 24px;">
            <div style="font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 600; color: #1E293B; margin-bottom: 8px;">AI Validation Summary</div>
            <div style="display: flex; gap: 24px;">
                <div><span style="color: #64748B; font-size: 13px; font-weight: 500;">Status:</span> <span class='badge {status_cls}'>{latest_run.status}</span></div>
                <div><span style="color: #64748B; font-size: 13px; font-weight: 500;">Score:</span> <span style="font-family: 'JetBrains Mono', monospace; font-weight: 600;">{latest_run.overall_score:.1f}%</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        findings = db.query(ValidationFinding).filter(ValidationFinding.validation_id == latest_run.id).all()
        for f in findings:
            if f.issue:
                with st.expander(f"{f.section_id if f.section_id else 'Cross-Section'} - {f.status}"):
                    st.write(f.issue)
    else:
        st.write("No AI Validation run found.")

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Process:** {current_note.process_name}")
        st.write(f"**Team:** {current_note.team}")
        st.write(f"**Version:** {current_note.version}")
        st.write(f"**Effective Date:** {current_note.effective_date}")
        st.write(f"**Next Review:** {current_note.next_review_date}")
    with col2:
        st.write(f"**Owner:** {current_note.process_owner}")
        st.write(f"**SME:** {current_note.subject_matter_expert}")
        st.write(f"**Champion:** {current_note.process_champion}")
        st.write(f"**Reviewer:** {current_note.process_reviewer}")
        st.write(f"**Approver:** {current_note.process_approver}")
        
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.subheader("Process Details")
    
    if not current_note.sections:
        st.info("No sections have been filled for this process note yet, showing blank template.")
        
    import yaml
    try:
        with open("config/sections.yaml", "r") as f:
            sections_config = yaml.safe_load(f).get("sections", [])
    except Exception:
        sections_config = []

    filled_sections = {s.section_id: s for s in current_note.sections}

    for sec_def in sections_config:
        sec_id = sec_def.get("id")
        sec_name = sec_def.get("name")
        st.markdown(f"#### Section {sec_id}: {sec_name}")
        
        if sec_id in filled_sections:
            s = filled_sections[sec_id]
            if s.content:
                st.write(s.content)
            elif s.structured_data:
                df = pd.DataFrame(s.structured_data)
                df.index = df.index + 1
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Section saved but empty.")
        else:
            st.info("Not filled.")
        st.markdown("<br>", unsafe_allow_html=True)
