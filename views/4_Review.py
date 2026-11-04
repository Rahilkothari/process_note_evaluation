import streamlit as st
from models.database import SessionLocal, get_db, ProcessNote, ProcessSection, ValidationRun, ValidationFinding, ReviewHistory, User
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
import pandas as pd
from services.export_service import generate_docx
from core.ui_utils import inject_custom_css, render_mermaid_flowchart
from config.guided_questions import clean_heading_hashes
import yaml
import copy
import uuid

import re

def extract_concise_gap(gap_str: str) -> str:
    """Distill verbose cross-section gap text into 1 punchy line with clean HTML bold tags (no stars)."""
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

def simplify_discrepancy(text: str) -> str:
    """Condense repetitive, mechanical, or complex error text into crisp, clean HTML bullets (zero stars)."""
    if not text:
        return ""
    clean_text = text.replace("*(Marked as OK by User)*", "").replace("*(Resolved by Clarification)*", "").strip()

    # 1. Match repeated "Row X: <Field> (is missing|cannot be blank|is empty|required)"
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

    # 2. Format cross-section run-ons with "Specifically: 1) ... ; 2) ..."
    if "Specifically:" in clean_text or "Specifically :" in clean_text:
        parts = re.split(r'Specifically\s*:\s*', clean_text, maxsplit=1)
        details = parts[1].strip()
        raw_points = re.split(r'\s*(?:;\s*)?(?:\d+\))\s*', details)
        clean_points = [p.strip().rstrip(';.') for p in raw_points if p.strip()]
        
        condensed_gaps = [extract_concise_gap(p) for p in clean_points]
        
        sec_m = re.findall(r'1\.\d+', clean_text)
        sec_str = " vs ".join(sorted(list(set(sec_m)))) if sec_m else ""
        header = f"📍 <b>Location:</b> Section {sec_str}\n" if sec_str else ""
        res = f"{header}\n".strip() + "\n" + "\n".join(condensed_gaps)
        return res

    # 3. Flowchart vs Process Description Inconsistency
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

    # 4. RACI Matrix vs Process Description
    if "RACI" in clean_text and ("missing" in clean_text.lower() or "activities" in clean_text.lower()):
        m_acts = re.search(r':\s*([^.]+)', clean_text)
        act_list = (m_acts.group(1).strip() if m_acts else "workflow activities").replace("*", "")
        return f"📍 <b>Location:</b> Section 1.12 (Process Description) vs Section 1.13 (RACI Matrix)\n• <b>Missing Roles:</b> Assign Responsible & Accountable for: <b>{act_list}</b>"

    # 5. General text section issue: Keep first 1-2 concise sentences
    sentences = [s.strip().replace("*", "") for s in re.split(r'\.\s+', clean_text) if s.strip()]
    if len(sentences) > 1:
        return f"• {sentences[0]}.\n• {sentences[1]}."
    return f"• {clean_text.replace('*', '')}"

def resolve_sections_for_finding(finding, note_sections, sec_cfgs):
    """Finds matching ProcessSection model objects for any finding (ID, Name, or Cross-Section)."""
    results = []
    sid_str = str(finding.section_id or "")
    
    # Check if cross-section like "Cross-Section (1.5 & 1.12 & 1.14)"
    found_ids = re.findall(r'1\.\d+', sid_str)
    if found_ids:
        for fid in found_ids:
            cfg = next((s for s in sec_cfgs if s.get("id") == fid), None)
            obj = next((s for s in note_sections if s.section_id == fid), None)
            if cfg and obj:
                results.append((cfg, obj))
        if results:
            return results

    # Single section match by ID or Name
    cfg = next((s for s in sec_cfgs if s.get("id") == sid_str or s.get("name", "").lower() == sid_str.lower()), None)
    if cfg:
        obj = next((s for s in note_sections if s.section_id == cfg["id"]), None)
        if obj:
            results.append((cfg, obj))
            return results

    return results

