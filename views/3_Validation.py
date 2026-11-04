def extract_concise_gap(gap_str: str) -> str:
    """Distill verbose cross-section gap text into 1 punchy line."""
    step_m = re.search(r'(Step\s*\d+)', gap_str, re.IGNORECASE)
    step_prefix = f"<b>{step_m.group(1)}:</b> " if step_m else ""
    clean_p = gap_str.replace("*", "").strip()

    if "omits" in clean_p.lower():
        after = re.split(r'omits\s+', clean_p, flags=re.IGNORECASE)[1].strip()
        core = re.split(r'\s+specified in\s+', after, flags=re.IGNORECASE)[0].strip().rstrip(';.')
        return f"• {step_prefix}Missing {core}"
    elif "does not detail" in clean_p.lower():
        req_m = re.search(r'requires\s+(.*?)(?:\s+prior|\s+before|,|\.)', clean_p, re.IGNORECASE)
        req_str = f"that {req_m.group(1)}" if req_m else "verification step"
        return f"• {step_prefix}Missing verification {req_str}"
    elif "requires" in clean_p.lower() and "but" in clean_p.lower():
        req_part = re.split(r'requires\s+', clean_p, flags=re.IGNORECASE)[1].split(", but")[0].strip()
        return f"• {step_prefix}Rule requires {req_part}"
    else:
        return f"• {step_prefix}{clean_p[:80]}"

def format_direct_discrepancy(text: str) -> str:
    """Format complex discrepancy text into direct, simple, easy-to-read bullet points."""
    if not text or not text.strip():
        return ""
    import re
    clean_text = text.replace("*(Marked as OK by User)*", "").replace("*(Resolved by Clarification)*", "").strip()

    pattern = r'Row\s+(\d+)\s*:\s*(.*?)(?:\s+in\s+[^.]+?)?\s+(?:is missing|cannot be blank|is empty|required)\.?'
    matches = re.findall(pattern, clean_text, re.IGNORECASE)
    if matches:
        from collections import defaultdict
        field_to_rows = defaultdict(list)
        for r_num, field in matches:
            clean_f = field.strip().rstrip(".").strip().replace("*", "")
            if clean_f.lower().startswith("document title"):
                clean_f = "Document Title"
            if r_num not in field_to_rows[clean_f]:
                field_to_rows[clean_f].append(r_num)
        items = []
        for field, rows in field_to_rows.items():
            sorted_rows = sorted(rows, key=lambda x: int(x))
            r_phrase = f"Row {sorted_rows[0]}" if len(sorted_rows) == 1 else f"Rows {', '.join(sorted_rows[:-1])} & {sorted_rows[-1]}"
            items.append(f"• <b>{field}</b> is incomplete in <b>{r_phrase}</b>")
        return "\n".join(items)

    if "Specifically:" in clean_text or "Specifically :" in clean_text:
        parts = re.split(r'Specifically\s*:\s*', clean_text, maxsplit=1)
        details = parts[1].strip()
        raw_points = re.split(r'\s*(?:;\s*)?(?:\d+\))\s*', details)
        clean_points = [p.strip().rstrip(';.') for p in raw_points if p.strip()]
        condensed_gaps = [extract_concise_gap(p) for p in clean_points]
        sec_m = re.findall(r'1\.\d+', clean_text)
        sec_str = " vs ".join(sorted(list(set(sec_m)))) if sec_m else ""
        header = f"📍 <b>Location:</b> Section {sec_str}\n" if sec_str else ""
        return f"{header}\n".strip() + "\n" + "\n".join(condensed_gaps)

    # Flowchart vs Process Description Inconsistency
    if "Inconsistency between the Process Flowchart" in clean_text or ("Flowchart" in clean_text and "Process Description" in clean_text):
        m_loop = re.search(r"contains\s+(?:a\s+)?(.*?)(?:,\s*but|\s+but)", clean_text, re.IGNORECASE)
        if m_loop:
            raw_loop = m_loop.group(1).replace("*", "").strip()
            loop_desc = re.sub(r'\s*\([^)]*\)', '', raw_loop).strip()
            if not loop_desc:
                loop_desc = "decision branch and non-compliance loop"
        else:
            loop_desc = "decision branch and non-compliance loop"
        return f"📍 <b>Location:</b> Section 1.11 (Flowchart) vs Section 1.12 (Process Description)\n• Flowchart specifies <b>{loop_desc}</b>, but Section 1.12 omits how this is executed."

    # RACI Matrix vs Process Description
    if "RACI" in clean_text and ("missing" in clean_text.lower() or "activities" in clean_text.lower()):
        m_acts = re.search(r':\s*([^.]+)', clean_text)
        act_list = (m_acts.group(1).strip() if m_acts else "workflow activities").replace("*", "")
        return f"📍 <b>Location:</b> Section 1.12 (Process Description) vs Section 1.13 (RACI Matrix)\n• <b>Missing Roles:</b> Assign Responsible & Accountable for: <b>{act_list}</b>"

    sentences = [s.strip().replace("*", "") for s in re.split(r'\.\s+', clean_text) if s.strip()]
    if len(sentences) > 1:
        return f"• {sentences[0]}.\n• {sentences[1]}."
    return f"• {clean_text.replace('*', '')}"

