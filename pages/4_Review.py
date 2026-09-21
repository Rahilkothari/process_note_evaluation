import streamlit as st
from models.database import SessionLocal, get_db, ProcessNote, ValidationRun, ValidationFinding
from sqlalchemy.orm import Session
import pandas as pd
from services.export_service import generate_docx


from core.ui_utils import inject_custom_css
from core.ui_utils import inject_custom_css


user_email = st.session_state.user.email if st.session_state.get("user") else ""
if st.session_state.get("current_user_role") not in ["admin", "reviewer"] and user_email not in ["rahilkk07@gmail.com", "rahilkko+07@gmail.com"]:
    st.error("Access Denied: You do not have the required permissions to access the Reviewer Dashboard. This page is restricted to Reviewers and Admins.")
    st.stop()

st.title("Reviewer Dashboard")

db: Session = SessionLocal()

filter_status = st.radio("View Notes", ["Pending Review", "Approved"], horizontal=True)
status_to_fetch = "UNDER_REVIEW" if filter_status == "Pending Review" else "APPROVED"

@st.cache_data(ttl=60)
def get_review_notes_metadata(_db: Session, status: str):
    notes = _db.query(ProcessNote.id, ProcessNote.process_name, ProcessNote.version, ProcessNote.status).filter(ProcessNote.status == status).all()
    return [{"id": n.id, "process_name": n.process_name, "version": n.version, "status": n.status} for n in notes]

notes_meta = get_review_notes_metadata(db, status_to_fetch)
if not notes_meta:
    st.info(f"No process notes found for: {filter_status}.")
    st.stop()

note_options = {f"[{n['id']}] {n['process_name']} (v{n['version']}) - {n['status'].replace('_', ' ')}": n['id'] for n in notes_meta}
default_idx = 0
if "selected_note_id" in st.session_state:
    for i, key in enumerate(note_options.keys()):
        if note_options[key] == st.session_state.selected_note_id:
            default_idx = i
            break

