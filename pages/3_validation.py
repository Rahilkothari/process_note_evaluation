import streamlit as st
from models.database import get_db, ProcessNote, ValidationRun, ValidationFinding, ProcessSection
from models.schemas import ProcessNoteSchema, ProcessSectionSchema
from sqlalchemy.orm import Session
from core.validation_engine import ValidationEngine
import json

st.set_page_config(page_title="Validation", layout="wide")
from core.ui_utils import inject_custom_css
from core.auth import require_login
inject_custom_css()
require_login()

st.title("Run AI Validation")

db: Session = next(get_db())
engine = ValidationEngine()

notes = db.query(ProcessNote).filter(ProcessNote.status.in_(["DRAFT", "NEEDS_REVISION"])).all()
note_options = {f"[{n.id}] {n.process_name} (v{n.version})": n for n in notes}

if not note_options:
    st.info("No draft process notes available for validation.")
    st.stop()

selected = st.selectbox("Select Process Note to Validate", list(note_options.keys()))
current_note = note_options[selected]

status_class = "badge-draft"
if current_note.status == "PASS": status_class = "badge-pass"
elif current_note.status == "WARNING": status_class = "badge-warning"
elif current_note.status == "NEEDS_REVISION": status_class = "badge-fail"

st.markdown(f"**Current Status:** <span class='badge {status_class}'>{current_note.status.replace('_', ' ')}</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if st.button("Run AI Validation", type="primary"):
    with st.spinner("Running layer 1 and semantic AI validation..."):
        import yaml
        try:
            with open("config/sections.yaml", "r") as f:
                sections_config = yaml.safe_load(f).get("sections", [])
        except Exception:
            sections_config = []
            
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
            overall_score=result.overall_score,
            status=result.overall_status,
            model_used="mock"
        )
        db.add(v_run)
        db.commit()
        db.refresh(v_run)
        
        for sec_res in result.section_results:
            vf = ValidationFinding(
                validation_id=v_run.id,
                section_id=sec_res.section,
                severity=sec_res.severity,
                status=sec_res.status,
                score=sec_res.score,
                issue="\n".join(sec_res.issues),
                recommendation="\n".join(sec_res.recommendations)
            )
            db.add(vf)
            
        for cr in result.cross_section_issues:
            vf = ValidationFinding(
                validation_id=v_run.id,
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
        badge_cls = "badge-pass" if f.status == "PASS" else ("badge-warning" if f.status == "WARNING" else "badge-fail")
        badge_html = f"<span class='badge {badge_cls}'>{f.status}</span>"
        
        with st.expander(f"{f.section_id} (Score: {f.score})"):
            st.markdown(f"**Status:** {badge_html}", unsafe_allow_html=True)
            if f.issue:
                st.markdown(f"**Issues ({f.severity}):**")
                st.write(f.issue)
            if f.recommendation:
                st.markdown("**Recommendation:**")
                st.write(f.recommendation)
            if not f.issue and not f.recommendation:
                st.write("Section looks good.")
                
    st.markdown("<br>", unsafe_allow_html=True)
    if latest_run.status in ["PASS", "WARNING", "NEEDS_REVISION"]:
        if st.button("Submit for Manual Review", type="primary"):
            current_note.status = "UNDER_REVIEW"
            db.commit()
            st.success("Submitted for manual review!")
            st.rerun()
