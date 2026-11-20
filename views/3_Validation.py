def format_direct_discrepancy(text: str) -> str:
    """Format complex discrepancy text into direct, simple, easy-to-read markdown bullet points."""
    if not text or not text.strip():
        return ""
    import re
    clean_text = text.replace("*(Marked as OK by User)*", "").replace("*(Resolved by Clarification)*", "").strip()

    # Table row missing field pattern (e.g. Row 1: Document Title is required)
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
            items.append(f"• **{field}** is incomplete in **{r_phrase}**")
        return "\n".join(items)

    # Convert any raw HTML <b> tags to markdown **
    clean_text = re.sub(r'</?b>', '**', clean_text)

    # Flowchart vs Process Description Inconsistency
    if "Inconsistency between the Process Flowchart" in clean_text or ("Flowchart" in clean_text and "Process Description" in clean_text):
        m_loop = re.search(r"contains\s+(?:a\s+)?(.*?)(?:,\s*but|\s+but)", clean_text, re.IGNORECASE)
        loop_desc = "decision branch and non-compliance loop"
        if m_loop:
            raw_loop = m_loop.group(1).replace("*", "").strip()
            cand = re.sub(r'\s*\([^)]*\)', '', raw_loop).strip()
            if cand:
                loop_desc = cand
        return f"📍 **Location:** Section 1.11 (Flowchart) vs Section 1.12 (Process Description)\n• Flowchart specifies **{loop_desc}**, but Section 1.12 omits how this is executed."

    # RACI Matrix vs Process Description
    if "RACI" in clean_text and ("missing" in clean_text.lower() or "activities" in clean_text.lower()):
        m_acts = re.search(r':\s*([^.]+)', clean_text)
        act_list = (m_acts.group(1).strip() if m_acts else "workflow activities").replace("*", "")
        return f"📍 **Location:** Section 1.12 (Process Description) vs Section 1.13 (RACI Matrix)\n• **Missing Roles:** Assign Responsible & Accountable roles for: **{act_list}**"

    # Clean double dots and collapse repeated bullets
    clean_text = re.sub(r'\.{2,}', '.', clean_text)
    clean_text = re.sub(r'[•\*\-]{2,}', '•', clean_text)

    # If text has bullet points embedded
    if "•" in clean_text or "\n-" in clean_text or "\n*" in clean_text:
        norm_text = re.sub(r'\n\s*[-*•]\s*', '\n• ', clean_text)
        norm_text = re.sub(r':\s*•', ':\n•', norm_text)
        raw_parts = [p.strip().rstrip('.') for p in norm_text.split('•') if p.strip()]
        if raw_parts:
            lead_title = ""
            items = []
            if raw_parts[0].endswith(":") and len(raw_parts) > 1:
                lead_title = raw_parts[0].rstrip(":").strip()
                items = raw_parts[1:]
            else:
                items = raw_parts

            formatted_items = []
            for it in items:
                clean_it = re.sub(r'^[•\-\*\s]+', '', it).strip().rstrip('.')
                if clean_it:
                    formatted_items.append(f"• {clean_it}")

            if lead_title and lead_title.lower() not in ["audit observation", "issue", "gap identified"]:
                return f"**{lead_title}:**\n" + "\n".join(formatted_items)
            return "\n".join(formatted_items)

    # Handle standard sentences without double dots or double bullets
    cleaned = re.sub(r'\s*\.{2,}', '.', clean_text)
    sentences = [re.sub(r'^[•\-\s]+', '', s).strip().replace("*", "") for s in re.split(r'\.\s+', cleaned) if s.strip()]
    if len(sentences) > 1:
        return f"• {sentences[0]}.\n• {sentences[1]}."
    elif sentences:
        return f"• {sentences[0]}."
    return clean_text

import streamlit as st
from models.database import SessionLocal, get_db, ProcessNote, ValidationRun, ValidationFinding, ProcessSection, ReviewHistory
from models.schemas import ProcessNoteSchema, ProcessSectionSchema
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from core.validation_engine import ValidationEngine
import json
import os
import re

from core.ui_utils import inject_custom_css