selected = st.selectbox("Select Process Note", list(note_options.keys()), index=default_idx)
selected_id = note_options[selected]
current_note = db.query(ProcessNote).filter(ProcessNote.id == selected_id).first()

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
                from models.database import ReviewHistory
                
                if decision == "Approve":
                    current_note.status = "APPROVED"
                    st.success("Note has been approved!")
                    action_val = "APPROVED"
                    
                    # Background RAG ingestion
                    def ingest_rag_background(note_id, team, sections_data):
                        from services.rag_service import rag_service
                        for sec_id, content in sections_data:
                            try:
                                rag_service.ingest_section(
                                    note_id=note_id,
                                    team=team,
                                    section_id=sec_id,
                                    content=content
                                )
                            except Exception as e:
                                print(f"Failed to ingest section {sec_id} into RAG: {e}")
                    
                    import threading
                    import json
                    sections_to_ingest = []
                    for section in current_note.sections:
                        content_to_ingest = section.content
                        if not content_to_ingest and section.structured_data:
                            content_to_ingest = json.dumps(section.structured_data)
                        if content_to_ingest and content_to_ingest != "[]":
                            sections_to_ingest.append((section.section_id, content_to_ingest))
                            
                    threading.Thread(target=ingest_rag_background, args=(current_note.id, current_note.team, sections_to_ingest)).start()
                    
                    # Clear reviewer comments from structured data upon approval
                    from sqlalchemy.orm.attributes import flag_modified
                    for section in current_note.sections:
                        if section.structured_data:
                            modified = False
                            for row in section.structured_data:
                                if "Reviewer Comment" in row:
                                    del row["Reviewer Comment"]
                                    modified = True
                            if modified:
                                flag_modified(section, "structured_data")
                                
                else:
                    import uuid
                    from models.database import ProcessSection
                    import copy
                    
                    if not current_note.document_id:
                        current_note.document_id = str(uuid.uuid4())
                        
                    current_note.status = "ARCHIVED"
                    
                    try:
                        v_num = float(current_note.version)
                        new_version = f"{v_num + 0.1:.1f}"
                    except:
                        new_version = current_note.version + "_revised"
                        
                    new_note = ProcessNote(
                        document_id=current_note.document_id,
                        process_name=current_note.process_name,
                        team=current_note.team,
                        version=new_version,
                        status="NEEDS_REVISION",
                        subject_matter_expert=current_note.subject_matter_expert,
                        process_owner=current_note.process_owner,
                        process_champion=current_note.process_champion,
                        process_reviewer=current_note.process_reviewer,
                        process_approver=current_note.process_approver,
                        effective_date=current_note.effective_date,
                        next_review_date=current_note.next_review_date,
                        created_by=current_note.created_by
                    )
                    
                    new_sections = []
                    for section in current_note.sections:
                        new_section = ProcessSection(
                            process_name=new_note.process_name,
                            section_id=section.section_id,
                            content=section.content,
                            structured_data=copy.deepcopy(section.structured_data) if section.structured_data else None
                        )
                        new_sections.append(new_section)
                    
                    new_note.sections = new_sections
                    db.add(new_note)
                        
                    st.warning(f"Note sent back for revision. A new draft (v{new_version}) was created.")
                    action_val = "SENT_BACK"
                    note_for_history = current_note
                    current_note = new_note
                
                reviewer_name = st.session_state.get("current_user_name", "Unknown Reviewer")
                review = ReviewHistory(
                    process_note_id=note_for_history.id if action_val == "SENT_BACK" else current_note.id,
                    process_name=current_note.process_name,
                    reviewer=reviewer_name,
                    action=action_val,
                    comments=comments
                )
                db.add(review)
                db.commit()
                
                # Notify creator
                from core.notifications import create_notification
                if current_note.created_by:
                    msg = f"Reviewer {reviewer_name} has {action_val.replace('_', ' ').lower()} your note '{current_note.process_name}'."
                    create_notification(db, current_note.created_by, msg, current_note.id)
                
                st.cache_data.clear()
                st.rerun()
    elif current_note.status == "APPROVED":
        st.success("This Process Note has been approved.")
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            file_stream = generate_docx(current_note)
            filename = f"Process_Note_{current_note.id}.docx"
            st.download_button("Export to Docx", file_stream, file_name=filename, type="primary", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col_btn2:
            if st.button("Revert Approval", type="secondary"):
                from models.database import ReviewHistory
                current_note.status = "UNDER_REVIEW"
                
                reviewer_name = st.session_state.get("current_user_name", "Unknown Reviewer")
                review = ReviewHistory(
                    process_note_id=current_note.id,
                    process_name=current_note.process_name,
                    reviewer=reviewer_name,
                    action="REVERTED_APPROVAL",
                    comments="Approval reverted by reviewer."
                )
                db.add(review)
                db.commit()
                st.rerun()

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
        
        import yaml
        try:
            with open("config/sections.yaml", "r") as f_yaml:
                sections_config = yaml.safe_load(f_yaml).get("sections", [])
        except Exception:
            sections_config = []

        findings = db.query(ValidationFinding).filter(ValidationFinding.validation_id == latest_run.id).all()
        for f in findings:
            if f.issue:
                is_manual = "*(Marked as OK by User)*" in (f.issue or "")
                display_issue = (f.issue or "").replace("*(Marked as OK by User)*\n\n", "").replace("*(Marked as OK by User)*", "")
                
                expander_status = f"{f.status} (Marked as OK by User)" if is_manual else f.status
                
                with st.expander(f"{f.section_id if f.section_id else 'Cross-Section'} - {expander_status}"):
                    st.markdown("**AI Finding:**")
                    st.write(display_issue.strip())
                    
                    if f.section_id:
                        st.markdown("---")
                        st.markdown(f"**Section Data ({f.section_id}):**")
                        
                        sec_def = next((s for s in sections_config if str(s.get("id")) == str(f.section_id) or str(s.get("name")) == str(f.section_id)), None)
                        true_section_id = sec_def.get("id") if sec_def else f.section_id
                        
                        section = next((s for s in current_note.sections if str(s.section_id) == str(true_section_id)), None)
                        
                        if section:
                            if section.content:
                                st.info(section.content)
                            elif section.structured_data:
                                import pandas as pd
                                df = pd.DataFrame(section.structured_data)
                                if "Reviewer Comment" not in df.columns:
                                    df["Reviewer Comment"] = ""
                                
                                disabled_cols = [c for c in df.columns if c != "Reviewer Comment"]
                                
                                edited_df = st.data_editor(
                                    df, 
                                    use_container_width=True,
                                    hide_index=True,
                                    disabled=disabled_cols,
                                    key=f"editor_tab2_{true_section_id}_{current_note.id}_{f.id}"
                                )
                                
                                edited_df = edited_df.fillna("")
                                new_data = edited_df.to_dict("records")
                                
                                if new_data != section.structured_data:
                                    section.structured_data = new_data
                                    from sqlalchemy.orm.attributes import flag_modified
                                    flag_modified(section, "structured_data")
                                    db.commit()
                            else:
                                st.write("*(Empty Section)*")
                        else:
                            st.write("*(Section not found or not filled)*")
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
                if "Reviewer Comment" not in df.columns:
                    df["Reviewer Comment"] = ""
                
                disabled_cols = [c for c in df.columns if c != "Reviewer Comment"]
                
                edited_df = st.data_editor(
                    df, 
                    use_container_width=True,
                    disabled=disabled_cols,
                    key=f"editor_{sec_id}_{current_note.id}"
                )
                
                edited_df = edited_df.fillna("")
                new_data = edited_df.to_dict("records")
                
                # Save changes automatically if modified
                if new_data != s.structured_data:
                    s.structured_data = new_data
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(s, "structured_data")
                    db.commit()
            else:
                st.info("Section saved but empty.")
        else:
            st.info("Not filled.")
        st.markdown("<br>", unsafe_allow_html=True)
