import streamlit as st
from models.database import get_db, ProcessNote, ValidationRun, ValidationFinding, ProcessSection, ReviewHistory
from models.schemas import ProcessNoteSchema, ProcessSectionSchema
from sqlalchemy.orm import Session
from core.validation_engine import ValidationEngine
import json
import os


from core.ui_utils import inject_custom_css
from core.ui_utils import inject_custom_css


st.title("Run AI Validation")

db: Session = next(get_db())
engine = ValidationEngine()

current_role = st.session_state.get("current_user_role", "creator")
current_user_id = st.session_state.get("current_user_id")

base_query = db.query(ProcessNote).filter(ProcessNote.status.in_(["DRAFT", "NEEDS_REVISION"]))
if current_role == "creator":
    notes = base_query.filter(ProcessNote.created_by == current_user_id).all()
else:
    notes = base_query.all()
note_options = {f"[{n.id}] {n.process_name} (v{n.version})": n for n in notes}

if not note_options:
    st.info("No draft process notes available for validation.")
    st.stop()

default_idx = 0
if "selected_note_id" in st.session_state:
    for i, key in enumerate(note_options.keys()):
        if note_options[key].id == st.session_state.selected_note_id:
            default_idx = i
            break

selected = st.selectbox("Select Process Note to Validate", list(note_options.keys()), index=default_idx)
current_note = note_options[selected]

status_class = "badge-draft"
if current_note.status == "PASS": status_class = "badge-pass"
elif current_note.status == "WARNING": status_class = "badge-warning"
elif current_note.status == "NEEDS_REVISION": status_class = "badge-fail"