def render_crisp_feedback(issue_text: str, rec_text: str, severity: str = "MEDIUM", questions_text: str = ""):
    """Renders validation issues and recommendations as crisp, bite-sized, high-contrast action cards without raw markdown asterisks or stars."""
    def clean_html_text(text: str) -> str:
        if not text:
            return ""
        t = text.strip()
        t = re.sub(r"^[•\-\–\—\s\d\.\)\(]+", "", t).strip()
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.DOTALL)
        t = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", t)
        t = t.replace("*", "")
        t = re.sub(r"^[•\-\–\—\s]+", "", t).strip()
        return t

    def extract_lines(t):
        if not t or not t.strip():
            return []
        clean = t.replace("*(Marked as OK by User)*", "").replace("*(Resolved by Clarification)*", "").replace("*(Resolved by Auto-Correction)*", "").strip()
        raw_lines = [l.strip() for l in re.split(r"[\r\n]+", clean) if l.strip()]
        if any(re.match(r"^[•\-\–\—\*\d\.]", l) for l in raw_lines):
            items = raw_lines
        else:
            pattern = r"(?<!\bSr)(?<!\bNo)(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<!\bSec)(?<!\bv)\.\s+(?=[A-Z0-9])"
            items = [s.strip() for s in re.split(pattern, clean) if s.strip()]

        res = []
        for it in items:
            cleaned = clean_html_text(it)
            if cleaned:
                if not cleaned.endswith((".", "?", "!", ":", ";", ">", "'", "\"")):
                    cleaned += "."
                res.append(cleaned)
        return res

    def to_clean_html(raw_html: str) -> str:
        return "\n".join(l.strip() for l in raw_html.strip().splitlines() if l.strip())

    raw_issues = extract_lines(issue_text)
    raw_recs = extract_lines(rec_text)

    pure_issues = []
    embedded_recs = []
    for l in raw_issues:
        l_lower = l.lower()
        if any(k in l_lower for k in ["must be clearly articulated", "must be specified", "should be updated", "recommended fix", "clearly articulate", "must be defined", "please define"]):
            embedded_recs.append(l)
        else:
            pure_issues.append(l)

    all_recs = raw_recs + embedded_recs
    unique_recs = []
    for r in all_recs:
        if r and r not in unique_recs:
            unique_recs.append(r)

    is_high = severity == "HIGH"
    is_warn = severity == "MEDIUM"
    border_color = "#E11D48" if is_high else ("#F59E0B" if is_warn else "#10B981")
    header_color = "#9F1239" if is_high else ("#92400E" if is_warn else "#166534")
    icon = "🔴" if is_high else ("⚠️" if is_warn else "💡")
    badge_label = "Action Required" if is_high else ("Operational Gap" if is_warn else "Polish Tip")

    # Case A: Multiple issues share ONE common recommendation (consolidate and mention solution ONCE)
    if len(pure_issues) > 1 and len(unique_recs) == 1:
        iss_items = "".join([f'<li style="margin-bottom: 5px;">{iss}</li>' for iss in pure_issues])
        common_rec = unique_recs[0]
        card = f"""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4.5px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin: 8px 0 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
<span style="font-weight: 700; color: {header_color}; font-size: 13.5px;">{icon} Identified Issues ({len(pure_issues)} items):</span>
<span style="font-size: 11px; font-weight: 700; color: {header_color}; background: #F8FAFC; padding: 2px 8px; border-radius: 10px; border: 1px solid #E2E8F0;">{badge_label}</span>
</div>
<ul style="margin: 0; padding-left: 20px; color: #334155; font-size: 13px; line-height: 1.5; margin-bottom: 8px;">
{iss_items}
</ul>
<div style="padding: 8px 12px; background: #F0FDF4; border-radius: 6px; border: 1px solid #BBF7D0; font-size: 12.5px; color: #166534; line-height: 1.45;">
<b>💡 Recommended Fix:</b> {common_rec}
</div>
</div>
"""
        st.markdown(to_clean_html(card), unsafe_allow_html=True)

    # Case B: Individual issues with distinct recommendations or single issue
    elif pure_issues:
        for idx, iss in enumerate(pure_issues):
            rc = unique_recs[idx] if idx < len(unique_recs) else ""
            rec_html = f'<div style="padding: 8px 12px; background: #F0FDF4; border-radius: 6px; border: 1px solid #BBF7D0; font-size: 12.5px; color: #166534; line-height: 1.45; margin-top: 8px;"><b>💡 Recommended Fix:</b> {rc}</div>' if rc else ""
            card = f"""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4.5px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin: 8px 0 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
<span style="font-weight: 700; color: {header_color}; font-size: 13.5px;">{icon} Point {idx + 1}:</span>
<span style="font-size: 11px; font-weight: 700; color: {header_color}; background: #F8FAFC; padding: 2px 8px; border-radius: 10px; border: 1px solid #E2E8F0;">{badge_label}</span>
</div>
<div style="color: #334155; font-size: 13px; line-height: 1.5;">
{iss}
</div>
{rec_html}
</div>
"""
            st.markdown(to_clean_html(card), unsafe_allow_html=True)

        if len(unique_recs) > len(pure_issues):
            for r_idx in range(len(pure_issues), len(unique_recs)):
                extra = f"""
<div style="padding: 8px 14px; background: #F0FDF4; border-radius: 6px; border: 1px solid #BBF7D0; border-left: 4px solid #22C55E; font-size: 12.5px; color: #166534; line-height: 1.45; margin: 6px 0;">
<b>💡 Additional Fix:</b> {unique_recs[r_idx]}
</div>
"""
                st.markdown(to_clean_html(extra), unsafe_allow_html=True)

    elif unique_recs:
        for idx, rc in enumerate(unique_recs):
            card = f"""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4.5px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin: 8px 0 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
<span style="font-weight: 700; color: {header_color}; font-size: 13.5px;">{icon} Point {idx + 1}:</span>
<span style="font-size: 11px; font-weight: 700; color: {header_color}; background: #F8FAFC; padding: 2px 8px; border-radius: 10px; border: 1px solid #E2E8F0;">{badge_label}</span>
</div>
<div style="padding: 8px 12px; background: #F0FDF4; border-radius: 6px; border: 1px solid #BBF7D0; font-size: 12.5px; color: #166534; line-height: 1.45;">
<b>💡 Recommended Fix:</b> {rc}
</div>
</div>
"""
            st.markdown(to_clean_html(card), unsafe_allow_html=True)

    if questions_text and questions_text.strip():
        q_lines = extract_lines(questions_text)
        if q_lines:
            q_html = "".join([f'<li style="margin-bottom: 5px;">{q}</li>' for q in q_lines])
            q_box = f"""
<div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4.5px solid #3B82F6; border-radius: 8px; padding: 10px 16px; margin: 10px 0;">
<div style="font-weight: 700; color: #1E40AF; font-size: 13px; margin-bottom: 5px;">
💬 Clarification Questions for Creator:
</div>
<ul style="margin: 0; padding-left: 20px; color: #1E3A8A; font-size: 12.5px; line-height: 1.45;">
{q_html}
</ul>
</div>
"""
            st.markdown(to_clean_html(q_box), unsafe_allow_html=True)