import streamlit as st
from models.database import SessionLocal, get_db, ProcessNote, ValidationRun, ValidationFinding, ProcessSection, ReviewHistory
from models.schemas import ProcessNoteSchema, ProcessSectionSchema
from sqlalchemy.orm import Session
from core.validation_engine import ValidationEngine
import json
import os


from core.ui_utils import inject_custom_css
from core.ui_utils import inject_custom_css


st.title("Run AI Validation")

db: Session = SessionLocal()
try:
    engine = ValidationEngine()

    current_role = st.session_state.get("current_user_role", "creator")
    current_user_id = st.session_state.get("current_user_id")

    valid_statuses = ["DRAFT", "NEEDS_REVISION", "WARNING", "PASS", "UNDER_REVIEW"]
    if current_role == "admin":
        base_query = db.query(ProcessNote).filter(ProcessNote.status.in_(valid_statuses))
    else:
        base_query = db.query(ProcessNote).filter(
            ProcessNote.created_by == current_user_id,
            ProcessNote.status.in_(valid_statuses)
        )
    notes = base_query.all()
    note_options = {f"[{n.id}] {n.process_name} (v{n.version})": n for n in notes}

    if not note_options:
        st.info("No process notes available for validation.")
        st.stop()

    # Clean up validation_selectbox if its key is no longer in note_options to prevent Streamlit ValueError
    if "validation_selectbox" in st.session_state:
        if st.session_state.validation_selectbox not in note_options:
            st.session_state.pop("validation_selectbox", None)

    # Sync widget state with selected_note_id
    opts_list = list(note_options.keys())
    default_index = 0
    if "selected_note_id" in st.session_state:
        for idx, (key, note) in enumerate(note_options.items()):
            if note.id == st.session_state.selected_note_id:
                st.session_state.validation_selectbox = key
                default_index = idx
                break

    def on_note_change():
        selected_str = st.session_state.get("validation_selectbox")
        if selected_str and selected_str in note_options:
            st.session_state.selected_note_id = note_options[selected_str].id

    selected = st.selectbox(
        "Select Process Note to Validate",
        opts_list,
        index=default_index,
        key="validation_selectbox",
        on_change=on_note_change
    )
    current_note = note_options[selected]
    st.session_state.selected_note_id = current_note.id

    status_class = "badge-draft"
    if current_note.status == "PASS": status_class = "badge-pass"
    elif current_note.status == "WARNING": status_class = "badge-warning"
    elif current_note.status == "NEEDS_REVISION": status_class = "badge-fail"
    elif current_note.status == "UNDER_REVIEW": status_class = "badge-review"

    st.markdown(f"**Current Status:** <span class='badge {status_class}'>{current_note.status.replace('_', ' ')}</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if current_note.status in ["NEEDS_REVISION", "APPROVED"]:
        latest_review = db.query(ReviewHistory).filter(ReviewHistory.process_note_id == current_note.id).order_by(ReviewHistory.timestamp.desc()).first()
        if latest_review and latest_review.comments:
            st.markdown(f"**Reviewer Comment ({latest_review.reviewer}):**")
            st.info(latest_review.comments)
            st.markdown("<br>", unsafe_allow_html=True)

    @st.cache_data
    def load_sections_config():
        import yaml
        try:
            with open("config/sections.yaml", "r") as f:
                return yaml.safe_load(f).get("sections", [])
        except Exception:
            return []

    sections_config = load_sections_config()

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
                rec_lines = list(sec_res.recommendations)
                if sec_res.questions:
                    rec_lines.append("\n**Clarification Questions for Process Owner:**")
                    rec_lines.extend([f"- {q}" for q in sec_res.questions])

                vf = ValidationFinding(
                    validation_id=v_run.id,
                    process_name=current_note.process_name,
                    section_id=sec_res.section,
                    severity=sec_res.severity,
                    status=sec_res.status,
                    score=sec_res.score,
                    issue="\n".join(sec_res.issues),
                    recommendation="\n".join(rec_lines),
                    is_cross_section=0
                )
                db.add(vf)

            for cr in result.cross_section_issues:
                cr_rec = []
                if cr.get("questions"):
                    cr_rec.append("**Clarification Questions for Process Owner:**")
                    cr_rec.extend([f"- {q}" for q in cr.get("questions")])

                rel = cr.get("related_sections", [])
                label = f"Cross-Section ({' & '.join(rel)})" if rel else "Cross-Section Alignment"

                vf = ValidationFinding(
                    validation_id=v_run.id,
                    process_name=current_note.process_name,
                    section_id=label,
                    severity=cr.get("severity", "MEDIUM"),
                    status="NEEDS_REVISION" if cr.get("severity") == "HIGH" else "WARNING",
                    score=0.0 if cr.get("severity") == "HIGH" else 50.0,
                    issue=cr.get("issue", ""),
                    recommendation="\n".join(cr_rec),
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
        from datetime import timedelta
        # Convert UTC to IST (+5:30)
        local_time = latest_run.timestamp + timedelta(hours=5, minutes=30)
        st.markdown(f"### Latest Validation Results (<span style='white-space: nowrap;'>{local_time.strftime('%Y-%m-%d %H:%M')}</span>)", unsafe_allow_html=True)

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

        st.markdown("### Cross-Section Alignment Audit (BE Standards)")
        cross_findings = [f for f in findings if f.is_cross_section == 1]
        if cross_findings:
            for f in cross_findings:
                is_resolved = "*(Resolved by Clarification)*" in (f.issue or "")
                display_cr_issue = (f.issue or "").replace("*(Resolved by Clarification)*\n\n", "").replace("*(Resolved by Clarification)*", "")

                with st.expander(f"⚠️ [{f.severity}] {f.section_id} - {'✅ Resolved' if is_resolved else 'Gap Identified'}", expanded=not is_resolved):
                    st.markdown(f"**Audit Observation:**\n\n{format_direct_discrepancy(display_cr_issue)}")

                    if f.recommendation and "**Clarification Questions for Process Owner:**" in f.recommendation:
                        st.markdown("""
                        <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 12px; border-radius: 4px; margin: 12px 0;">
                            <strong style="color: #92400E;">💬 Action Required: Business Excellence Clarification Questions</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        q_part = f.recommendation.split("**Clarification Questions for Process Owner:**")[1].strip()
                        st.markdown(q_part)

                        if not is_resolved:
                            cr_ans = st.text_area("Process Owner Response / Operational Details:", key=f"cr_ans_{f.id}", height=85, placeholder="Explain who executes this, tools used, and verification procedure...")
                            if st.button("✨ Incorporate Clarification into Process Description (1.12)", key=f"btn_apply_cr_{f.id}", type="primary"):
                                if not cr_ans.strip():
                                    st.warning("Please enter your clarification response.")
                                else:
                                    with st.spinner("AI is incorporating your explanation into Section 1.12..."):
                                        from services.llm_service import get_llm_provider
                                        llm = get_llm_provider()
                                        desc_sec = db.query(ProcessSection).filter(ProcessSection.process_note_id == current_note.id, ProcessSection.section_id == "1.12").first()
                                        if desc_sec and desc_sec.structured_data:
                                            updated_data = llm.resolve_clarification("1.12", "table", desc_sec.structured_data, display_cr_issue, cr_ans)
                                            desc_sec.structured_data = updated_data
                                            f.status = "PASS"
                                            f.severity = "LOW"
                                            f.issue = f"*(Resolved by Clarification)*\n\n{f.issue}"
                                            db.commit()
                                            st.success("Clarification saved to Section 1.12! Click 'Run AI Validation' above to re-evaluate.")
                                            st.rerun()
        else:
            st.success("✅ No cross-section gaps found. Business rules, KPIs, flowchart, and RACI are fully aligned with Process Description.")

        st.markdown("### Section-by-Section Findings")
        sec_findings = [f for f in findings if f.is_cross_section == 0]

        for f in sec_findings:
            is_manual = "*(Marked as OK by User)*" in (f.issue or "") or "*(Resolved by Clarification)*" in (f.issue or "")
            display_issue = (f.issue or "").replace("*(Marked as OK by User)*\n\n", "").replace("*(Marked as OK by User)*", "").replace("*(Resolved by Clarification)*\n\n", "")

            badge_cls = "badge-pass" if f.status == "PASS" else ("badge-warning" if f.status == "WARNING" else "badge-fail")
            badge_text = "PASS (Resolved)" if is_manual else f.status
            badge_html = f"<span class='badge {badge_cls}'>{badge_text}</span>"

            if is_manual:
                status_emoji = "✅ PASS (Resolved)"
            else:
                status_emoji = "✅ PASS" if f.status == "PASS" else ("⚠️ WARNING" if f.status == "WARNING" else "❌ NEEDS REVISION")

            with st.expander(f"{f.section_id} (Score: {f.score}) - {status_emoji}"):
                st.markdown(f"**Status:** {badge_html}", unsafe_allow_html=True)
                if display_issue.strip():
                    st.markdown(f"**Issues ({f.severity}):**")
                    st.write(display_issue.strip())

                # Check for clarification questions
                if f.recommendation:
                    if "**Clarification Questions for Process Owner:**" in f.recommendation:
                        rec_parts = f.recommendation.split("**Clarification Questions for Process Owner:**")
                        advice = rec_parts[0].strip()
                        questions = rec_parts[1].strip()

                        if advice:
                            st.markdown("**Recommendation:**")
                            st.write(advice)

                        st.markdown("""
                        <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 10px; border-radius: 4px; margin: 10px 0;">
                            <strong style="color: #92400E;">💬 Clarification Questions for Process Owner:</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(questions)

                        if f.status != "PASS" and not is_manual:
                            sec_ans = st.text_area("Your response / missing details for this section:", key=f"ans_sec_{f.id}", height=80)
                            if st.button("✨ Apply Clarification to This Section", key=f"btn_sec_apply_{f.id}", type="primary"):
                                if not sec_ans.strip():
                                    st.warning("Please type your response before applying.")
                                else:
                                    with st.spinner("AI is updating this section..."):
                                        from services.llm_service import get_llm_provider
                                        llm = get_llm_provider()

                                        # Find true section ID
                                        sec_def = next((s for s in sections_config if str(s.get("id")) == str(f.section_id) or str(s.get("name")) == str(f.section_id) or str(f.section_id).startswith(str(s.get("id")))), None)
                                        t_sec_id = sec_def.get("id") if sec_def else f.section_id.split(" ")[0].replace("-", "").strip()

                                        target_sec = db.query(ProcessSection).filter(ProcessSection.process_note_id == current_note.id, ProcessSection.section_id == t_sec_id).first()
                                        if target_sec:
                                            s_type = sec_def.get("type", "text") if sec_def else "text"
                                            curr_cont = target_sec.structured_data if s_type == "table" else (target_sec.content or "")
                                            updated_res = llm.resolve_clarification(t_sec_id, s_type, curr_cont, questions, sec_ans)
                                            if s_type == "table" and isinstance(updated_res, list):
                                                target_sec.structured_data = updated_res
                                            else:
                                                target_sec.content = str(updated_res)

                                            f.status = "PASS"
                                            f.severity = "LOW"
                                            f.issue = f"*(Resolved by Clarification)*\n\n{f.issue}"
                                            db.commit()
                                            st.success(f"Section {t_sec_id} updated with your clarification! Click 'Run AI Validation' above to re-evaluate.")
                                            st.rerun()
                    else:
                        st.markdown("**Recommendation:**")
                        st.write(f.recommendation)

                if not display_issue.strip() and not f.recommendation:
                    st.write("Section looks good.")

                if f.status != "PASS" and not is_manual:
                    if st.button("Mark as OK (Ignore Feedback)", key=f"ignore_{f.id}"):
                        f.status = "PASS"
                        f.severity = "LOW"
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

                        pass_threshold = 75.0
                        warning_threshold = 65.0

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
                                    st.markdown('<div style="font-weight: 700; font-size: 14px; color: #1E293B; margin: 6px 0;">👤 Manual Reviewer Feedback</div>', unsafe_allow_html=True)
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
                st.markdown('<div style="font-weight: 700; font-size: 14px; color: #1E293B; margin: 6px 0;">✏️ Edit Section Content</div>', unsafe_allow_html=True)
                if sec_def:
                    sec_type = sec_def.get("type")
                    if sec_type == "text":
                        with st.form(f"inline_edit_{true_section_id}_{latest_run.id}"):
                            from config.guided_questions import clean_heading_hashes
                            current_val = clean_heading_hashes(section.content, true_section_id) if section else ""
                            new_content = st.text_area("Update content:", value=current_val, height=150)
                            if st.form_submit_button("Save Update", type="primary"):
                                cleaned_val = clean_heading_hashes(new_content, true_section_id)
                                if not section:
                                    section = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=true_section_id, content=cleaned_val)
                                    db.add(section)
                                else:
                                    section.content = cleaned_val
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
                            disabled_cols = ["Reviewer Comment"] if "Reviewer Comment" in df.columns else False
                            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"inline_editor_{true_section_id}_{latest_run.id}", column_config=column_config, disabled=disabled_cols)
                            if st.form_submit_button("Save Update", type="primary"):
                                raw_data = edited_df.to_dict(orient="records")
                                json_data = []
                                for row in raw_data:
                                    clean_row = {}
                                    for k, v in row.items():
                                        if pd.isna(v):
                                            clean_row[k] = None
                                        elif hasattr(v, 'isoformat'):
                                            clean_row[k] = v.isoformat()
                                        else:
                                            clean_row[k] = v
                                    json_data.append(clean_row)
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
        if current_note.status in ["PASS", "WARNING", "NEEDS_REVISION"]:
            if current_note.status == "NEEDS_REVISION":
                st.warning("⚠️ **Note:** This process note is currently flagged as **Needs Revision**. Reviewers will see these critical findings in the Review queue.")
            if st.button("Submit for Manual Review", type="primary", use_container_width=True):
                current_note.status = "UNDER_REVIEW"

                # Record submission in ReviewHistory
                rev_history = ReviewHistory(
                    process_note_id=current_note.id,
                    process_name=current_note.process_name,
                    reviewer=st.session_state.get("current_user_name", "Creator"),
                    action="SUBMITTED",
                    comments="Submitted by creator for governance review.",
                )
                db.add(rev_history)
                db.commit()

                # Notify reviewers
                from models.database import User
                from core.notifications import create_notification
                reviewers = db.query(User).filter(User.role.in_(["reviewer", "admin"])).all()
                user_name = st.session_state.get("current_user_name", "A user")
                msg = f"{user_name} has submitted '{current_note.process_name}' for manual review."
                for r in reviewers:
                    create_notification(db, r.id, msg, current_note.id)

                # Safely update selectbox key in session state
                updated_key = f"[{current_note.id}] {current_note.process_name} (v{current_note.version})"
                st.session_state.validation_selectbox = updated_key
                st.session_state.selected_note_id = current_note.id

                st.success("🎉 Successfully submitted for manual review! Reviewers have been notified.")
                st.rerun()
        elif current_note.status == "UNDER_REVIEW":
            st.info("🕒 **Status: Under Review** — This note has been successfully submitted and is currently in the Review Queue. Reviewers can now inspect, comment, or approve it in the **Review & Sign-Off** hub.")

finally:
    db.close()