st.markdown(f"**Current Status:** <span class='badge {status_class}'>{current_note.status.replace('_', ' ')}</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if current_note.status in ["NEEDS_REVISION", "APPROVED"]:
    latest_review = db.query(ReviewHistory).filter(ReviewHistory.process_note_id == current_note.id).order_by(ReviewHistory.timestamp.desc()).first()
    if latest_review and latest_review.comments:
        st.markdown(f"**Reviewer Comment ({latest_review.reviewer}):**")
        st.info(latest_review.comments)
        st.markdown("<br>", unsafe_allow_html=True)

import yaml
try:
    with open("config/sections.yaml", "r") as f:
        sections_config = yaml.safe_load(f).get("sections", [])
except Exception:
    sections_config = []

if st.button("Run AI Validation", type="primary"):
    with st.spinner("AI Evaluation in process..."):
        filled_sections = {s.section_id: s for s in current_note.sections}
        sections_payload = []
        
        for sec_def in sections_config:
            sec_id = sec_def.get("id")
            if sec_id in filled_sections:
                s = filled_sections[sec_id]
                sections_payload.append(ProcessSectionSchema(
                    section_id=s.section_id,
                    content=s.content,
                    structured_data=s.structured_data
                ))
            else:
                # Add empty section so rule validator catches it
                sections_payload.append(ProcessSectionSchema(
                    section_id=sec_id,
                    content="",
                    structured_data=[]
                ))
        
        payload = ProcessNoteSchema(
            process_name=current_note.process_name,
            team=current_note.team,
            version=current_note.version,
            sections=sections_payload
        )
        
        result = engine.run_validation(payload)
        
        v_run = ValidationRun(
            process_note_id=current_note.id,
            process_name=current_note.process_name,
            overall_score=result.overall_score,
            status=result.overall_status,
            model_used=os.getenv("LLM_MODEL", "gemini-3.5-flash")
        )
        db.add(v_run)
        db.commit()
        db.refresh(v_run)
        
        for sec_res in result.section_results:
            vf = ValidationFinding(
                validation_id=v_run.id,
                process_name=current_note.process_name,
                section_id=sec_res.section,
                severity=sec_res.severity,
                status=sec_res.status,
                score=sec_res.score,
                issue="\n".join(sec_res.issues),
                recommendation="\n".join(sec_res.recommendations),
                is_cross_section=0
            )
            db.add(vf)
            
        for cr in result.cross_section_issues:
            vf = ValidationFinding(
                validation_id=v_run.id,
                process_name=current_note.process_name,
                severity=cr.get("severity", "MEDIUM"),
                status="WARNING",
                issue=cr.get("issue", ""),
                is_cross_section=1
            )
            db.add(vf)
            
        current_note.status = result.overall_status
        db.commit()
        st.success("Validation Complete!")
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

latest_run = db.query(ValidationRun).filter(ValidationRun.process_note_id == current_note.id).order_by(ValidationRun.timestamp.desc()).first()

if latest_run:
    st.subheader(f"Latest Validation Results ({latest_run.timestamp.strftime('%Y-%m-%d %H:%M')})")
    
    status_class = "badge-pass" if latest_run.status == "PASS" else ("badge-warning" if latest_run.status == "WARNING" else "badge-fail")
    score_bar_class = "score-pass" if latest_run.status == "PASS" else ("score-warn" if latest_run.status == "WARNING" else "score-fail")
    
    st.markdown(f"""
    <div style="background-color: #FFFFFF; border-radius: 12px; padding: 24px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <div style="color: #64748B; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Overall Score</div>
                <div style="font-family: 'Outfit', sans-serif; font-size: 36px; font-weight: 700; color: #0F172A;">{latest_run.overall_score:.1f}%</div>
            </div>
            <div>
                <span class='badge {status_class}' style='font-size: 14px; padding: 8px 16px;'>{latest_run.status.replace('_', ' ')}</span>
            </div>
        </div>
        <div class="score-bar-container">
            <div class="score-bar-fill {score_bar_class}" style="width: {latest_run.overall_score}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    findings = db.query(ValidationFinding).filter(ValidationFinding.validation_id == latest_run.id).all()
    
    st.markdown("### Cross-Section Findings")
    cross_findings = [f for f in findings if f.is_cross_section == 1]
    if cross_findings:
        for f in cross_findings:
            st.warning(f"[{f.severity}] {f.issue}")
    else:
        st.success("No cross-section issues found.")
        
    st.markdown("### Section Findings")
    sec_findings = [f for f in findings if f.is_cross_section == 0]
    
    for f in sec_findings:
        is_manual = "*(Marked as OK by User)*" in (f.issue or "")
        display_issue = (f.issue or "").replace("*(Marked as OK by User)*\n\n", "").replace("*(Marked as OK by User)*", "")
        
        badge_cls = "badge-pass" if f.status == "PASS" else ("badge-warning" if f.status == "WARNING" else "badge-fail")
        badge_text = "PASS (Marked as OK)" if is_manual else f.status
        badge_html = f"<span class='badge {badge_cls}'>{badge_text}</span>"
        
        if is_manual:
            status_emoji = "✅ PASS (Marked as OK)"
        else:
            status_emoji = "✅ PASS" if f.status == "PASS" else ("⚠️ WARNING" if f.status == "WARNING" else "❌ NEEDS REVISION")
        
        with st.expander(f"{f.section_id} (Score: {f.score}) - {status_emoji}"):
            st.markdown(f"**Status:** {badge_html}", unsafe_allow_html=True)
            if display_issue.strip():
                st.markdown(f"**Issues ({f.severity}):**")
                st.write(display_issue.strip())
            if f.recommendation:
                st.markdown("**Recommendation:**")
                st.write(f.recommendation)
            if not display_issue.strip() and not f.recommendation:
                st.write("Section looks good.")
                
            if f.status != "PASS" and not is_manual:
                if st.button("Mark as OK (Ignore Feedback)", key=f"ignore_{f.id}"):
                    # Update this finding
                    f.status = "PASS"
                    f.severity = "LOW"
                    # Preserve original score, do not change to 100.0
                    f.issue = f"*(Marked as OK by User)*\n\n{f.issue}" if f.issue else "*(Marked as OK by User)*"
                    db.commit()
                    
                    # Recalculate overall run score and status
                    all_f = db.query(ValidationFinding).filter(ValidationFinding.validation_id == latest_run.id).all()
                    sec_f = [res for res in all_f if res.is_cross_section == 0]
                    
                    total_score = sum([res.score for res in sec_f])
                    num_sections = len(sec_f)
                    
                    if num_sections > 0:
                        latest_run.overall_score = round(total_score / num_sections, 1)
                        
                    critical_issues = sum([1 for res in all_f if res.severity == "HIGH"])
                    warnings = sum([1 for res in all_f if (res.severity == "MEDIUM" or res.status == "WARNING")])
                    sections_needing_revision = sum([1 for res in all_f if res.status == "NEEDS_REVISION"])
                    
                    pass_threshold = float(os.getenv("PASS_THRESHOLD", 80))
                    warning_threshold = float(os.getenv("WARNING_THRESHOLD", 70))
                    
                    if critical_issues > 0 or sections_needing_revision > 0 or latest_run.overall_score < warning_threshold:
                        latest_run.status = "NEEDS_REVISION"
                    elif latest_run.overall_score < pass_threshold or warnings > 0:
                        latest_run.status = "WARNING"
                    else:
                        latest_run.status = "PASS"
                        
                    current_note.status = latest_run.status
                    db.commit()
                    st.rerun()
            
            # Show manual reviewer comments if they exist
            # f.section_id from ValidationFinding might actually be the section name due to validation_engine logic.
            # Let's find the correct config first by checking both id and name.
            sec_def = next((s for s in sections_config if str(s.get("id")) == str(f.section_id) or str(s.get("name")) == str(f.section_id)), None)
            
            true_section_id = sec_def.get("id") if sec_def else f.section_id
            
            section = next((s for s in current_note.sections if str(s.section_id) == str(true_section_id)), None)
            if section and section.structured_data:
                import pandas as pd
                df = pd.DataFrame(section.structured_data)
                if "Reviewer Comment" in df.columns:
                    has_comments = False
                    for idx, row in df.iterrows():
                        comment = row.get("Reviewer Comment")
                        if comment and str(comment).strip():
                            if not has_comments:
                                st.markdown("---")
                                st.markdown("##### 👤 Manual Reviewer Feedback")
                                has_comments = True
                            
                            row_id = ""
                            if "Sr. No." in df.columns and pd.notna(row.get("Sr. No.")):
                                row_id = f"Row {row.get('Sr. No.')}"
                            elif len(df.columns) > 0:
                                first_col = df.columns[0]
                                row_id = f"{first_col}: {row.get(first_col, 'Item')}"
                            else:
                                row_id = f"Item {idx + 1}"
                                
                            st.info(f"**{row_id}**: {comment}")
            
            # Inline Editing UI
            st.markdown("---")
            st.markdown("##### ✏️ Edit Section Content")
            if sec_def:
                sec_type = sec_def.get("type")
                if sec_type == "text":
                    with st.form(f"inline_edit_{true_section_id}_{latest_run.id}"):
                        current_val = section.content if section else ""
                        new_content = st.text_area("Update content:", value=current_val, height=150)
                        if st.form_submit_button("Save Update", type="primary"):
                            if not section:
                                section = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=true_section_id, content=new_content)
                                db.add(section)
                            else:
                                section.content = new_content
                            db.commit()
                            st.success("Section updated! ⚠️ **Note: Re-run AI Validation to get an updated score.**")
                            
                elif sec_type == "table":
                    fields = sec_def.get("fields", [])
                    import pandas as pd
                    if section and section.structured_data:
                        df = pd.DataFrame(section.structured_data)
                        df.index = df.index + 1
                        render_fields = list(fields)
                        if "Reviewer Comment" in df.columns:
                            render_fields.append("Reviewer Comment")
                        for field in render_fields:
                            if field not in df.columns:
                                df[field] = None
                        df = df[render_fields]
                    else:
                        df = pd.DataFrame(columns=fields)
                        df.loc[1] = [None for _ in fields]
                        
                    column_config = {}
                    for field in fields:
                        f_lower = field.lower()
                        if "date" in f_lower:
                            column_config[field] = st.column_config.DateColumn(field, format="YYYY-MM-DD")
                            df[field] = pd.to_datetime(df[field], errors='coerce').dt.date
                        elif "no." in f_lower or "tat" in f_lower:
                            column_config[field] = st.column_config.NumberColumn(field, step=1)
                            df[field] = pd.to_numeric(df[field], errors='coerce')
                        elif field in ["Responsible (R)", "Accountable (A)", "Consulted (C)", "Informed (I)"]:
                            column_config[field] = st.column_config.SelectboxColumn(field, options=["Yes", "No"])
                        elif "level of risk" in f_lower:
                            column_config[field] = st.column_config.SelectboxColumn(field, options=["High", "Medium", "Low"])
                        else:
                            column_config[field] = st.column_config.TextColumn(field)

                    with st.form(f"inline_edit_{true_section_id}_{latest_run.id}"):
                        st.markdown("Update the table below:")
                        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"inline_editor_{true_section_id}_{latest_run.id}", column_config=column_config)
                        if st.form_submit_button("Save Update", type="primary"):
                            json_data = edited_df.to_dict(orient="records")
                            if not section:
                                section = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=true_section_id, structured_data=json_data)
                                db.add(section)
                            else:
                                section.structured_data = json_data
                                from sqlalchemy.orm.attributes import flag_modified
                                flag_modified(section, "structured_data")
                            db.commit()
                            st.success("Section updated! ⚠️ **Note: Re-run AI Validation to get an updated score.**")
                            
                elif sec_type == "file":
                    st.info("File upload editing must be done on the Create Process page.")
            else:
                st.warning(f"Could not load configuration for section {f.section_id}.")
    st.markdown("<br>", unsafe_allow_html=True)
    if latest_run.status in ["PASS", "WARNING", "NEEDS_REVISION"]:
        if st.button("Submit for Manual Review", type="primary"):
            current_note.status = "UNDER_REVIEW"
            db.commit()
            
            # Notify reviewers
            from models.database import User
            from core.notifications import create_notification
            reviewers = db.query(User).filter(User.role.in_(["reviewer", "admin"])).all()
            user_name = st.session_state.get("current_user_name", "A user")
            msg = f"{user_name} has submitted '{current_note.process_name}' for manual review."
            for r in reviewers:
                create_notification(db, r.id, msg, current_note.id)
                
            st.success("Submitted for manual review!")
            st.rerun()