def render_inline_section_comment_ui(cfg, sec_obj, current_note, db, key_prefix="disc"):
    """Renders live section table/text and an inline Reviewer Comment box directly inside the card."""
    sid = cfg.get("id")
    sname = cfg.get("name")
    stype = cfg.get("type", "text")
    
    if stype == "table":
        t_rows = sec_obj.structured_data or []
        if not t_rows:
            st.info(f"ℹ️ Section {sid} ({sname}) table has no rows.")
        else:
            df_rev = pd.DataFrame(t_rows)
            if "Reviewer Comment" not in df_rev.columns:
                df_rev["Reviewer Comment"] = ""

            disabled_cols = [c for c in df_rev.columns if c != "Reviewer Comment"]
            
            st.caption(f"✏️ **In-Line Row Feedback:** Type specific remarks directly into the **'Reviewer Comment'** column below:")
            
            edited_df = st.data_editor(
                df_rev,
                use_container_width=True,
                disabled=disabled_cols,
                key=f"{key_prefix}_editor_{sid}_{current_note.id}_{len(t_rows)}"
            )
            
            edited_df = edited_df.fillna("")
            raw_data = edited_df.to_dict("records")
            new_data = []
            for row in raw_data:
                clean_row = {}
                for k, v in row.items():
                    if pd.isna(v): clean_row[k] = None
                    elif hasattr(v, 'isoformat'): clean_row[k] = v.isoformat()
                    else: clean_row[k] = v
                new_data.append(clean_row)

            if new_data != sec_obj.structured_data:
                sec_obj.structured_data = new_data
                flag_modified(sec_obj, "structured_data")
                db.add(sec_obj)
                db.commit()
                st.toast(f"✅ Saved comment for Section {sid}!", icon="💾")

        # Overall section remark box
        rem_col1, rem_col2 = st.columns([8, 2])
        with rem_col1:
            rem_val = st.text_input(
                f"Overall Section Remark for Section {sid}:",
                placeholder=f"e.g., Row 1 & 2 need specific control descriptions before approval.",
                key=f"{key_prefix}_tbl_rem_{sid}_{sec_obj.id}",
                label_visibility="collapsed"
            )
        with rem_col2:
            if st.button("💾 Save Remark", key=f"{key_prefix}_btn_tbl_{sid}_{sec_obj.id}", use_container_width=True):
                if rem_val.strip():
                    rev_rec = ReviewHistory(
                        process_note_id=current_note.id,
                        process_name=current_note.process_name,
                        reviewer=st.session_state.get("current_user_name") or "Reviewer",
                        action="COMMENTED",
                        comments=f"[Section {sid} - {sname}]: {rem_val.strip()}"
                    )
                    db.add(rev_rec)
                    db.commit()
                    st.toast(f"✅ Remark saved for Section {sid}!", icon="💾")
                    st.rerun()

    elif stype in ["flowchart", "file"]:
        mermaid_src = sec_obj.content or ""
        if "graph " in mermaid_src or "flowchart " in mermaid_src:
            render_mermaid_flowchart(mermaid_src, show_code_toggle=False)
        elif mermaid_src.endswith(('.png', '.jpg', '.jpeg')):
            import os
            img_path = os.path.join("uploads", mermaid_src)
            if os.path.exists(img_path):
                st.image(img_path, caption=mermaid_src, use_container_width=True)
            else:
                st.info(f"Uploaded diagram: {mermaid_src}")
        else:
            st.info("No flowchart diagram data available.")
            
        rem_col1, rem_col2 = st.columns([8, 2])
        with rem_col1:
            rem_val = st.text_input(
                f"Remark for Section {sid}:",
                placeholder="e.g., Please add decision diamonds for the approval gate.",
                key=f"{key_prefix}_diag_rem_{sid}_{sec_obj.id}",
                label_visibility="collapsed"
            )
        with rem_col2:
            if st.button("💾 Save Remark", key=f"{key_prefix}_btn_diag_{sid}_{sec_obj.id}", use_container_width=True):
                if rem_val.strip():
                    rev_rec = ReviewHistory(
                        process_note_id=current_note.id,
                        process_name=current_note.process_name,
                        reviewer=st.session_state.get("current_user_name") or "Reviewer",
                        action="COMMENTED",
                        comments=f"[Section {sid} - {sname}]: {rem_val.strip()}"
                    )
                    db.add(rev_rec)
                    db.commit()
                    st.toast(f"✅ Remark saved for Section {sid}!", icon="💾")
                    st.rerun()
    else:
        # Text/narrative section
        clean_txt = clean_heading_hashes(sec_obj.content or "", sid, sname)
        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; font-size: 13px; color: #334155; max-height: 200px; overflow-y: auto; margin-bottom: 8px; white-space: pre-wrap;">
            {clean_txt}
        </div>
        """, unsafe_allow_html=True)
        
        rem_col1, rem_col2 = st.columns([8, 2])
        with rem_col1:
            rem_val = st.text_input(
                f"Remark for Section {sid}:",
                placeholder=f"e.g., Needs more operational detail regarding the entry criteria.",
                key=f"{key_prefix}_text_rem_{sid}_{sec_obj.id}",
                label_visibility="collapsed"
            )
        with rem_col2:
            if st.button("💾 Save Remark", key=f"{key_prefix}_btn_save_{sid}_{sec_obj.id}", use_container_width=True):
                if rem_val.strip():
                    rev_rec = ReviewHistory(
                        process_note_id=current_note.id,
                        process_name=current_note.process_name,
                        reviewer=st.session_state.get("current_user_name") or "Reviewer",
                        action="COMMENTED",
                        comments=f"[Section {sid} - {sname}]: {rem_val.strip()}"
                    )
                    db.add(rev_rec)
                    db.commit()
                    st.toast(f"✅ Remark saved for Section {sid}!", icon="💾")
                    st.rerun()

    # Show previous remarks if any
    prev_remarks = db.query(ReviewHistory).filter(
        ReviewHistory.process_note_id == current_note.id,
        ReviewHistory.action == "COMMENTED",
        ReviewHistory.comments.like(f"[Section {sid}%")
    ).order_by(ReviewHistory.timestamp.desc()).all()
    if prev_remarks:
        st.markdown("<div style='font-size: 11.5px; font-weight: 700; color: #4338CA; margin-top: 6px;'>💬 Previous Reviewer Remarks on this Section:</div>", unsafe_allow_html=True)
        for pr in prev_remarks[:3]:
            st.markdown(f"""
            <div style="background: #EEF2FF; border-left: 3px solid #6366F1; padding: 5px 10px; border-radius: 4px; font-size: 12px; color: #312E81; margin-top: 4px;">
                <strong>{pr.reviewer or 'Reviewer'}</strong> <span style="color: #6366F1; font-size: 11px;">({pr.timestamp.strftime('%b %d, %H:%M') if pr.timestamp else ''})</span>: {pr.comments.split(']: ', 1)[-1] if ']: ' in (pr.comments or '') else pr.comments}
            </div>
            """, unsafe_allow_html=True)

inject_custom_css()

user_email = (st.session_state.user.email if st.session_state.get("user") else "").lower()
current_role = st.session_state.get("current_user_role", "creator")

# Strict Segregation of Duties: ONLY designated reviewers and admins can access Reviewer Hub
if current_role not in ["admin", "reviewer"]:
    st.error("🔒 **Access Denied**: You do not have permissions to access the Reviewer Hub. This page is strictly reserved for Designated Reviewers and Governance Admins.")
    st.info("💡 As a Process Creator, you can view your notes and audit results from the **Dashboard** and **Validation & Audit** tabs.")
    st.stop()

# Header
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid #E2E8F0;">
    <div>
        <h2 style="margin: 0; font-size: 24px; font-weight: 700; color: #0F172A;">📋 Process Note Review & Approval Hub</h2>
        <span style="color: #64748B; font-size: 13.5px;">Institutional Quality Assurance, Segregation of Duties & Managerial Sign-Off</span>
    </div>
    <div style="font-size: 12px; font-weight: 600; color: #4338CA; background: #EEF2FF; border: 1px solid #C7D2FE; padding: 4px 12px; border-radius: 20px;">
        Reviewer Suite • 22 Sections
    </div>
</div>
""", unsafe_allow_html=True)