def render_inline_section_editor(sec_def, section, current_note, db, key_suffix=""):
    """Renders interactive inline editor (data_editor for tables, text_area for text/flowcharts) directly inside finding cards."""
    if not sec_def:
        st.warning("Could not load configuration for this section.")
        return

    sec_id = sec_def.get("id")
    sec_name = sec_def.get("name")
    sec_type = sec_def.get("type")

    st.markdown(f'<div style="font-weight: 700; font-size: 13.5px; color: #1E293B; margin: 10px 0 6px 0;">✏️ Edit Section {sec_id} ({sec_name}) Content</div>', unsafe_allow_html=True)

    if sec_type == "text":
        with st.form(f"inline_edit_{sec_id}_{key_suffix}"):
            from config.guided_questions import clean_heading_hashes
            current_val = clean_heading_hashes(section.content, sec_id) if section else ""
            new_content = st.text_area("Update content:", value=current_val, height=150)
            if st.form_submit_button(f"💾 Save Update to Section {sec_id}", type="primary"):
                cleaned_val = clean_heading_hashes(new_content, sec_id)
                if not section:
                    section = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=cleaned_val)
                    db.add(section)
                else:
                    section.content = cleaned_val
                db.commit()
                st.success(f"✅ Section {sec_id} updated! ⚠️ Re-run AI Validation above to get an updated score.")
                st.rerun()

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
            elif f_lower in ["sr. no.", "sr. no", "sr no.", "sr no", "serial no"]:
                column_config[field] = st.column_config.NumberColumn(field, step=1)
                df[field] = pd.to_numeric(df[field], errors='coerce')
            elif field in ["Responsible (R)", "Accountable (A)", "Consulted (C)", "Informed (I)"]:
                column_config[field] = st.column_config.SelectboxColumn(field, options=["Yes", "No"])
            elif "level of risk" in f_lower:
                column_config[field] = st.column_config.SelectboxColumn(field, options=["High", "Medium", "Low"])
            else:
                column_config[field] = st.column_config.TextColumn(field)

        with st.form(f"inline_edit_{sec_id}_{key_suffix}"):
            st.markdown(f"Update table rows for **Section {sec_id} - {sec_name}**:")
            disabled_cols = ["Reviewer Comment"] if "Reviewer Comment" in df.columns else False
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"inline_editor_{sec_id}_{key_suffix}", column_config=column_config, disabled=disabled_cols)
            if st.form_submit_button(f"💾 Save Update to Section {sec_id}", type="primary"):
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
                    section = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=json_data)
                    db.add(section)
                else:
                    section.structured_data = json_data
                    flag_modified(section, "structured_data")
                db.commit()
                st.success(f"✅ Section {sec_id} updated! ⚠️ Re-run AI Validation above to get an updated score.")
                st.rerun()

    elif sec_type in ["flowchart", "file"]:
        current_chart = section.content if section else ""
        with st.form(f"inline_edit_{sec_id}_{key_suffix}"):
            st.markdown(f"Update Mermaid flowchart syntax for **Section {sec_id}**:")
            new_flow = st.text_area("Mermaid Flowchart Code:", value=current_chart or "", height=140)
            if st.form_submit_button(f"💾 Save Flowchart to Section {sec_id}", type="primary"):
                if not section:
                    section = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=new_flow)
                    db.add(section)
                else:
                    section.content = new_flow
                db.commit()
                st.success(f"✅ Flowchart updated! ⚠️ Re-run AI Validation above to get an updated score.")
                st.rerun()


