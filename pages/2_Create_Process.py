import streamlit as st
import yaml
import os
import pandas as pd
import json
from models.database import SessionLocal, get_db, ProcessNote, ProcessSection, User
from sqlalchemy.orm import Session


from core.ui_utils import inject_custom_css
from core.ui_utils import inject_custom_css


st.title("Create / Edit Process Note")
st.markdown("""
<div style="background-color: #FFFBEB; border: 1px solid #FEF3C7; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
    <h4 style="color: #92400E; margin-top: 0;">📝 How to draft your process note:</h4>
    <ol style="color: #92400E; margin-bottom: 0;">
        <li><b>Start by filling out the Basic Information</b> below (Name, Team, SMEs, etc.) and click <b>Next</b>.</li>
        <li><b>Select a Note:</b> If you already started one, select it from the dropdown to continue editing.</li>
        <li><b>Fill Out Sections:</b> Scroll down to the 'Process Details' area. Use the dropdown to jump between sections (e.g. 1.0, 1.1).</li>
        <li><b>Save Often:</b> Make sure to click the <b>Save Section</b> button inside each tab before moving to the next one!</li>
        <li><b>Use AI:</b> Stuck on what to write? Click the <b>✨ Get AI Suggestion</b> button for a head start based on your team's history.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_sections_config():
    with open("config/sections.yaml", "r") as f:
        return yaml.safe_load(f)

config = load_sections_config()
sections = config.get("sections", [])

db: Session = SessionLocal()
try:

    action_options = ["Create New Process Note", "Edit Existing Process Note"]
    default_action_idx = 0
    if st.session_state.get("action_radio") == "Edit Existing Process Note":
        default_action_idx = 1

    action = st.radio("What would you like to do?", action_options, index=default_action_idx, horizontal=True)
    st.session_state["action_radio"] = action
    
    if action == "Create New Process Note":
        current_note = None
    else:
        existing_notes = db.query(ProcessNote).filter(ProcessNote.status.in_(["DRAFT", "NEEDS_REVISION", "WARNING", "PASS"])).order_by(ProcessNote.id.desc()).all()
        if not existing_notes:
            st.info("You don't have any existing drafts to edit.")
            st.stop()
            
        note_options = {}
        for n in existing_notes:
            note_options[f"[{n.id}] {n.process_name} (v{n.version}) - {n.status}"] = n
            
        note_keys = list(note_options.keys())
        default_idx = 0
        if "selected_note_key" in st.session_state:
            try:
                default_idx = note_keys.index(st.session_state.selected_note_key)
            except ValueError:
                pass
                
        selected_option = st.selectbox("Select a Note to Edit", note_keys, index=default_idx)
        current_note = note_options[selected_option]
        st.session_state.selected_note_key = selected_option

    st.markdown("<br>", unsafe_allow_html=True)
    
    if current_note and current_note.status == "NEEDS_REVISION":
        from models.database import ReviewHistory
        latest_review = db.query(ReviewHistory).join(ProcessNote, ReviewHistory.process_note_id == ProcessNote.id).filter(ProcessNote.document_id == current_note.document_id).order_by(ReviewHistory.timestamp.desc()).first()
        if latest_review and latest_review.comments:
            st.error(f"**Reviewer Feedback ({latest_review.reviewer}):**\n\n{latest_review.comments}")
            st.markdown("<br>", unsafe_allow_html=True)

    with st.container():
        st.subheader("Basic Information")
        with st.form("basic_info_form"):
            col1, col2 = st.columns(2)
            with col1:
                process_name = st.text_input("Process Name *", value=current_note.process_name if current_note else "", help="The official name of the process being documented.")
                team = st.text_input("Team *", value=current_note.team if current_note else "", help="The department or team responsible for this process.")
                version = st.text_input("Version Number", value=current_note.version if current_note else "1.0", help="e.g., 1.0 for new, 1.1 for minor updates.")
                subject_matter_expert = st.text_input("Subject Matter Expert", value=current_note.subject_matter_expert if current_note else "", help="The person with deep technical/domain knowledge of this process.")
                process_owner = st.text_input("Process Owner", value=current_note.process_owner if current_note else "", help="The leader ultimately responsible for the execution of this process.")
            with col2:
                process_champion = st.text_input("Process Champion", value=current_note.process_champion if current_note else "", help="The person driving the adoption and improvement of this process.")
                process_reviewer = st.text_input("Process Reviewer", value=current_note.process_reviewer if current_note else "", help="The person responsible for reviewing this document for accuracy.")
                process_approver = st.text_input("Process Approver", value=current_note.process_approver if current_note else "", help="The person who provides final sign-off on this document.")
            
                import datetime
                def parse_date(date_str):
                    if date_str:
                        try:
                            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                        except ValueError:
                            return None
                    return None
                
                eff_date_val = parse_date(current_note.effective_date if current_note else None)
                rev_date_val = parse_date(current_note.next_review_date if current_note else None)
            
                effective_date = st.date_input("Effective Date", value=eff_date_val, help="The date this version of the process goes live.")
                next_review_date = st.date_input("Next Review Date", value=rev_date_val, help="When this document should be reviewed again.")
            
                # Convert date objects back to strings for DB storage
                effective_date = str(effective_date) if effective_date else ""
                next_review_date = str(next_review_date) if next_review_date else ""
        
            st.markdown("<p style='font-size: 13px; color: #64748B; margin-top: 8px;'>* Required fields. <strong>You MUST click the button below to save this information!</strong></p>", unsafe_allow_html=True)
            save_basic = st.form_submit_button("💾 Save Basic Information", type="primary")

    if save_basic:
        if not process_name or not process_name.strip():
            st.error("Process Name is a required field. Please provide it before proceeding.")
            st.stop()
        if not team or not team.strip():
            st.error("Team is a required field. Please provide it before proceeding.")
            st.stop()
        
        # Validation passed
        if current_note is None:
            import uuid
            current_note = ProcessNote(
                document_id=str(uuid.uuid4()),
                process_name=process_name if process_name else "Untitled Process",
                team=team if team else "Unassigned",
                version=version,
                status="DRAFT",
                subject_matter_expert=subject_matter_expert,
                process_owner=process_owner,
                process_champion=process_champion,
                process_reviewer=process_reviewer,
                process_approver=process_approver,
                effective_date=effective_date,
                next_review_date=next_review_date,
                created_by=st.session_state.get("current_user_id")
            )
            db.add(current_note)
            db.commit()
            db.refresh(current_note)
            st.session_state["action_radio"] = "Edit Existing Process Note"
            st.session_state.selected_note_key = f"[{current_note.id}] {current_note.process_name} (v{current_note.version}) - {current_note.status}"
            st.success("Draft created! You can now fill in the 22 sections below.")
            st.rerun()
        else:
            current_note.process_name = process_name if process_name else "Untitled Process"
            current_note.team = team if team else "Unassigned"
            current_note.version = version
            current_note.subject_matter_expert = subject_matter_expert
            current_note.process_owner = process_owner
            current_note.process_champion = process_champion
            current_note.process_reviewer = process_reviewer
            current_note.process_approver = process_approver
            current_note.effective_date = effective_date
            current_note.next_review_date = next_review_date
            db.commit()
            st.success("Basic info updated successfully!")

    st.markdown("<br>", unsafe_allow_html=True)

    if current_note:
        st.subheader("Process Details (Step-by-Step)")
    
        team_lower = current_note.team.lower() if current_note.team else ""
        if "volunteer" in team_lower or "comm" in team_lower:
            st.info(f"💡 **Pre-Submission Checklist:** Review the governance criteria for the **{current_note.team}** team before submitting.")
            with st.expander(f"View {current_note.team} Audit & Governance Guidelines", expanded=False):
                if "volunteer" in team_lower:
                    st.markdown("""
    **Ensure your process note adequately covers:**
    - Types of Volunteering
    - Volunteer onboarding, registration and eligibility criteria.
    - Volunteer allocation/deployment process across programmes and activities.
    - Volunteer engagement, attendance and participation tracking.
    - Roles, responsibilities and reporting structure of volunteers.
    - Volunteer training, orientation and capacity-building process.
    - Volunteer communication, grievance handling and escalation mechanism.
    - Background verification, code of conduct and safeguarding requirements, wherever applicable.
    - Volunteer exit process.
    - Volunteer data management, documentation and records maintained.
    - Monitoring, feedback and performance evaluation of volunteers.
    - Volunteer certification process, including eligibility criteria, assessment/completion requirements, approval and issuance of certificates.
                    """)
                elif "comm" in team_lower:
                    st.markdown("""
    **Ensure your process note adequately covers:**
    - Branding guidelines, brand identity and usage standards across all KEF programmes, offices and communication channels.
    - Brand approval process for logos, creatives, collaterals, signage, merchandise and other branded materials.
    - Communication and marketing strategy, planning and annual activity calendar.
    - Content development, review and approval process for internal and external communications.
    - Social media management, content calendar, posting and monitoring process.
    - Website/content management, including updates and approval controls.
    - Event, campaign and programme communication process.
    - Media engagement, PR, press releases and external communication approvals.
    - Creative/design development process, including agency/vendor coordination.
    - Photography, videography and consent management for use of images, videos and other content.
    - Marketing collateral development, printing and distribution process.
    - Stakeholder communication and coordination with programme/project teams.
    - Communication budget, vendor management and payment/approval process.
    - Roles, responsibilities, approval matrix and escalation mechanism.
    - Records and documentation of campaigns, communications, approvals and performance/MIS.
                    """)
                
        st.markdown("Scroll down to fill out all sections of the process note. **Read the instruction box** in each section before entering data.")
    
        def is_section_filled(sec, s_config):
            if not sec:
                return False
            stype = s_config.get("type", "text")
            if stype == "table":
                if not sec.structured_data:
                    return False
                for row in sec.structured_data:
                    if isinstance(row, dict) and any(v is not None and str(v).strip() != "" for v in row.values()):
                        return True
                return False
            elif stype in ["file", "flowchart"]:
                return bool(sec.content and sec.content.strip())
            else:
                return bool(sec.content and sec.content.strip())

        existing_sections = {s.section_id: s for s in current_note.sections}
        completed_count = sum(1 for s in sections if is_section_filled(existing_sections.get(s['id']), s))
        total_count = len(sections)
    
        st.markdown(f"**Progress:** {completed_count} / {total_count} Sections Completed")
        st.progress(completed_count / total_count)
    
        if "current_section_edit" not in st.session_state:
            st.session_state["current_section_edit"] = f"{sections[0]['id']} {sections[0]['name']}"

        tab_names = [f"{sec['id']} {sec['name']}" for sec in sections]
    
        # Ensure current state is valid
        if st.session_state["current_section_edit"] not in tab_names:
            st.session_state["current_section_edit"] = tab_names[0]
        
        current_idx = tab_names.index(st.session_state["current_section_edit"])

        # Section Navigation Control Bar
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px; margin-bottom: 6px;">
                <span style="font-size: 13px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.04em;">
                    📂 Section Navigation
                </span>
                <span style="font-size: 12px; font-weight: 600; background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; padding: 2px 10px; border-radius: 12px;">
                    Step {current_idx + 1} of {total_count}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        nav_col1, nav_col2, nav_col3 = st.columns([1.2, 5.6, 1.2])
        with nav_col1:
            if st.button("◀ Prev", disabled=(current_idx == 0), use_container_width=True, key="btn_nav_prev", help="Navigate to previous section"):
                st.session_state["current_section_edit"] = tab_names[current_idx - 1]
                st.rerun()
        with nav_col3:
            if st.button("Next ▶", disabled=(current_idx == total_count - 1), use_container_width=True, key="btn_nav_next", help="Navigate to next section"):
                st.session_state["current_section_edit"] = tab_names[current_idx + 1]
                st.rerun()
        with nav_col2:
            selected_tab = st.selectbox(
                "Select a Section to Fill Out:",
                tab_names,
                key="current_section_edit",
                label_visibility="collapsed"
            )
    
        sec_config = sections[tab_names.index(selected_tab)]
        sec_id = sec_config['id']
        existing_sec = existing_sections.get(sec_id)

        help_text = sec_config.get('help_text', 'No instructions provided.')
        example_text = sec_config.get('example', '')

        is_completed = is_section_filled(existing_sec, sec_config)
        status_badge = (
            '<span style="background: #DCFCE7; color: #166534; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 12px; border: 1px solid #86EFAC;">✓ Section Completed</span>'
            if is_completed
            else '<span style="background: #FEF3C7; color: #92400E; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 12px; border: 1px solid #FDE68A;">⏳ Pending Input</span>'
        )

        example_html = (
            f'<div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed #CBD5E1; color: #64748B; font-size: 12.5px; font-style: italic;"><b>Example:</b> {example_text}</div>'
            if example_text
            else ""
        )

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #3B82F6; border-radius: 8px; padding: 12px 16px; margin: 8px 0 16px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-weight: 700; color: #1E293B; font-size: 13.5px;">📋 Instructions for {sec_config['name']}</span>
                    {status_badge}
                </div>
                <div style="color: #334155; font-size: 13px; line-height: 1.5;">
                    {help_text}
                </div>
                {example_html}
            </div>
            """,
            unsafe_allow_html=True
        )

        # AI Process Co-pilot: Interactive Guided Assistant for Creator
        import datetime
        from config.guided_questions import (
            SECTION_GUIDED_SPECS,
            compute_next_review_date,
            build_table_rows_from_answers,
            build_text_summary_from_answers,
            build_mermaid_flowchart_from_answers
        )
        spec = SECTION_GUIDED_SPECS.get(sec_id)
        if spec:
            guide_expanded = st.session_state.get(f"show_guide_{sec_id}", not is_completed)
            expander_title = (
                f"📝 Click Here to Fill This Section: Guided Assistant ({spec['title']})"
                if not is_completed
                else f"✨ AI Process Co-pilot: Guided Q&A Assistant ({spec['title']})"
            )

            if not is_completed:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%); 
                                border: 2px solid #818CF8; border-radius: 8px; padding: 12px 16px; margin: 4px 0 12px 0;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 22px;">👉</span>
                            <div>
                                <span style="font-weight: 700; color: #3730A3; font-size: 14px;">
                                    Click in the dropdown below to fill this section
                                </span>
                                <span style="color: #4B5563; font-size: 12.5px; display: block; margin-top: 2px;">
                                    Answer the guided questions in the form below to auto-format and populate <b>{sec_config['name']}</b>. The manual editor is kept hidden until filled.
                                </span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with st.expander(expander_title, expanded=guide_expanded):
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%); 
                                border: 1px solid #C7D2FE; border-left: 4px solid #6366F1; border-radius: 8px; 
                                padding: 10px 14px; margin-bottom: 14px;">
                        <div style="font-weight: 700; color: #3730A3; font-size: 13.5px; display: flex; align-items: center; gap: 6px;">
                            <span>🤖 Interactive AI Assistant</span>
                        </div>
                        <div style="color: #4B5563; font-size: 13px; margin-top: 3px; line-height: 1.4;">
                            <i>{spec['intro']}</i> Answer the questions below and click <b>Auto-Fill Section</b> to generate high-quality, standardized content.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                answers = {}
                fields = spec.get("fields", [])
                
                # Special high-polish interactive wizard for Section 1.3: Document Review Cycle
                if sec_id == "1.3":
                    ex_data = existing_sec.structured_data[0] if (existing_sec and existing_sec.structured_data) else {}
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        eff_val = st.date_input(
                            "1. Effective Date (When this process goes live):",
                            value=datetime.date.today(),
                            key=f"qa_{sec_id}_eff_date",
                            help="The date from which this version of the process becomes binding."
                        )
                    with c2:
                        freq_options = [
                            "Annual (Every 12 months)",
                            "Semi-Annual (Every 6 months)",
                            "Quarterly (Every 3 months)",
                            "Monthly",
                            "Biennial (Every 2 years)",
                            "Event-triggered / As needed"
                        ]
                        freq_val = st.selectbox(
                            "2. How often must this document be reviewed?",
                            options=freq_options,
                            index=0,
                            key=f"qa_{sec_id}_freq",
                            help="Corporate governance standard review cycle frequency."
                        )
                    
                    calculated_next = compute_next_review_date(eff_val, freq_val)
                    combo_key = f"_combo_{sec_id}"
                    curr_combo = f"{eff_val}_{freq_val}"
                    if st.session_state.get(combo_key) != curr_combo:
                        st.session_state[f"qa_{sec_id}_next_date"] = calculated_next
                        st.session_state[combo_key] = curr_combo

                    c3, c4 = st.columns(2)
                    with c3:
                        next_val = st.date_input(
                            "3. Scheduled Next Review Date:",
                            value=st.session_state.get(f"qa_{sec_id}_next_date", calculated_next),
                            key=f"qa_{sec_id}_next_date",
                            help="Auto-calculated from Effective Date + Frequency (you can adjust if needed)."
                        )
                    with c4:
                        def_owner = ex_data.get("Process Owner") or "Program Head (PH)"
                        owner_options = [
                            "Program Head (PH)",
                            "Operations Manager",
                            "Vertical Lead",
                            "Program Director",
                            "Quality & Excellence Lead",
                            "Other (Specify custom role...)"
                        ]
                        owner_idx = owner_options.index(def_owner) if def_owner in owner_options else 0
                        owner_sel = st.selectbox(
                            "4. Designated Process Owner Role:",
                            options=owner_options,
                            index=owner_idx,
                            key=f"qa_{sec_id}_owner_sel",
                            help="Select standard organizational designation responsible for periodic review."
                        )
                        if "other" in owner_sel.lower():
                            owner_role = st.text_input(
                                "↳ Specify custom owner role:",
                                placeholder="e.g. Operations Director",
                                key=f"qa_{sec_id}_owner_custom"
                            )
                        else:
                            owner_role = owner_sel
                    
                    c5, c6 = st.columns(2)
                    with c5:
                        user_name = st.session_state.get("current_user_name", "")
                        def_name = ex_data.get("Name") or user_name
                        owner_name = st.text_input(
                            "5. Process Owner Name:",
                            value=def_name,
                            placeholder="e.g. John Doe",
                            key=f"qa_{sec_id}_name"
                        )
                    with c6:
                        def_sign = ex_data.get("Sign") or ("".join([p[0].upper() for p in def_name.split()[:2]]) if def_name else "PH")
                        owner_sign = st.text_input(
                            "6. Signature Code / Initials:",
                            value=def_sign,
                            placeholder="e.g. JD or PH",
                            key=f"qa_{sec_id}_sign"
                        )
                    
                    answers = {
                        "eff_date": eff_val,
                        "review_frequency": freq_val,
                        "next_review_date": next_val,
                        "process_owner": owner_role,
                        "owner_name": owner_name,
                        "owner_sign": owner_sign
                    }
                else:
                    # General interactive questionnaire layout with role dropdown support
                    def render_qa_widget(field_dict):
                        ftype = field_dict.get("type", "text")
                        fid = field_dict["id"]
                        flabel = field_dict["label"]
                        fhelp = field_dict.get("help")
                        k = f"qa_{sec_id}_{fid}"
                        
                        if ftype == "date":
                            return st.date_input(flabel, value=datetime.date.today(), key=k, help=fhelp)
                        elif ftype == "select":
                            opts = field_dict.get("options", [])
                            d_idx = 0
                            if field_dict.get("default") and field_dict["default"] in opts:
                                d_idx = opts.index(field_dict["default"])
                            sel = st.selectbox(flabel, options=opts, index=d_idx, key=k, help=fhelp)
                            if "other" in str(sel).lower():
                                custom = st.text_input(f"↳ Specify custom {flabel.split('(')[0].strip()}:", placeholder="e.g. Lead Coordinator / External Auditor", key=f"{k}_custom")
                                return custom.strip() if custom.strip() else sel
                            return sel
                        elif ftype == "textarea":
                            return st.text_area(flabel, placeholder=field_dict.get("placeholder", ""), height=80, key=k, help=fhelp)
                        else:
                            return st.text_input(flabel, placeholder=field_dict.get("placeholder", ""), key=k, help=fhelp)

                    i = 0
                    while i < len(fields):
                        f = fields[i]
                        f_type = f.get("type", "text")
                        
                        next_f = fields[i+1] if i + 1 < len(fields) else None
                        next_f_type = next_f.get("type", "text") if next_f else None
                        
                        can_pair = (f_type in ["text", "date", "select"]) and (next_f_type in ["text", "date", "select"] if next_f else False)
                        
                        if can_pair and next_f:
                            col1, col2 = st.columns(2)
                            with col1:
                                answers[f["id"]] = render_qa_widget(f)
                            with col2:
                                answers[next_f["id"]] = render_qa_widget(next_f)
                            i += 2
                        else:
                            answers[f["id"]] = render_qa_widget(f)
                            i += 1

                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                
                # Action buttons depending on section type
                if sec_config["type"] == "table":
                    multi_row_sections = ["1.12", "1.13", "1.5", "1.14", "1.15", "1.16", "1.17", "1.18", "1.19", "1.20", "1.21", "1.22"]
                    if sec_id in multi_row_sections:
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            apply_btn = st.button("✨ Set / Overwrite Table", key=f"btn_apply_{sec_id}", type="primary", use_container_width=True)
                        with col_btn2:
                            append_btn = st.button("➕ Add as New Row to Table", key=f"btn_append_{sec_id}", use_container_width=True)
                    else:
                        apply_btn = st.button(f"✨ Apply Answers to {sec_config['name']} Table", key=f"btn_apply_{sec_id}", type="primary")
                        append_btn = False

                    if apply_btn:
                        new_rows = build_table_rows_from_answers(sec_id, answers)
                        if not existing_sec:
                            new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=new_rows)
                            db.add(new_sec)
                        else:
                            existing_sec.structured_data = new_rows
                        db.commit()
                        st.session_state[f"show_guide_{sec_id}"] = False
                        st.session_state[f"is_editing_{sec_id}"] = False
                        st.success(f"✅ {sec_config['name']} table populated from your answers! Check the preview below.")
                        st.rerun()

                    if append_btn:
                        new_rows = build_table_rows_from_answers(sec_id, answers)
                        existing_rows = existing_sec.structured_data if (existing_sec and existing_sec.structured_data) else []
                        if sec_id == "1.13" and new_rows:
                            new_rows[0]["Sr. No."] = len(existing_rows) + 1
                        combined_rows = existing_rows + new_rows
                        if not existing_sec:
                            new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=combined_rows)
                            db.add(new_sec)
                        else:
                            existing_sec.structured_data = combined_rows
                        db.commit()
                        st.session_state[f"show_guide_{sec_id}"] = False
                        st.session_state[f"is_editing_{sec_id}"] = False
                        st.success(f"✅ New row added to {sec_config['name']} table! Check preview below.")
                        st.rerun()

                elif sec_config["type"] == "flowchart":
                    if st.button("✨ Auto-Generate Flowchart from Steps", key=f"btn_flow_{sec_id}", type="primary"):
                        mermaid_code = build_mermaid_flowchart_from_answers(answers)
                        if not existing_sec:
                            new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=mermaid_code)
                            db.add(new_sec)
                        else:
                            existing_sec.content = mermaid_code
                        db.commit()
                        st.session_state[f"show_guide_{sec_id}"] = False
                        st.session_state[f"is_editing_{sec_id}"] = False
                        st.success("✅ Flowchart updated from your steps! Check preview below.")
                        st.rerun()

                elif sec_config["type"] == "text":
                    col_t1, col_t2 = st.columns([1, 1])
                    with col_t1:
                        apply_text_btn = st.button("✨ Apply Answers to Section", key=f"btn_apply_txt_{sec_id}", type="primary", use_container_width=True)
                    with col_t2:
                        ai_text_btn = st.button("🤖 Polish & Synthesize with AI", key=f"btn_ai_txt_{sec_id}", use_container_width=True)

                    if apply_text_btn:
                        formatted_content = build_text_summary_from_answers(sec_id, answers)
                        if not existing_sec:
                            new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=formatted_content)
                            db.add(new_sec)
                        else:
                            existing_sec.content = formatted_content
                        db.commit()
                        st.session_state[f"show_guide_{sec_id}"] = False
                        st.session_state[f"is_editing_{sec_id}"] = False
                        st.success("✅ Section content updated from your answers! Check preview below.")
                        st.rerun()

                    if ai_text_btn:
                        with st.spinner("AI is synthesizing professional enterprise content..."):
                            from services.llm_service import get_llm_provider
                            llm = get_llm_provider()
                            raw_notes = build_text_summary_from_answers(sec_id, answers)
                            gen_result = llm.generate_section_from_qa(sec_id, sec_config, raw_notes, team_name=current_note.team)
                            if not existing_sec:
                                new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=gen_result)
                                db.add(new_sec)
                            else:
                                existing_sec.content = gen_result
                            db.commit()
                            st.session_state[f"show_guide_{sec_id}"] = False
                            st.session_state[f"is_editing_{sec_id}"] = False
                            st.success("✅ Section synthesized with AI! Check preview below.")
                            st.rerun()

                if is_completed:
                    if st.button("✖️ Collapse Guided Form", key=f"btn_close_expander_{sec_id}"):
                        st.session_state[f"show_guide_{sec_id}"] = False
                        st.rerun()

        is_editing = st.session_state.get(f"is_editing_{sec_id}", False)

        with st.container():
            if sec_config["type"] == "text":
                if not is_completed and not is_editing:
                    st.markdown(
                        """
                        <div style="background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 8px; padding: 18px 20px; text-align: center; margin: 16px 0; color: #64748B;">
                            <div style="font-size: 20px; margin-bottom: 4px;">🔒</div>
                            <div style="font-weight: 700; color: #334155; font-size: 13.5px;">Text Editor is Hidden</div>
                            <div style="font-size: 12.5px; margin-top: 4px; line-height: 1.5;">
                                Please use the guided assistant in the dropdown above to fill this section first.<br>
                                Once filled, your response will appear here and you can edit or format it directly whenever needed.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("🛠️ Enter Text Directly in Editor (Skip Guide)", key=f"btn_manual_txt_{sec_id}"):
                        st.session_state[f"is_editing_{sec_id}"] = True
                        st.rerun()
                elif is_completed and not is_editing:
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 8px;">
                            <span style="font-weight: 700; color: #1E293B; font-size: 14px;">📄 Current {sec_config['name']} Content:</span>
                            <span style="font-size: 11.5px; background: #DCFCE7; color: #166534; font-weight: 600; padding: 3px 10px; border-radius: 12px; border: 1px solid #86EFAC;">✓ Saved & Active</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; line-height: 1.6; color: #1E293B; font-size: 13.5px; margin-bottom: 12px; white-space: pre-wrap;">{existing_sec.content}</div>
                        """,
                        unsafe_allow_html=True
                    )
                    col_act1, col_act2 = st.columns([1, 1])
                    with col_act1:
                        if st.button("✏️ Edit Content Directly", key=f"btn_edit_txt_{sec_id}", type="primary", use_container_width=True):
                            st.session_state[f"is_editing_{sec_id}"] = True
                            st.rerun()
                    with col_act2:
                        if st.button("🤖 Modify via Guided Assistant", key=f"btn_reopen_qa_txt_{sec_id}", use_container_width=True):
                            st.session_state[f"show_guide_{sec_id}"] = True
                            st.rerun()
                else:
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.markdown(f"##### ✏️ Editing {sec_config['name']}:")
                    with col_h2:
                        if is_completed and st.button("✖️ Cancel / Done", key=f"btn_cancel_txt_{sec_id}", use_container_width=True):
                            st.session_state[f"is_editing_{sec_id}"] = False
                            st.rerun()

                    with st.form(f"form_{sec_id}"):
                        val = existing_sec.content if existing_sec else ""
                        content = st.text_area("Provide your detailed response below:", value=val, height=250)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            save_btn = st.form_submit_button("Save Section", type="primary")
                        with col2:
                            ai_btn = st.form_submit_button(f"✨ Get AI Suggestion for {sec_id}")

                        if ai_btn:
                            from services.rag_service import rag_service
                            from services.llm_service import get_llm_provider
                
                            with st.spinner("Generating suggestion based on your notes and team history..."):
                                context_list = rag_service.get_team_context(current_note.team, sec_id)
                                if isinstance(context_list, str):
                                    context_list = [context_list]
                                llm = get_llm_provider()
                                suggestion = llm.generate_suggestion(sec_config, context_list, user_draft=content)
                                st.info(f"**AI Suggestion (Copy and paste into the box above):**\n\n{suggestion}")

                        if save_btn:
                            from core.rule_validator import RuleValidator
                            from models.schemas import ProcessSectionSchema
                            sec_schema = ProcessSectionSchema(section_id=sec_id, content=content, structured_data=[])
                            issues = RuleValidator().validate(sec_schema, config)
                
                            if issues:
                                for issue in issues:
                                    st.error(f"Validation Error: {issue}")
                            else:
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=content)
                                    db.add(new_sec)
                                else:
                                    existing_sec.content = content
                                db.commit()
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success(f"Section {sec_id} saved successfully!")
                                st.rerun()

            elif sec_config["type"] == "table":
                # Special Quick-Action for RACI Matrix (1.13)
                if sec_id == "1.13":
                    st.markdown("""
                    <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                        <span style="color: #1E40AF; font-weight: 600;">📋 Standard RACI Matrix Format (BE Standard):</span>
                        <p style="color: #1E40AF; font-size: 13px; margin: 4px 0 0 0;">
                        Activities must match Section 1.12. Specify exact job titles/designations (e.g. PH, Manager, Vertical Lead) under R, A, C, and I. Do NOT use Yes/No.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    desc_sec = existing_sections.get("1.12")
                    if desc_sec and desc_sec.structured_data:
                        if st.button("🔄 Auto-Populate Activities from Process Description (1.12)", key="btn_sync_raci"):
                            new_raci_data = []
                            for i, row in enumerate(desc_sec.structured_data, start=1):
                                new_raci_data.append({
                                    "Sr. No.": i,
                                    "Activity name": row.get("Activity", f"Activity {i}"),
                                    "Activity description": row.get("Description", ""),
                                    "Timeline": row.get("TAT", "Given timeline"),
                                    "Responsible": row.get("Owner/Role", ""),
                                    "Accountable": "",
                                    "Consulted by": "",
                                    "Informed to": ""
                                })
                            if not existing_sec:
                                new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=new_raci_data)
                                db.add(new_sec)
                            else:
                                existing_sec.structured_data = new_raci_data
                            db.commit()
                            st.success("Activities synced from Section 1.12! Now assign the Accountable, Consulted, and Informed designations.")
                            st.rerun()

                fields = sec_config.get("fields", [])
    
                if existing_sec and existing_sec.structured_data:
                    df = pd.DataFrame(existing_sec.structured_data)
                    df.index = df.index + 1
        
                    render_fields = list(fields)
                    if "Reviewer Comment" in df.columns:
                        render_fields.append("Reviewer Comment")
            
                    for f in render_fields:
                        if f not in df.columns:
                            df[f] = None
                    df = df[render_fields]
                else:
                    df = pd.DataFrame(columns=fields)
                    if sec_id == "1.1":
                        df.loc[1] = [None for _ in fields]
                        df.loc[2] = [None for _ in fields]
                        df.loc[3] = [None for _ in fields]
                        if "Role" in df.columns:
                            df.at[1, "Role"] = "Process Owner"
                            df.at[2, "Role"] = "Process Reviewer"
                            df.at[3, "Role"] = "Process Approver"
                    elif sec_id == "1.2":
                        df.loc[1] = [None for _ in fields]
                        if "Version No." in df.columns:
                            df.at[1, "Version No."] = "1.0"
                        if "Amendment" in df.columns:
                            df.at[1, "Amendment"] = "Initial Draft"
                    elif sec_id == "1.13":
                        # Check if Section 1.12 has activities
                        desc_sec = existing_sections.get("1.12")
                        if desc_sec and desc_sec.structured_data:
                            for i, row in enumerate(desc_sec.structured_data, start=1):
                                df.loc[i] = [None for _ in fields]
                                if "Sr. No." in df.columns: df.at[i, "Sr. No."] = i
                                if "Activity name" in df.columns: df.at[i, "Activity name"] = row.get("Activity", "")
                                if "Activity description" in df.columns: df.at[i, "Activity description"] = row.get("Description", "")
                                if "Timeline" in df.columns: df.at[i, "Timeline"] = row.get("TAT", "Given timeline")
                                if "Responsible" in df.columns: df.at[i, "Responsible"] = row.get("Owner/Role", "")
                        else:
                            df.loc[1] = [None for _ in fields]
                            if "Sr. No." in df.columns: df.at[i, "Sr. No."] = 1
                    elif sec_id == "1.15":
                        df.loc[1] = [None for _ in fields]
                        if "Exception Description" in df.columns:
                            df.at[1, "Exception Description"] = "No known exceptions identified"
                    else:
                        df.loc[1] = [None for _ in fields]
    
                column_config = {}
                for f in fields:
                    f_lower = f.lower()
                    if "date" in f_lower:
                        column_config[f] = st.column_config.DateColumn(f, format="YYYY-MM-DD")
                        df[f] = pd.to_datetime(df[f], errors='coerce').dt.date
                    elif f == "Sr. No." or "no." in f_lower or f_lower == "tat":
                        column_config[f] = st.column_config.NumberColumn(f, step=1)
                        df[f] = pd.to_numeric(df[f], errors='coerce')
                    elif "level of risk" in f_lower:
                        column_config[f] = st.column_config.SelectboxColumn(f, options=["High", "Medium", "Low"])
                    elif sec_id == "1.13" and f == "Responsible":
                        r_opts = ["PH", "Field Officer", "Operations Manager", "Vertical Lead", "Project Manager", "Trainer", "Finance Lead", "HR Lead"]
                        exist_r = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(r_opts + exist_r))), help="Select designation executing the work")
                    elif sec_id == "1.13" and f == "Accountable":
                        a_opts = ["Manager", "PH", "Vertical Lead", "Director", "Quality Lead"]
                        exist_a = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(a_opts + exist_a))), help="Select single Accountable owner")
                    elif sec_id == "1.13" and f == "Consulted by":
                        c_opts = ["Director", "Quality Lead", "Vertical Lead", "Legal & Compliance", "Finance Lead"]
                        exist_c = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(c_opts + exist_c))), help="Select consulted stakeholder")
                    elif sec_id == "1.13" and f == "Informed to":
                        i_opts = ["CEO Project teams", "SCD internal teams", "Operations Team", "Program Director", "Finance Team"]
                        exist_i = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(i_opts + exist_i))), help="Select informed team")
                    elif sec_id == "1.5" and f == "Owner":
                        kpi_o = ["Program Head (PH)", "Operations Manager", "Vertical Lead", "Program Director", "Quality & Excellence Lead", "Project Manager"]
                        exist_o = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(kpi_o + exist_o))), help="Select KPI Owner")
                    elif sec_id == "1.5" and f == "Maker":
                        kpi_m = ["Field Officer", "Field Executive", "Operations Executive", "Program Associate", "Project Executive", "Trainer / Facilitator", "Program Head (PH)"]
                        exist_m = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(kpi_m + exist_m))), help="Select Maker")
                    elif sec_id == "1.5" and f == "Checker":
                        kpi_c = ["Operations Manager", "Program Head (PH)", "Vertical Lead", "Quality & Business Excellence Lead", "Project Manager", "Program Director"]
                        exist_c = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(kpi_c + exist_c))), help="Select Checker")
                    elif sec_id == "1.5" and f in ["Report Frequency", "Review Frequency"]:
                        freq_opts = ["Daily", "Weekly", "Monthly", "Quarterly", "Semi-Annually", "Annually"]
                        exist_fr = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(freq_opts + exist_fr))))
                    elif sec_id == "1.15" and f in ["Prop By", "Recom By", "Approved By", "Informed to"]:
                        exc_opts = ["Field Officer", "Operations Executive", "Program Head (PH)", "Operations Manager", "Vertical Lead", "Program Director", "CEO / Leadership", "CEO Project teams", "Finance Team"]
                        exist_exc = [str(x) for x in df[f].dropna().unique() if str(x).strip()]
                        column_config[f] = st.column_config.SelectboxColumn(f, options=sorted(list(set(exc_opts + exist_exc))))
                    elif sec_id == "1.18" and f == "Storage Type":
                        column_config[f] = st.column_config.SelectboxColumn(f, options=["Both Soft & Hard copy", "Soft copy", "Hard copy"])
                    elif sec_id == "1.18" and f == "Retention period":
                        column_config[f] = st.column_config.SelectboxColumn(f, options=["7 Years", "5 Years", "3 Years", "10 Years", "Permanent"])
                    elif sec_id == "1.18" and f == "Criticality":
                        column_config[f] = st.column_config.SelectboxColumn(f, options=["High", "Medium", "Low"])
                    elif f in ["Responsible", "Accountable", "Consulted by", "Informed to", "Owner/Role", "Process Owner"]:
                        column_config[f] = st.column_config.TextColumn(f, help=f"Enter designation/job title for {f} (e.g. Manager, PH, Vertical Lead)")
                    else:
                        column_config[f] = st.column_config.TextColumn(f)

                if not is_completed and not is_editing:
                    st.markdown(
                        """
                        <div style="background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 8px; padding: 18px 20px; text-align: center; margin: 16px 0; color: #64748B;">
                            <div style="font-size: 20px; margin-bottom: 4px;">🔒</div>
                            <div style="font-weight: 700; color: #334155; font-size: 13.5px;">Table Editor is Hidden</div>
                            <div style="font-size: 12.5px; margin-top: 4px; line-height: 1.5;">
                                Please use the guided form in the dropdown above and click <b>Apply Answers</b> to populate this table.<br>
                                Once filled, the table will be displayed here, and you can edit rows directly whenever needed.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("🛠️ Enter Data Manually in Raw Table Instead (Skip Guide)", key=f"btn_manual_tbl_{sec_id}"):
                        st.session_state[f"is_editing_{sec_id}"] = True
                        st.rerun()
                elif is_completed and not is_editing:
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 8px;">
                            <span style="font-weight: 700; color: #1E293B; font-size: 14px;">📄 Current {sec_config['name']} Table ({len(df)} row{'s' if len(df) != 1 else ''}):</span>
                            <span style="font-size: 11.5px; background: #DCFCE7; color: #166534; font-weight: 600; padding: 3px 10px; border-radius: 12px; border: 1px solid #86EFAC;">✓ Saved & Active</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.dataframe(df, use_container_width=True)

                    col_act1, col_act2 = st.columns([1, 1])
                    with col_act1:
                        if st.button("✏️ Edit Table Directly", key=f"btn_edit_tbl_{sec_id}", type="primary", use_container_width=True):
                            st.session_state[f"is_editing_{sec_id}"] = True
                            st.rerun()
                    with col_act2:
                        if st.button("🤖 Modify via Guided Assistant", key=f"btn_reopen_qa_tbl_{sec_id}", use_container_width=True):
                            st.session_state[f"show_guide_{sec_id}"] = True
                            st.rerun()
                else:
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.markdown(f"##### ✏️ Editing {sec_config['name']} Table:")
                    with col_h2:
                        if is_completed and st.button("✖️ Cancel / Done", key=f"btn_cancel_tbl_{sec_id}", use_container_width=True):
                            st.session_state[f"is_editing_{sec_id}"] = False
                            st.rerun()

                    with st.form(f"form_table_{sec_id}"):
                        st.markdown("Edit the table below:")
                        disabled_cols = ["Reviewer Comment"] if "Reviewer Comment" in df.columns else False
                        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"editor_{sec_id}", column_config=column_config, disabled=disabled_cols)
            
                        if st.form_submit_button("Save Section", type="primary"):
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
                
                            from core.rule_validator import RuleValidator
                            from models.schemas import ProcessSectionSchema
                            sec_schema = ProcessSectionSchema(section_id=sec_id, content="", structured_data=json_data)
                            issues = RuleValidator().validate(sec_schema, config)
                
                            if issues:
                                for issue in issues:
                                    st.error(f"Validation Error: {issue}")
                            else:
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=json_data)
                                    db.add(new_sec)
                                else:
                                    existing_sec.structured_data = json_data
                                db.commit()
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success(f"Section {sec_id} saved successfully!")
                                st.rerun()

            elif sec_config["type"] in ["file", "flowchart"]:
                current_chart = existing_sec.content if existing_sec else ""
                
                if not is_completed and not is_editing:
                    st.markdown(
                        """
                        <div style="background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 8px; padding: 18px 20px; text-align: center; margin: 16px 0; color: #64748B;">
                            <div style="font-size: 20px; margin-bottom: 4px;">🔒</div>
                            <div style="font-weight: 700; color: #334155; font-size: 13.5px;">Flowchart Editor is Hidden</div>
                            <div style="font-size: 12.5px; margin-top: 4px; line-height: 1.5;">
                                Please use the guided generator above to build flowchart steps, or auto-generate from Section 1.12.<br>
                                Once generated, your flowchart will appear here and you can edit or upload files directly.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("🛠️ Edit Mermaid Syntax / Upload Diagram Manually", key=f"btn_manual_flow_{sec_id}"):
                        st.session_state[f"is_editing_{sec_id}"] = True
                        st.rerun()
                elif is_completed and not is_editing:
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 8px;">
                            <span style="font-weight: 700; color: #1E293B; font-size: 14px;">📊 Saved Flowchart Diagram:</span>
                            <span style="font-size: 11.5px; background: #DCFCE7; color: #166534; font-weight: 600; padding: 3px 10px; border-radius: 12px; border: 1px solid #86EFAC;">✓ Saved & Active</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if current_chart and not current_chart.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.docx', '.vsdx')):
                        clean_mermaid = current_chart.replace("```mermaid", "").replace("```", "").strip()
                        st.markdown(f"```mermaid\n{clean_mermaid}\n```")
                    elif current_chart and current_chart.endswith(('.png', '.jpg', '.jpeg')):
                        img_path = os.path.join("uploads", current_chart)
                        if os.path.exists(img_path):
                            st.image(img_path, caption=current_chart, use_container_width=True)
                        else:
                            st.info(f"Uploaded diagram: {current_chart}")
                    else:
                        st.info(f"Saved diagram: {current_chart}")

                    col_act1, col_act2 = st.columns([1, 1])
                    with col_act1:
                        if st.button("✏️ Edit Flowchart / Upload New", key=f"btn_edit_flow_{sec_id}", type="primary", use_container_width=True):
                            st.session_state[f"is_editing_{sec_id}"] = True
                            st.rerun()
                    with col_act2:
                        if st.button("🤖 Modify via Guided Assistant", key=f"btn_reopen_qa_flow_{sec_id}", use_container_width=True):
                            st.session_state[f"show_guide_{sec_id}"] = True
                            st.rerun()
                else:
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.markdown(f"##### ✏️ Editing {sec_config['name']}:")
                    with col_h2:
                        if is_completed and st.button("✖️ Cancel / Done", key=f"btn_cancel_flow_{sec_id}", use_container_width=True):
                            st.session_state[f"is_editing_{sec_id}"] = False
                            st.rerun()

                    flow_tab1, flow_tab2 = st.tabs(["📊 Visual Flowchart (AI Generated / Mermaid)", "📁 Upload Diagram File"])
                    
                    with flow_tab1:
                        st.markdown("""
                        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                            <span style="color: #0F172A; font-weight: 600;">Process Flowchart Generator:</span>
                            <p style="color: #64748B; font-size: 13px; margin: 4px 0 0 0;">
                            Depicts the actual process flow, decision points, and hand-offs directly aligned with Section 1.12.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        desc_sec = existing_sections.get("1.12")
                        col_f1, col_f2 = st.columns([1, 1])
                        with col_f1:
                            if st.button("✨ Auto-Generate Flowchart from Process Description (1.12)", key="btn_gen_flowchart"):
                                if not desc_sec or not desc_sec.structured_data:
                                    st.warning("Please fill out Section 1.12 (Process Description) first so the AI can map the steps into a flowchart.")
                                else:
                                    with st.spinner("Generating operational process flowchart..."):
                                        from services.llm_service import get_llm_provider
                                        llm = get_llm_provider()
                                        mermaid_code = llm.generate_flowchart_mermaid(desc_sec.structured_data)
                                        if not existing_sec:
                                            new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=mermaid_code)
                                            db.add(new_sec)
                                        else:
                                            existing_sec.content = mermaid_code
                                        db.commit()
                                        st.session_state[f"is_editing_{sec_id}"] = False
                                        st.success("Flowchart generated successfully!")
                                        st.rerun()

                        with st.form(f"form_flow_{sec_id}"):
                            chart_content = st.text_area(
                                "Flowchart Definition (Mermaid Syntax):", 
                                value=current_chart if current_chart and not current_chart.endswith(('.png', '.jpg', '.pdf', '.docx', '.vsdx')) else "graph TD\n    A[Start Process] --> B[Execute Key Steps] --> C[End Process]", 
                                height=200,
                                help="Edit the diagram nodes, decision branches, and handoffs."
                            )
                            save_chart_btn = st.form_submit_button("Save Flowchart Diagram", type="primary")
                            if save_chart_btn:
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=chart_content)
                                    db.add(new_sec)
                                else:
                                    existing_sec.content = chart_content
                                db.commit()
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success("Flowchart saved successfully!")
                                st.rerun()

                        if current_chart and not current_chart.endswith(('.png', '.jpg', '.pdf', '.docx', '.vsdx')):
                            st.markdown("#### Live Flowchart Preview:")
                            try:
                                clean_mermaid = current_chart.replace("```mermaid", "").replace("```", "").strip()
                                st.markdown(f"```mermaid\n{clean_mermaid}\n```")
                            except Exception as e:
                                st.info(f"Diagram code: {current_chart}")

                    with flow_tab2:
                        st.markdown("Upload an existing visual flowchart diagram (Visio, Draw.io, PNG, JPG, PDF):")
                        uploaded_file = st.file_uploader("Choose a diagram file", type=["png", "jpg", "jpeg", "pdf", "vsdx", "drawio", "docx"], key=f"uploader_{sec_id}")
                        if existing_sec and existing_sec.content and existing_sec.content.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.docx', '.vsdx')):
                            st.info(f"Currently uploaded file: {existing_sec.content}")
                            if existing_sec.content.endswith(('.png', '.jpg', '.jpeg')):
                                img_path = os.path.join("uploads", existing_sec.content)
                                if os.path.exists(img_path):
                                    st.image(img_path, caption=existing_sec.content, use_container_width=True)

                        if st.button("Save Uploaded Diagram", key=f"save_file_{sec_id}", type="primary"):
                            if uploaded_file is not None:
                                os.makedirs("uploads", exist_ok=True)
                                file_path = os.path.join("uploads", uploaded_file.name)
                                with open(file_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                                content_val = uploaded_file.name
                            else:
                                content_val = existing_sec.content if existing_sec else ""
                            
                            if not content_val:
                                st.error("Please upload a file before saving.")
                            else:
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=content_val)
                                    db.add(new_sec)
                                else:
                                    existing_sec.content = content_val
                                db.commit()
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success(f"Flowchart diagram file saved: {content_val}")
                                st.rerun()
    
        st.markdown("<br><hr>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👀 Preview Full Draft", use_container_width=True, help="Read through your entire process note so far."):
                if current_note:
                    st.session_state.selected_note_id = current_note.id
                st.switch_page("pages/5_View_All_Notes.py")
    
        current_idx = tab_names.index(selected_tab)
        with col2:
            if current_idx < len(tab_names) - 1:
                def go_next():
                    st.session_state["current_section_edit"] = tab_names[current_idx + 1]
                st.button("Next Section ➔", type="primary", use_container_width=True, on_click=go_next)
            else:
                if completed_count < total_count:
                    st.warning(f"You have only completed {completed_count}/{total_count} sections. It is highly recommended to finish all sections before validation.")
                if st.button("Proceed to Validation ➔", type="primary", use_container_width=True):
                    if current_note:
                        st.session_state.selected_note_id = current_note.id
                    st.switch_page("pages/3_Validation.py")

finally:
    db.close()