db: Session = SessionLocal()
try:
    # Top Status Filter
    col_f1, col_f2 = st.columns([2.5, 7.5])
    with col_f1:
        filter_status = st.selectbox(
            "Filter Queue",
            ["Pending Review (Under Review)", "Active Notes (Drafts & Revisions)", "Approved Notes", "All Notes"],
            index=0,
            label_visibility="collapsed"
        )

    # Query notes based on filter
    if filter_status == "Pending Review (Under Review)":
        query_statuses = ["UNDER_REVIEW"]
    elif filter_status == "Active Notes (Drafts & Revisions)":
        query_statuses = ["DRAFT", "NEEDS_REVISION", "WARNING", "PASS", "UNDER_REVIEW"]
    elif filter_status == "Approved Notes":
        query_statuses = ["APPROVED"]
    else:
        query_statuses = ["UNDER_REVIEW", "APPROVED", "DRAFT", "NEEDS_REVISION", "WARNING", "PASS", "ARCHIVED"]

    notes = db.query(ProcessNote).filter(ProcessNote.status.in_(query_statuses)).order_by(ProcessNote.updated_at.desc()).all()

    if not notes:
        st.info(f"ℹ️ No process notes found matching filter: **{filter_status}**.")
        if filter_status == "Pending Review (Under Review)":
            st.caption("💡 Tip: Select 'Active Notes' or 'All Notes' above to review draft process notes or previous releases.")
        st.stop()

    note_options = {
        f"[{n.id}] {n.process_name} (v{n.version}) • {n.team or 'Operations'} • {n.status.replace('_', ' ')}": n.id
        for n in notes
    }

    # Pre-select note if in session
    note_keys = list(note_options.keys())
    default_idx = 0
    if "selected_note_id" in st.session_state:
        for idx, (lbl, nid) in enumerate(note_options.items()):
            if nid == st.session_state.selected_note_id:
                default_idx = idx
                break

    with col_f2:
        selected_label = st.selectbox("Select Process Note to Review", note_keys, index=default_idx, label_visibility="collapsed")
        selected_id = note_options[selected_label]
        st.session_state.selected_note_id = selected_id

    current_note = db.query(ProcessNote).filter(ProcessNote.id == selected_id).first()
    if not current_note:
        st.error("Selected note could not be retrieved.")
        st.stop()

    # Load Sections Configuration
    with open("config/sections.yaml", "r", encoding="utf-8") as f_yaml:
        sections_config = yaml.safe_load(f_yaml).get("sections", [])
    total_sections_count = len(sections_config)

    # Calculate status badge
    st_val = current_note.status.replace('_', ' ')
    if current_note.status == "APPROVED":
        status_badge_html = '<span style="background: #DCFCE7; color: #166534; font-size: 11.5px; font-weight: 700; padding: 4px 12px; border-radius: 12px; border: 1px solid #86EFAC;">✓ APPROVED</span>'
    elif current_note.status == "UNDER_REVIEW":
        status_badge_html = '<span style="background: #FEF3C7; color: #92400E; font-size: 11.5px; font-weight: 700; padding: 4px 12px; border-radius: 12px; border: 1px solid #FDE68A;">⏳ UNDER REVIEW</span>'
    elif current_note.status in ["NEEDS_REVISION", "WARNING"]:
        status_badge_html = f'<span style="background: #FEE2E2; color: #991B1B; font-size: 11.5px; font-weight: 700; padding: 4px 12px; border-radius: 12px; border: 1px solid #FCA5A5;">⚠️ {st_val}</span>'
    else:
        status_badge_html = f'<span style="background: #F1F5F9; color: #475569; font-size: 11.5px; font-weight: 700; padding: 4px 12px; border-radius: 12px; border: 1px solid #CBD5E1;">📝 {st_val}</span>'

    # Executive Note Summary Card
    st.markdown(f"""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <div>
                <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Reviewing Process Note:</span>
                <div style="font-size: 18px; font-weight: 700; color: #1E293B; margin-top: 2px;">{current_note.process_name}</div>
                <div style="font-size: 13px; color: #64748B; margin-top: 2px;">Version {current_note.version} &bull; Team: <strong>{current_note.team}</strong></div>
            </div>
            <div style="text-align: right;">
                {status_badge_html}
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 12.5px;">
            <div><span style="color: #64748B;">Process Owner:</span><br><strong>{current_note.process_owner or 'Not Assigned'}</strong></div>
            <div><span style="color: #64748B;">Process Approver:</span><br><strong>{current_note.process_approver or 'Not Assigned'}</strong></div>
            <div><span style="color: #64748B;">Reviewer Assigned:</span><br><strong>{current_note.process_reviewer or 'Business Excellence'}</strong></div>
            <div><span style="color: #64748B;">Effective Date:</span><br><strong>{current_note.effective_date or 'TBD'}</strong></div>
            <div><span style="color: #64748B;">Review Cycle:</span><br><strong>{current_note.next_review_date or 'Annual'}</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3 Main Tabs
    tab1, tab2, tab3 = st.tabs(["📝 Reviewer Sign-Off & Actions", "🛡️ AI Governance & Quality Audit", "📖 Full 22 Sections Review"])

    # -------------------------------------------------------------
    # TAB 1: REVIEWER SIGN-OFF & ACTIONS
    # -------------------------------------------------------------
    with tab1:
        st.markdown("<div style='font-weight: 700; font-size: 15px; color: #1E293B; margin-bottom: 8px;'>Managerial Determination:</div>", unsafe_allow_html=True)

        if current_note.status in ["UNDER_REVIEW", "NEEDS_REVISION", "WARNING", "DRAFT", "PASS"]:
            with st.form(f"review_action_form_{current_note.id}"):
                c_act1, c_act2 = st.columns([1, 1])
                with c_act1:
                    decision = st.radio(
                        "Select Review Decision:",
                        ["✅ Approve & Officially Release Process Note", "🔄 Request Revisions & Return to Creator"],
                        index=0
                    )
                with c_act2:
                    st.markdown("""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 12.5px; color: #475569;">
                        <b>Governance Guidelines:</b><br>
                        • <b>Approve:</b> Formally seals the note as institutional SOP. Ingests into RAG and clears internal review marks.<br>
                        • <b>Request Revisions:</b> Generates a revised version draft (e.g., v1.1) and returns to creator with your specific notes.
                    </div>
                    """, unsafe_allow_html=True)

                reviewer_comments = st.text_area(
                    "Reviewer Comments & Executive Guidance for the Creator:",
                    placeholder="e.g., Process looks solid. Approved with minor clarification on Turnaround Time targets in Section 1.5.",
                    height=100
                )

                submit_decision = st.form_submit_button("🚀 Submit Final Decision", type="primary", use_container_width=True)

                if submit_decision:
                    reviewer_name = st.session_state.get("current_user_name") or user_email.split("@")[0].title() or "Designated Reviewer"

                    if "approve" in decision.lower():
                        current_note.status = "APPROVED"
                        action_val = "APPROVED"

                        # Clear internal reviewer draft comments upon formal approval
                        for s in current_note.sections:
                            if s.structured_data:
                                mod = False
                                for row in s.structured_data:
                                    if "Reviewer Comment" in row:
                                        del row["Reviewer Comment"]
                                        mod = True
                                if mod:
                                    flag_modified(s, "structured_data")
                                    db.add(s)

                        # Background RAG ingestion
                        def ingest_rag_bg(n_id, team_str, sec_list):
                            from services.rag_service import rag_service
                            for s_id, s_cont in sec_list:
                                try:
                                    rag_service.ingest_section(note_id=n_id, team=team_str, section_id=s_id, content=s_cont)
                                except Exception:
                                    pass

                        import threading, json
                        secs_to_ingest = []
                        for s in current_note.sections:
                            cont = s.content or (json.dumps(s.structured_data) if s.structured_data else "")
                            if cont and cont != "[]":
                                secs_to_ingest.append((s.section_id, cont))
                        threading.Thread(target=ingest_rag_bg, args=(current_note.id, current_note.team, secs_to_ingest)).start()

                        # Record History
                        rev_rec = ReviewHistory(
                            process_note_id=current_note.id,
                            process_name=current_note.process_name,
                            reviewer=reviewer_name,
                            action=action_val,
                            comments=reviewer_comments or "Formally approved by reviewer."
                        )
                        db.add(rev_rec)
                        db.commit()

                        from core.notifications import create_notification
                        if current_note.created_by:
                            create_notification(db, current_note.created_by, f"🎉 Congratulations! Reviewer {reviewer_name} has officially APPROVED your process note '{current_note.process_name}'.", current_note.id)

                        st.success(f"🎉 Process Note '{current_note.process_name}' has been officially APPROVED!")
                        st.cache_data.clear()
                        st.rerun()

                    else:
                        # Send back for revision: create new version draft
                        if not current_note.document_id:
                            current_note.document_id = str(uuid.uuid4())

                        current_note.status = "ARCHIVED"
                        try:
                            v_num = float(current_note.version)
                            new_v = f"{v_num + 0.1:.1f}"
                        except Exception:
                            new_v = current_note.version + "_revised"

                        new_note = ProcessNote(
                            document_id=current_note.document_id,
                            process_name=current_note.process_name,
                            team=current_note.team,
                            version=new_v,
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
                        for s in current_note.sections:
                            ns = ProcessSection(
                                process_name=new_note.process_name,
                                section_id=s.section_id,
                                content=s.content,
                                structured_data=copy.deepcopy(s.structured_data) if s.structured_data else None
                            )
                            new_sections.append(ns)
                        new_note.sections = new_sections
                        db.add(new_note)
                        db.flush()

                        final_sent_back_comments = (reviewer_comments if (reviewer_comments and reviewer_comments.strip()) else (
                            "\n".join([f"• {h.comments}" for h in db.query(ReviewHistory).filter(ReviewHistory.process_note_id == current_note.id, ReviewHistory.action == "COMMENTED").all() if h.comments]) or "Revisions requested by reviewer."
                        ))

                        # Record History on both current note and new note
                        rev_rec_old = ReviewHistory(
                            process_note_id=current_note.id,
                            process_name=current_note.process_name,
                            reviewer=reviewer_name,
                            action="SENT_BACK",
                            comments=final_sent_back_comments
                        )
                        db.add(rev_rec_old)

                        rev_rec_new = ReviewHistory(
                            process_note_id=new_note.id,
                            process_name=new_note.process_name,
                            reviewer=reviewer_name,
                            action="SENT_BACK",
                            comments=final_sent_back_comments
                        )
                        db.add(rev_rec_new)

                        # Forward previous section remarks to the new note
                        commented_records = db.query(ReviewHistory).filter(
                            ReviewHistory.process_note_id == current_note.id,
                            ReviewHistory.action == "COMMENTED"
                        ).all()
                        for cr in commented_records:
                            db.add(ReviewHistory(
                                process_note_id=new_note.id,
                                process_name=new_note.process_name,
                                reviewer=cr.reviewer,
                                action=cr.action,
                                comments=cr.comments,
                                timestamp=cr.timestamp
                            ))

                        db.commit()

                        from core.notifications import create_notification
                        if current_note.created_by:
                            create_notification(db, current_note.created_by, f"📝 Reviewer {reviewer_name} requested revisions on '{current_note.process_name}'. A new draft (v{new_v}) is ready for your updates.", new_note.id)

                        st.success(f"✅ Revisions requested! Draft version {new_v} has been created and sent back to the creator.")
                        st.cache_data.clear()
                        st.rerun()

        elif current_note.status == "APPROVED":
            st.markdown("""
            <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 10px; padding: 18px 22px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">🎉</span>
                    <div>
                        <div style="font-weight: 700; color: #166534; font-size: 16px;">This Process Note is Officially Approved and Released!</div>
                        <div style="color: #15803D; font-size: 13px; margin-top: 3px;">The document complies with all Business Excellence standards and is indexed in the organizational knowledge repository.</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_doc1, col_doc2 = st.columns([1.5, 3.5])
            with col_doc1:
                @st.cache_data(show_spinner=False)
                def get_cached_docx_bytes(n_id, up_time, _note):
                    return generate_docx(_note).getvalue()

                docx_bytes = get_cached_docx_bytes(current_note.id, str(current_note.updated_at), current_note)
                st.download_button(
                    "📥 Export Official Process Note (.docx)",
                    data=docx_bytes,
                    file_name=f"{current_note.process_name.replace(' ', '_')}_v{current_note.version}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )
            with col_doc2:
                if st.button("⚠️ Revert Approval (Reopen for Review)", type="secondary", use_container_width=False):
                    current_note.status = "UNDER_REVIEW"
                    reviewer_name = st.session_state.get("current_user_name") or "Reviewer"
                    db.add(ReviewHistory(
                        process_note_id=current_note.id,
                        process_name=current_note.process_name,
                        reviewer=reviewer_name,
                        action="REVERTED_APPROVAL",
                        comments="Approval reverted by reviewer for administrative corrections."
                    ))
                    db.commit()
                    st.cache_data.clear()
                    st.rerun()

    # -------------------------------------------------------------
    # TAB 2: AI GOVERNANCE & QUALITY AUDIT FINDINGS
    # -------------------------------------------------------------
    with tab2:
        latest_run = db.query(ValidationRun).filter(ValidationRun.process_note_id == current_note.id).order_by(ValidationRun.timestamp.desc()).first()

        if not latest_run:
            st.info("ℹ️ No automated validation run is recorded yet for this note. Creators can run AI Validation from the Validation & Audit tab.")
        else:
            score = latest_run.overall_score or 0.0
            score_color = "#16A34A" if score >= 75 else ("#EA580C" if score >= 65 else "#DC2626")

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                <div>
                    <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;">Automated Audit Result:</span>
                    <div style="font-size: 22px; font-weight: 800; color: {score_color}; margin-top: 2px;">{score:.1f}% Quality Score</div>
                    <div style="font-size: 12.5px; color: #64748B;">Audit Run Date: {latest_run.timestamp.strftime('%B %d, %Y at %I:%M %p') if latest_run.timestamp else 'Recent'}</div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 13px; font-weight: 700; padding: 5px 14px; border-radius: 20px; background: {'#DCFCE7' if score >= 75 else '#FEF3C7' if score >= 65 else '#FEE2E2'}; color: {'#166534' if score >= 75 else '#92400E' if score >= 65 else '#991B1B'}; border: 1px solid {'#86EFAC' if score >= 75 else '#FDE68A' if score >= 65 else '#FCA5A5'};">
                        {latest_run.status}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            findings = db.query(ValidationFinding).filter(ValidationFinding.validation_id == latest_run.id).all()

            # Filter to ONLY actual discrepancies (status != PASS and issue is not blank)
            real_discrepancies = [
                f for f in findings
                if (f.issue and f.issue.strip()) and (f.status in ["NEEDS_REVISION", "WARNING", "FAIL"] or "*(Marked as OK by User)*" in (f.issue or ""))
            ]

            pass_count = len([f for f in findings if f.status == "PASS" and (not f.issue or not f.issue.strip() or "*(Marked as OK by User)*" in (f.issue or ""))])

            st.markdown(f'''
            <div style="display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap;">
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 700; color: #166534;">
                    ✅ {pass_count} Sections Fully Compliant
                </div>
                <div style="background: {'#FEF2F2' if any(f.severity == 'HIGH' or f.status == 'NEEDS_REVISION' for f in real_discrepancies) else '#F8FAFC'}; border: 1px solid {'#FECACA' if any(f.severity == 'HIGH' or f.status == 'NEEDS_REVISION' for f in real_discrepancies) else '#E2E8F0'}; border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 700; color: {'#991B1B' if any(f.severity == 'HIGH' or f.status == 'NEEDS_REVISION' for f in real_discrepancies) else '#64748B'};">
                    🔴 {len([f for f in real_discrepancies if f.severity == 'HIGH' or f.status == 'NEEDS_REVISION'])} Critical Blockers
                </div>
                <div style="background: {'#FFFBEB' if any(f.severity != 'HIGH' and f.status != 'NEEDS_REVISION' for f in real_discrepancies) else '#F8FAFC'}; border: 1px solid {'#FDE68A' if any(f.severity != 'HIGH' and f.status != 'NEEDS_REVISION' for f in real_discrepancies) else '#E2E8F0'}; border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 700; color: {'#92400E' if any(f.severity != 'HIGH' and f.status != 'NEEDS_REVISION' for f in real_discrepancies) else '#64748B'};">
                    🟡 {len([f for f in real_discrepancies if f.severity != 'HIGH' and f.status != 'NEEDS_REVISION'])} Advisory Notices
                </div>
            </div>
            ''', unsafe_allow_html=True)

            if not real_discrepancies:
                st.success("🎉 Excellent! All 22 sections meet Business Excellence standards with 0 discrepancies detected.")
            else:
                for idx, f in enumerate(real_discrepancies, 1):
                    is_ok_user = "*(Marked as OK by User)*" in (f.issue or "")
                    clean_issue = (f.issue or "").replace("*(Marked as OK by User)*\n\n", "").replace("*(Marked as OK by User)*", "").strip()

                    is_critical = (f.severity == "HIGH" or f.status in ["NEEDS_REVISION", "FAIL"])
                    status_badge = "🟢 Resolved by Creator" if is_ok_user else ("🔴 Critical Discrepancy" if is_critical else "🟡 Advisory Notice")

                    with st.expander(f"Discrepancy {idx}: {f.section_id or 'General Governance'} • {status_badge}", expanded=is_critical):
                        # 1. Crisp 'What to Check' box (strictly clean, zero raw stars)
                        crisp_info = simplify_discrepancy(clean_issue)
                        clean_html_info = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', crisp_info)
                        clean_html_info = clean_html_info.replace('*', '').replace(chr(10), '<br>')
                        
                        st.markdown(f"""
                        <div style="background: {'#FEF2F2' if is_critical else '#FFFBEB'}; border-left: 4px solid {'#EF4444' if is_critical else '#F59E0B'}; padding: 12px 16px; border-radius: 6px; margin-bottom: 12px;">
                            <div style="font-weight: 700; font-size: 12px; color: {'#991B1B' if is_critical else '#92400E'}; margin-bottom: 6px; letter-spacing: 0.04em; text-transform: uppercase;">
                                🔍 What to Check & Verify:
                            </div>
                            <div style="color: #1E293B; font-size: 13.5px; line-height: 1.55;">
                                {clean_html_info}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Only show clean action guidance if any (never dump author essay questions on reviewer)
                        clean_advice = (f.recommendation or "").split("**Clarification Questions")[0].strip()
                        if clean_advice:
                            st.markdown(f"""
                            <div style="font-size: 12px; color: #475569; margin: -6px 0 10px 0; background: #F8FAFC; border-left: 3px solid #94A3B8; padding: 6px 12px; border-radius: 4px;">
                                💡 <b>Guidance:</b> {clean_advice.replace(chr(10), ' ')}
                            </div>
                            """, unsafe_allow_html=True)

                        # 2. Section Details & In-Line Reviewer Comments
                        matched_sections = resolve_sections_for_finding(f, current_note.sections, sections_config)
                        
                        if matched_sections:
                            st.markdown("<div style='font-weight: 700; font-size: 13px; color: #1E293B; margin: 12px 0 6px 0;'>📋 Section Details & In-Line Feedback:</div>", unsafe_allow_html=True)
                            if len(matched_sections) > 1:
                                sec_tabs = st.tabs([f"Sec {m_cfg['id']} ({m_cfg['name']})" for m_cfg, _ in matched_sections])
                                for t_idx, (m_cfg, m_sec_obj) in enumerate(matched_sections):
                                    with sec_tabs[t_idx]:
                                        render_inline_section_comment_ui(m_cfg, m_sec_obj, current_note, db, key_prefix=f"disc_{f.id}_{m_cfg['id']}")
                            else:
                                m_cfg, m_sec_obj = matched_sections[0]
                                render_inline_section_comment_ui(m_cfg, m_sec_obj, current_note, db, key_prefix=f"disc_{f.id}")
                        else:
                            st.caption("ℹ️ Section content is currently empty.")


    # -------------------------------------------------------------
    # TAB 3: FULL 22 SECTIONS REVIEW
    # -------------------------------------------------------------
    with tab3:
        filled_sections = {s.section_id: s for s in current_note.sections}

        # Navigation bar for section review
        col_nav_l, col_nav_r = st.columns([7, 3])
        with col_nav_r:
            view_mode = st.radio("Display Mode", ["Step-by-Step Navigator", "Continuous All Sections"], horizontal=True, label_visibility="collapsed")

        tab_sec_options = [f"{s['id']} {s['name']}" for s in sections_config]

        if "review_active_tab" not in st.session_state or st.session_state.review_active_tab not in tab_sec_options:
            st.session_state.review_active_tab = tab_sec_options[0]

        curr_sec_idx = tab_sec_options.index(st.session_state.review_active_tab)

        if view_mode == "Step-by-Step Navigator":
            col_b1, col_b2, col_b3 = st.columns([1, 6, 1])
            with col_b1:
                if st.button("◀ Prev", key="btn_rev_prev", disabled=(curr_sec_idx == 0), use_container_width=True):
                    st.session_state.review_active_tab = tab_sec_options[curr_sec_idx - 1]
                    st.rerun()
            with col_b3:
                if st.button("Next ▶", key="btn_rev_next", disabled=(curr_sec_idx == total_sections_count - 1), use_container_width=True):
                    st.session_state.review_active_tab = tab_sec_options[curr_sec_idx + 1]
                    st.rerun()
            with col_b2:
                sel_sec_tab = st.selectbox(
                    "Navigate Section",
                    tab_sec_options,
                    index=curr_sec_idx,
                    key="sel_reviewer_section_dropdown",
                    label_visibility="collapsed"
                )
                if sel_sec_tab != st.session_state.review_active_tab:
                    st.session_state.review_active_tab = sel_sec_tab
                    st.rerun()

            sections_to_show = [sections_config[curr_sec_idx]]
        else:
            sections_to_show = sections_config

        # Render sections
        for s_cfg in sections_to_show:
            sid = s_cfg["id"]
            sname = s_cfg["name"]
            stype = s_cfg.get("type", "text")
            sec_obj = filled_sections.get(sid)

            # Determine badge
            has_data = False
            if sec_obj:
                if stype == "table" and sec_obj.structured_data and len(sec_obj.structured_data) > 0:
                    has_data = True
                elif stype in ["flowchart", "file", "text"] and sec_obj.content and str(sec_obj.content).strip():
                    has_data = True

            sec_badge = (
                '<span style="background: #DCFCE7; color: #166534; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 12px; border: 1px solid #86EFAC;">✓ Filled & Active</span>'
                if has_data
                else '<span style="background: #FEF3C7; color: #92400E; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 12px; border: 1px solid #FDE68A;">⏳ Empty / Unfilled</span>'
            )

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 16px; margin-top: 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 15px; font-weight: 700; color: #1E293B;">Section {sid}: {sname}</div>
                <div>{sec_badge}</div>
            </div>
            """, unsafe_allow_html=True)

            if not has_data:
                st.info(f"ℹ️ Section {sid} ({sname}) has not been filled by the creator yet.")
            else:
                if stype == "table":
                    t_rows = sec_obj.structured_data or []
                    df_rev = pd.DataFrame(t_rows)
                    if "Reviewer Comment" not in df_rev.columns:
                        df_rev["Reviewer Comment"] = ""

                    disabled_cols = [c for c in df_rev.columns if c != "Reviewer Comment"]

                    st.caption("💡 Reviewer Tip: You can type specific feedback directly into the **'Reviewer Comment'** column below:")
                    edited_rev_df = st.data_editor(
                        df_rev,
                        use_container_width=True,
                        disabled=disabled_cols,
                        key=f"rev_editor_{sid}_{current_note.id}_{len(t_rows)}"
                    )

                    edited_rev_df = edited_rev_df.fillna("")
                    raw_data = edited_rev_df.to_dict("records")
                    new_data = []
                    for row in raw_data:
                        clean_row = {}
                        for k, v in row.items():
                            if pd.isna(v): clean_row[k] = None
                            elif hasattr(v, 'isoformat'): clean_row[k] = v.isoformat()
                            else: clean_row[k] = v
                        new_data.append(clean_row)

                    if new_data != sec_obj.structured_data:
                        sec_obj.structured_data = new_data
                        flag_modified(sec_obj, "structured_data")
                        db.add(sec_obj)
                        db.commit()

                elif stype in ["flowchart", "file"]:
                    mermaid_src = sec_obj.content or ""
                    if "graph " in mermaid_src or "flowchart " in mermaid_src:
                        render_mermaid_flowchart(mermaid_src, show_code_toggle=True)
                    elif mermaid_src.endswith(('.png', '.jpg', '.jpeg')):
                        import os
                        img_path = os.path.join("uploads", mermaid_src)
                        if os.path.exists(img_path):
                            st.image(img_path, caption=mermaid_src, use_container_width=True)
                        else:
                            st.info(f"Uploaded diagram: {mermaid_src}")
                    else:
                        st.info("No flowchart diagram data available.")

                else:  # text
                    clean_txt = clean_heading_hashes(sec_obj.content or "", sid, sname)
                    st.markdown(f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; line-height: 1.6; color: #334155; font-size: 13.5px;">
                        {clean_txt}
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

finally:
    db.close()