st.title("Run AI Validation")

db: Session = SessionLocal()
try:
    engine = ValidationEngine()

    current_role = st.session_state.get("current_user_role", "creator")
    current_user_id = st.session_state.get("current_user_id")

    valid_statuses = ["DRAFT", "NEEDS_REVISION", "WARNING", "PASS", "UNDER_REVIEW"]
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

    latest_review = db.query(ReviewHistory).filter(ReviewHistory.process_note_id == current_note.id).order_by(ReviewHistory.timestamp.desc()).first()
    flagged_review_sids = set()
    if latest_review and latest_review.comments:
        flagged_review_sids = set(re.findall(r'1\.\d+', latest_review.comments))

    if current_note.status == "NEEDS_REVISION":
        if latest_review and latest_review.comments:
            pills_html = " ".join([f'<span style="background: #FFFFFF; border: 1.5px solid #F43F5E; color: #9F1239; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 11.5px; margin-right: 6px;">⚠️ Section {sid}</span>' for sid in sorted(flagged_review_sids)])
            pills_summary = f'<div style="margin-top: 10px; padding-top: 10px; border-top: 1px dashed #FECDD3; font-size: 12.5px; color: #9F1239;"><b>Flagged Sections Needing Revision:</b> {pills_html}</div>' if pills_html else ""
            clean_reviewer_comments = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', latest_review.comments).replace('*', '')
            st.markdown(f"""
            <div style="background: #FFF1F2; border: 2px solid #FDA4AF; border-left: 6px solid #E11D48; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="font-weight: 800; color: #9F1239; font-size: 14.5px; display: flex; align-items: center; gap: 8px;">
                        <span>📢</span> <b>Reviewer Feedback from {latest_review.reviewer} (Revisions Required):</b>
                    </div>
                    <span style="font-size: 11px; color: #E11D48; background: #FFE4E6; border: 1.5px solid #FDA4AF; padding: 3px 10px; border-radius: 12px; font-weight: 800;">Action Required</span>
                </div>
                <div style="color: #4C0519; font-size: 13.5px; line-height: 1.5; font-weight: 500; background: #FFFFFF; border: 1px solid #FECDD3; border-radius: 6px; padding: 12px 16px; margin-top: 4px; white-space: pre-wrap;">
                    {clean_reviewer_comments}
                </div>
                {pills_summary}
            </div>
            """, unsafe_allow_html=True)
    elif current_note.status == "APPROVED":
        if latest_review and latest_review.comments:
            st.markdown(f"**Reviewer Comment ({latest_review.reviewer}):**")
            st.info(latest_review.comments)
            st.markdown("<br>", unsafe_allow_html=True)

    # Reassuring Quick-Submission Banner
    if current_note.status == "UNDER_REVIEW":
        st.markdown("""
        <div style="background: #FEF3C7; border: 1px solid #FCD34D; border-left: 5px solid #F59E0B; border-radius: 8px; padding: 12px 18px; margin-bottom: 16px;">
            <div style="font-weight: 700; color: #92400E; font-size: 14px; margin-bottom: 2px;">🕒 Process Note Under Manual Review</div>
            <div style="color: #78350F; font-size: 13px;">This draft has been submitted to reviewers and is currently in the Review Queue. Reviewers can inspect, comment, or approve it.</div>
        </div>
        """, unsafe_allow_html=True)
    elif current_note.status == "APPROVED":
        st.markdown("""
        <div style="background: #DCFCE7; border: 1px solid #86EFAC; border-left: 5px solid #16A34A; border-radius: 8px; padding: 12px 18px; margin-bottom: 16px;">
            <div style="font-weight: 700; color: #166534; font-size: 14px; margin-bottom: 2px;">🎉 Process Note Approved</div>
            <div style="color: #14532D; font-size: 13px;">This process note has received official sign-off and approval.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #22C55E; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <div style="font-weight: 700; color: #166534; font-size: 14px; margin-bottom: 2px;">
                        🚀 Ready to submit this Process Note for Review?
                    </div>
                    <div style="color: #14532D; font-size: 12.5px;">
                        You can submit anytime for human manual review! The AI checks below are purely optional tips to help polish your draft before submission.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        sub_col1, sub_col2 = st.columns([1.6, 3.4])
        with sub_col1:
            if st.button("🚀 Submit for Manual Review", key="btn_top_submit_manual_review", type="primary", use_container_width=True):
                current_note.status = "UNDER_REVIEW"
                user_name = st.session_state.get("current_user_name", "Creator")
                rev_history = ReviewHistory(
                    process_note_id=current_note.id,
                    process_name=current_note.process_name,
                    reviewer=user_name,
                    action="SUBMITTED",
                    comments="Submitted by creator for manual review.",
                )
                db.add(rev_history)
                db.commit()

                from models.database import User
                from core.notifications import create_notification
                reviewers = db.query(User).filter(User.role == "reviewer").all()
                msg = f"{user_name} has submitted '{current_note.process_name}' (v{current_note.version}) for manual review."
                for r in reviewers:
                    create_notification(db, r.id, msg, current_note.id)

                st.session_state.selected_note_id = current_note.id
                st.toast("Submitted for manual review!", icon="🚀")
                st.rerun()

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
                    status="WARNING",
                    score=75.0,
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

        pass_thresh = float(os.getenv("PASS_THRESHOLD", 75))
        warn_thresh = float(os.getenv("WARNING_THRESHOLD", 65))
        status_class = "badge-pass" if latest_run.status == "PASS" else ("badge-warning" if latest_run.status == "WARNING" else "badge-fail")
        score_bar_class = "score-pass" if latest_run.overall_score >= pass_thresh else ("score-warn" if latest_run.overall_score >= warn_thresh else "score-fail")

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

        st.markdown("### 💡 Draft Consistency Tips Between Sections")
        st.caption("Optional suggestions to ensure timelines, roles, and rules stay aligned across your sections. You can submit your note for manual review anytime!")
        cross_findings = [f for f in findings if f.is_cross_section == 1]
        if cross_findings:
            for f in cross_findings:
                is_resolved = "*(Resolved by Clarification)*" in (f.issue or "")
                display_cr_issue = (f.issue or "").replace("*(Resolved by Clarification)*\n\n", "").replace("*(Resolved by Clarification)*", "")
                clean_sec_label = f.section_id.replace("Cross-Section", "Sections").strip()
                exp_title = f"✅ {clean_sec_label} - Resolved" if is_resolved else f"💡 Suggestion: {clean_sec_label} Alignment"

                with st.expander(exp_title, expanded=False):
                    cr_advice = f.recommendation or ""
                    cr_questions = ""
                    if f.recommendation and "**Clarification Questions for Process Owner:**" in f.recommendation:
                        rec_parts = f.recommendation.split("**Clarification Questions for Process Owner:**")
                        cr_advice = rec_parts[0].strip()
                        cr_questions = rec_parts[1].strip()

                    render_crisp_feedback(display_cr_issue, cr_advice, f.severity or "MEDIUM", cr_questions)

                    # Identify all involved sections for this cross-section finding
                    found_sids = re.findall(r'1\.\d+', str(f.section_id or ""))
                    if not found_sids:
                        found_sids = ["1.12"]
                    # Deduplicate found_sids while preserving order
                    found_sids = list(dict.fromkeys(found_sids))

                    involved_sections = []
                    for sid in found_sids:
                        c_def = next((s for s in sections_config if str(s.get("id")) == sid), None)
                        s_obj = next((s for s in current_note.sections if str(s.section_id) == sid), None)
                        if c_def:
                            involved_sections.append((c_def, s_obj))

                    st.markdown("---")

                    # Direct Section Content Editor (Primary Action)
                    st.markdown('<div style="font-weight: 700; font-size: 14px; color: #1E293B; margin-bottom: 6px;">✏️ Edit Section Content Directly (In-Place)</div>', unsafe_allow_html=True)
                    st.caption("You can directly edit the table cells, text, or flowchart for any involved section below:")

                    if len(involved_sections) == 1:
                        c_def, s_obj = involved_sections[0]
                        render_inline_section_editor(c_def, s_obj, current_note, db, key_suffix=f"cr_{f.id}_{c_def['id']}")
                    elif len(involved_sections) > 1:
                        tab_titles = [f"✏️ Section {c['id']} ({c['name']})" for c, _ in involved_sections]
                        sec_tabs = st.tabs(tab_titles)
                        for t_idx, (c_def, s_obj) in enumerate(involved_sections):
                            with sec_tabs[t_idx]:
                                render_inline_section_editor(c_def, s_obj, current_note, db, key_suffix=f"cr_{f.id}_{c_def['id']}")

                    # Optional AI Assistant Helper (Toggled cleanly to avoid Streamlit nested expander exception)
                    if not is_resolved and involved_sections:
                        st.markdown("---")
                        show_cr_ai = st.toggle("🤖 Need AI help updating a section based on your prompt?", key=f"toggle_cr_ai_{f.id}", value=False)
                        if show_cr_ai:
                            st.caption("Type your operational explanation below. AI will automatically incorporate your updates into the chosen section.")

                            sec_labels = [f"Section {c['id']} ({c['name']})" for c, _ in involved_sections]
                            sel_col1, sel_col2 = st.columns([1.5, 2.5])
                            with sel_col1:
                                target_sec_label = st.selectbox("Target Section to update:", sec_labels, key=f"cr_target_sec_{f.id}")
                                chosen_idx = sec_labels.index(target_sec_label)
                                chosen_cfg, chosen_sec_obj = involved_sections[chosen_idx]

                            with sel_col2:
                                cr_ans = st.text_area("Your response / clarification notes:", key=f"cr_ans_{f.id}", height=75, placeholder="e.g. Specify responsible roles, TAT, or step procedures...")

                            if st.button(f"✨ Have AI Update Section {chosen_cfg['id']}", key=f"btn_apply_cr_{f.id}", type="primary"):
                                if not cr_ans.strip():
                                    st.warning("Please enter your clarification response.")
                                else:
                                    with st.spinner(f"AI is incorporating your explanation into Section {chosen_cfg['id']}..."):
                                        from services.llm_service import get_llm_provider
                                        llm = get_llm_provider()
                                        target_sec = db.query(ProcessSection).filter(ProcessSection.process_note_id == current_note.id, ProcessSection.section_id == chosen_cfg['id']).first()
                                        sec_type = chosen_cfg.get("type", "table")
                                        curr_cont = target_sec.structured_data if sec_type == "table" else (target_sec.content if target_sec else "")
                                        if target_sec:
                                            updated_data = llm.resolve_clarification(chosen_cfg['id'], sec_type, curr_cont, display_cr_issue, cr_ans)
                                            if sec_type == "table":
                                                target_sec.structured_data = updated_data
                                                flag_modified(target_sec, "structured_data")
                                            else:
                                                target_sec.content = updated_data
                                            f.status = "PASS"
                                            f.severity = "LOW"
                                            f.issue = f"*(Resolved by Clarification)*\n\n{f.issue}"
                                            db.commit()
                                            st.success(f"✅ AI successfully updated Section {chosen_cfg['id']}! ⚠️ Click 'Run AI Validation' above to re-evaluate.")
                                            st.rerun()
        else:
            st.success("✅ No cross-section gaps found. Business rules, KPIs, flowchart, and RACI are fully aligned with Process Description.")

        def recompute_latest_run_score(run_obj, note_obj):
            all_f = db.query(ValidationFinding).filter(ValidationFinding.validation_id == run_obj.id).all()
            sec_f = [res for res in all_f if res.is_cross_section == 0]
            total_score = sum([res.score for res in sec_f])
            num_sections = len(sec_f)
            raw_score = (total_score / num_sections) if num_sections > 0 else 0.0
            run_obj.overall_score = max(0.0, round(raw_score, 1))
            pass_threshold = float(os.getenv("PASS_THRESHOLD", 75))
            warning_threshold = float(os.getenv("WARNING_THRESHOLD", 65))
            if run_obj.overall_score >= pass_threshold:
                run_obj.status = "PASS"
            elif run_obj.overall_score >= warning_threshold:
                run_obj.status = "WARNING"
            else:
                run_obj.status = "NEEDS_REVISION"
            note_obj.status = run_obj.status
            db.commit()

        st.markdown("### Section-by-Section Findings")
        sec_findings = [f for f in findings if f.is_cross_section == 0]

        for f in sec_findings:
            is_manual = "*(Marked as OK by User)*" in (f.issue or "") or "*(Resolved by Clarification)*" in (f.issue or "") or "*(Resolved by Auto-Correction)*" in (f.issue or "")
            display_issue = (f.issue or "").replace("*(Marked as OK by User)*\n\n", "").replace("*(Marked as OK by User)*", "").replace("*(Resolved by Clarification)*\n\n", "").replace("*(Resolved by Clarification)*", "").replace("*(Resolved by Auto-Correction)*\n\n", "").replace("*(Resolved by Auto-Correction)*", "")

            badge_cls = "badge-pass" if f.status == "PASS" else ("badge-warning" if f.status == "WARNING" else "badge-fail")
            badge_text = "PASS (Resolved)" if is_manual else f.status
            badge_html = f"<span class='badge {badge_cls}'>{badge_text}</span>"

            if is_manual:
                status_emoji = "✅ PASS (Resolved)"
            else:
                status_emoji = "✅ PASS" if f.status == "PASS" else ("⚠️ WARNING" if f.status == "WARNING" else "❌ NEEDS REVISION")

            is_flagged_by_reviewer = f.section_id in flagged_review_sids
            if is_flagged_by_reviewer:
                exp_label = f"🚨 {f.section_id} (Score: {f.score}) - 🔴 REVIEWER FLAGGED - {status_emoji}"
            else:
                exp_label = f"{f.section_id} (Score: {f.score}) - {status_emoji}"

            with st.expander(exp_label, expanded=is_flagged_by_reviewer):
                if is_flagged_by_reviewer:
                    st.markdown("""
                    <div style="background: #FFF1F2; border-left: 5px solid #E11D48; border-radius: 4px; padding: 8px 12px; margin-bottom: 12px; color: #9F1239; font-weight: 700; font-size: 13px;">
                        🚨 Reviewer has specifically requested changes on this section.
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown(f"**Status:** {badge_html}", unsafe_allow_html=True)
                advice = f.recommendation or ""
                questions = ""
                if f.recommendation and "**Clarification Questions for Process Owner:**" in f.recommendation:
                    rec_parts = f.recommendation.split("**Clarification Questions for Process Owner:**")
                    advice = rec_parts[0].strip()
                    questions = rec_parts[1].strip()

                if display_issue.strip() or advice.strip() or questions.strip():
                    render_crisp_feedback(display_issue, advice, f.severity, questions)
                else:
                    st.markdown("""
                    <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4.5px solid #22C55E; border-radius: 8px; padding: 10px 14px; margin: 8px 0; color: #166534; font-size: 13px; font-weight: 600;">
                        ✅ Section looks good. Fully compliant with enterprise process note standards.
                    </div>
                    """, unsafe_allow_html=True)

                needs_polish_or_fix = (f.score < 100 or f.status != "PASS" or bool(display_issue.strip()) or bool(advice.strip())) and not is_manual

                if needs_polish_or_fix:
                    sec_def = next((s for s in sections_config if str(s.get("id")) == str(f.section_id) or str(s.get("name")) == str(f.section_id) or str(f.section_id).startswith(str(s.get("id")))), None)
                    t_sec_id = sec_def.get("id") if sec_def else f.section_id.split(" ")[0].replace("-", "").strip()
                    target_sec = db.query(ProcessSection).filter(ProcessSection.process_note_id == current_note.id, ProcessSection.section_id == t_sec_id).first()

                    if st.button("Mark as OK (Ignore Feedback)", key=f"ignore_{f.id}"):
                        f.score = 100.0 if f.score < 100 else f.score
                        f.status = "PASS"
                        f.severity = "LOW"
                        f.issue = f"*(Marked as OK by User)*\n\n{f.issue}" if f.issue else "*(Marked as OK by User)*"
                        db.commit()
                        recompute_latest_run_score(latest_run, current_note)
                        st.rerun()

                    if f.status != "PASS":
                        show_sec_ai = st.toggle("🤖 Need AI help updating this section with your answer?", key=f"toggle_sec_ai_{f.id}", value=False)
                        if show_sec_ai:
                            sec_ans = st.text_area("Your response / missing details for this section:", key=f"ans_sec_{f.id}", height=75)
                            if st.button("✨ Apply Clarification to This Section", key=f"btn_sec_apply_{f.id}", type="primary"):
                                if not sec_ans.strip():
                                    st.warning("Please type your response before applying.")
                                else:
                                    with st.spinner("AI is updating this section..."):
                                        from services.llm_service import get_llm_provider
                                        llm = get_llm_provider()
                                        if target_sec:
                                            s_type = sec_def.get("type", "text") if sec_def else "text"
                                            curr_cont = target_sec.structured_data if s_type == "table" else (target_sec.content or "")
                                            questions_to_use = questions if questions else (display_issue if display_issue else advice)
                                            updated_res = llm.resolve_clarification(t_sec_id, s_type, curr_cont, questions_to_use, sec_ans)
                                            if s_type == "table" and isinstance(updated_res, list):
                                                target_sec.structured_data = updated_res
                                                from sqlalchemy.orm.attributes import flag_modified
                                                flag_modified(target_sec, "structured_data")
                                            else:
                                                target_sec.content = str(updated_res)

                                            f.score = 100.0 if f.score < 100 else f.score
                                            f.status = "PASS"
                                            f.severity = "LOW"
                                            f.issue = f"*(Resolved by Clarification)*\n\n{f.issue}"
                                            db.commit()
                                            recompute_latest_run_score(latest_run, current_note)
                                            st.success(f"Section {t_sec_id} updated with your clarification! Score updated.")
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
                if sec_def:
                    render_inline_section_editor(sec_def, section, current_note, db, key_suffix=f"sec_{f.id}_{true_section_id}")
                else:
                    st.warning(f"Could not load configuration for section {f.section_id}.")
        st.markdown("<br>", unsafe_allow_html=True)
        if current_note.status in ["PASS", "WARNING", "NEEDS_REVISION"]:
            st.info("ℹ️ Your reviewer will inspect this draft in the Review dashboard and can approve it or suggest adjustments.")
            if st.button("Submit for Manual Review", key="btn_bottom_submit_manual_review", type="primary", use_container_width=True):
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
                reviewers = db.query(User).filter(User.role == "reviewer").all()
                user_name = st.session_state.get("current_user_name", "A user")
                msg = f"{user_name} has submitted '{current_note.process_name}' for manual review."
                for r in reviewers:
                    create_notification(db, r.id, msg, current_note.id)

                st.session_state.selected_note_id = current_note.id
                st.success("🎉 Successfully submitted for manual review! Reviewers have been notified.")
                st.rerun()
        elif current_note.status == "UNDER_REVIEW":
            st.info("🕒 **Status: Under Review** — This note has been successfully submitted and is currently in the Review Queue. Reviewers can now inspect, comment, or approve it in the **Review & Sign-Off** hub.")

finally:
    db.close()
