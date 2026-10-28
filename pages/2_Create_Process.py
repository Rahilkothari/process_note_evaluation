import streamlit as st
import yaml
import os
import pandas as pd
import json
from models.database import SessionLocal, get_db, ProcessNote, ProcessSection, User
from sqlalchemy.orm import Session


from core.ui_utils import inject_custom_css, render_mermaid_flowchart


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
    
        def get_section_audit_status(sec, s_config):
            if not sec:
                return "pending", ["Section not yet filled."]
            stype = s_config.get("type", "text")
            if stype == "table":
                if not sec.structured_data:
                    return "pending", ["Table is empty."]
            elif stype in ["file", "flowchart"]:
                if not sec.content or not str(sec.content).strip():
                    return "pending", ["Flowchart / file is missing."]
            else:
                if not sec.content or not str(sec.content).strip():
                    return "pending", ["Section content is empty."]
            
            from core.rule_validator import RuleValidator
            from models.schemas import ProcessSectionSchema
            sec_schema = ProcessSectionSchema(
                section_id=s_config["id"],
                content=sec.content or "",
                structured_data=sec.structured_data or []
            )
            issues = RuleValidator().validate(sec_schema, {"sections": sections})
            if issues:
                return "needs_revision", issues
            return "ready", []

        def is_section_filled(sec, s_config):
            st_code, _ = get_section_audit_status(sec, s_config)
            return st_code != "pending"

        db_sections = db.query(ProcessSection).filter(ProcessSection.process_note_id == current_note.id).all()
        existing_sections = {s.section_id: s for s in db_sections}
        
        status_map = {s["id"]: get_section_audit_status(existing_sections.get(s["id"]), s) for s in sections}
        ready_count = sum(1 for sid, (st_code, _) in status_map.items() if st_code == "ready")
        needs_rev_count = sum(1 for sid, (st_code, _) in status_map.items() if st_code == "needs_revision")
        pending_count = sum(1 for sid, (st_code, _) in status_map.items() if st_code == "pending")
        completed_count = ready_count + needs_rev_count
        total_count = len(sections)
        estimated_readiness = round((ready_count / total_count) * 100, 1)

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 16px; margin: 12px 0 16px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 700; color: #1E293B; font-size: 13.5px;">📊 Form Completion & Audit Readiness</span>
                    <span style="font-weight: 700; color: {'#16A34A' if estimated_readiness >= 75 else '#EA580C' if estimated_readiness >= 40 else '#DC2626'}; font-size: 13px;">
                        Readiness: {estimated_readiness}%
                    </span>
                </div>
                <div style="font-size: 12px; color: #64748B; margin-bottom: 8px; display: flex; gap: 16px;">
                    <span><b>✓ Audit Ready:</b> <span style="color: #166534; font-weight: 600;">{ready_count}</span></span>
                    <span><b>⚠️ Needs Detail:</b> <span style="color: #B45309; font-weight: 600;">{needs_rev_count}</span></span>
                    <span><b>⏳ Pending:</b> <span style="color: #64748B; font-weight: 600;">{pending_count}</span></span>
                    <span><b>Total Sections:</b> {total_count}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.progress(ready_count / total_count if total_count > 0 else 0)
    
        tab_names = [f"{sec['id']} {sec['name']}" for sec in sections]
    
        if "active_section_tab" not in st.session_state:
            st.session_state["active_section_tab"] = st.session_state.get("current_section_edit", tab_names[0])
        if st.session_state["active_section_tab"] not in tab_names:
            st.session_state["active_section_tab"] = tab_names[0]
        
        current_idx = tab_names.index(st.session_state["active_section_tab"])

        def set_active_section(new_tab):
            if new_tab in tab_names:
                st.session_state["active_section_tab"] = new_tab
                st.session_state["current_section_edit"] = new_tab

        def on_section_dropdown_change():
            chosen = st.session_state.get("section_nav_dropdown")
            if chosen in tab_names:
                st.session_state["active_section_tab"] = chosen
                st.session_state["current_section_edit"] = chosen

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
                set_active_section(tab_names[current_idx - 1])
                st.rerun()
        with nav_col3:
            if st.button("Next ▶", disabled=(current_idx == total_count - 1), use_container_width=True, key="btn_nav_next", help="Navigate to next section"):
                set_active_section(tab_names[current_idx + 1])
                st.rerun()
        with nav_col2:
            selected_tab = st.selectbox(
                "Select a Section to Fill Out:",
                tab_names,
                index=current_idx,
                key="section_nav_dropdown",
                on_change=on_section_dropdown_change,
                label_visibility="collapsed"
            )
            st.session_state["active_section_tab"] = selected_tab
            st.session_state["current_section_edit"] = selected_tab
    
        sec_config = sections[tab_names.index(selected_tab)]
        sec_id = sec_config['id']
        existing_sec = existing_sections.get(sec_id)

        help_text = sec_config.get('help_text', 'No instructions provided.')
        example_text = sec_config.get('example', '')

        curr_status, curr_issues = status_map.get(sec_id, ("pending", []))
        if curr_status == "ready":
            status_badge = '<span style="background: #DCFCE7; color: #166534; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 12px; border: 1px solid #86EFAC;">✓ Audit-Ready</span>'
        elif curr_status == "needs_revision":
            status_badge = f'<span style="background: #FEE2E2; color: #991B1B; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 12px; border: 1px solid #FCA5A5;">⚠️ Needs Detail ({len(curr_issues)} issue{"s" if len(curr_issues) > 1 else ""})</span>'
        else:
            status_badge = '<span style="background: #FEF3C7; color: #92400E; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 12px; border: 1px solid #FDE68A;">⏳ Pending Input</span>'

        is_completed = (curr_status == "ready")

        example_clean = example_text.strip()
        if example_clean.lower().startswith("example:"):
            example_clean = example_clean[len("example:"):].strip()
        example_clean = example_clean.replace("\n", " ")

        example_html = (
            f'<div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed #CBD5E1; color: #64748B; font-size: 12.5px; font-style: italic;"><b>Example:</b> {example_clean}</div>'
            if example_clean
            else ""
        )

        issues_html = ""
        if curr_status == "needs_revision" and curr_issues:
            issues_list_str = "".join([f"<li>{iss}</li>" for iss in curr_issues])
            issues_html = (
                f'<div style="margin-top: 10px; background: #FFF1F2; border: 1px solid #FECDD3; border-radius: 6px; padding: 8px 12px; color: #9F1239; font-size: 12px;">'
                f'<div style="font-weight: 700; margin-bottom: 4px;">⚠️ Current Audit Gaps (Will result in 0 score if left unaddressed):</div>'
                f'<ul style="margin: 0; padding-left: 18px;">{issues_list_str}</ul>'
                f'</div>'
            )

        border_color = '#16A34A' if curr_status == 'ready' else '#EF4444' if curr_status == 'needs_revision' else '#3B82F6'

        instructions_html = (
            f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin: 8px 0 16px 0;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
            f'<span style="font-weight: 700; color: #1E293B; font-size: 13.5px;">📋 Instructions for {sec_config["name"]}</span>'
            f'{status_badge}'
            f'</div>'
            f'<div style="color: #334155; font-size: 13px; line-height: 1.5;">{help_text}</div>'
            f'{example_html}'
            f'{issues_html}'
            f'</div>'
        )
        st.markdown(instructions_html, unsafe_allow_html=True)

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
            with st.expander(f"✨ AI Process Co-pilot: Guided Assistant ({spec['title']})", expanded=guide_expanded):
                copilot_banner = (
                    f'<div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%); '
                    f'border: 1px solid #C7D2FE; border-left: 4px solid #6366F1; border-radius: 8px; '
                    f'padding: 12px 16px; margin-bottom: 14px;">'
                    f'<div style="font-weight: 700; color: #3730A3; font-size: 14px; display: flex; align-items: center; gap: 6px;">'
                    f'<span>🤖 AI Co-pilot: Guided Assistant</span>'
                    f'</div>'
                    f'<div style="color: #4B5563; font-size: 13px; margin-top: 4px; line-height: 1.5;">'
                    f'{spec["intro"]}<br/>'
                    f'<span style="color: #4F46E5; font-weight: 600;">💡 Quick Tip:</span> '
                    f'Feel free to write simple notes, rough bullet points, or informal thoughts. Our AI will automatically fix typos, elevate tone, and structure all standard enterprise details for you.'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(copilot_banner, unsafe_allow_html=True)

                if sec_config.get("type") == "table":
                    undo_rows_guide = st.session_state.get(f"undo_table_{sec_id}")
                    if undo_rows_guide is not None:
                        ug_col1, ug_col2 = st.columns([3, 1])
                        with ug_col1:
                            st.warning(f"↩️ **Undo Available:** A previous version with **{len(undo_rows_guide)} rows** was saved before the last change.")
                        with ug_col2:
                            if st.button(f"↩️ Restore {len(undo_rows_guide)} Rows", key=f"btn_undo_guide_top_{sec_id}", type="secondary", use_container_width=True):
                                import copy
                                st.session_state[f"redo_table_{sec_id}"] = copy.deepcopy(existing_sec.structured_data if (existing_sec and existing_sec.structured_data) else [])
                                existing_sec.structured_data = copy.deepcopy(undo_rows_guide)
                                db.commit()
                                del st.session_state[f"undo_table_{sec_id}"]
                                st.success(f"✅ Table restored to previous {len(undo_rows_guide)} rows!")
                                st.rerun()

                with st.form(key=f"guided_qa_form_{sec_id}", clear_on_submit=False):
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
                        next_date_key = f"qa_{sec_id}_next_date"
                        curr_combo = f"{eff_val}_{freq_val}"
                        if st.session_state.get(combo_key) != curr_combo or next_date_key not in st.session_state:
                            st.session_state[next_date_key] = calculated_next
                            st.session_state[combo_key] = curr_combo

                        c3, c4 = st.columns(2)
                        with c3:
                            next_val = st.date_input(
                                "3. Scheduled Next Review Date:",
                                key=next_date_key,
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
                            custom_owner = st.text_input(
                                "↳ If 'Other' role selected above, specify custom role:",
                                value=ex_data.get("Process Owner") if (ex_data.get("Process Owner") not in owner_options) else "",
                                placeholder="e.g. Operations Director",
                                key=f"qa_{sec_id}_owner_custom"
                            )
                            owner_role = custom_owner.strip() if ("other" in owner_sel.lower() and custom_owner.strip()) else owner_sel
                        
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
                            
                            # Prepopulate from existing section data if not already modified in session
                            existing_field_val = ""
                            if existing_sec:
                                if sec_config["type"] == "table" and existing_sec.structured_data:
                                    first_row = existing_sec.structured_data[0] if isinstance(existing_sec.structured_data, list) and len(existing_sec.structured_data) > 0 else {}
                                    for col_k, col_v in first_row.items():
                                        if col_k.lower() == fid.lower() or col_k.lower() in flabel.lower() or fid.lower() in col_k.lower():
                                            existing_field_val = str(col_v or "")
                                            break
                                elif sec_config["type"] == "text" and existing_sec.content:
                                    existing_field_val = existing_sec.content
                                elif sec_config["type"] in ["flowchart", "file"] and existing_sec.content:
                                    try:
                                        from config.guided_questions import parse_flowchart_steps
                                        res = parse_flowchart_steps(existing_sec.content)
                                        if isinstance(res, (tuple, list)) and len(res) == 2:
                                            p_steps, p_decs = res
                                        else:
                                            p_steps, p_decs = [], []
                                        if fid == "steps" and p_steps:
                                            existing_field_val = "\n".join(p_steps)
                                        elif fid == "decisions" and p_decs:
                                            existing_field_val = "\n".join(p_decs)
                                    except Exception:
                                        pass
                            
                            if ftype == "date":
                                def_date = datetime.date.today()
                                if existing_field_val:
                                    try:
                                        def_date = datetime.date.fromisoformat(str(existing_field_val).split("T")[0])
                                    except Exception:
                                        pass
                                if k in st.session_state and not isinstance(st.session_state[k], (datetime.date, datetime.datetime)):
                                    del st.session_state[k]
                                return st.date_input(flabel, value=def_date, key=k, help=fhelp)

                            elif ftype == "select":
                                opts = field_dict.get("options", [])
                                if not opts:
                                    opts = ["N/A"]
                                d_idx = 0
                                def_choice = existing_field_val or field_dict.get("default", "")
                                if def_choice in opts:
                                    d_idx = opts.index(def_choice)
                                elif def_choice and any("other" in str(o).lower() for o in opts):
                                    other_opt = next((o for o in opts if "other" in str(o).lower()), None)
                                    if other_opt:
                                        d_idx = opts.index(other_opt)
                                
                                # Protect against Streamlit ValueError if session_state has a value not in opts
                                if k in st.session_state and st.session_state[k] not in opts:
                                    del st.session_state[k]

                                sel = st.selectbox(flabel, options=opts, index=d_idx, key=k, help=fhelp)
                                if any("other" in str(o).lower() for o in opts):
                                    custom_k = f"{k}_custom"
                                    if custom_k not in st.session_state and existing_field_val and existing_field_val not in opts:
                                        st.session_state[custom_k] = existing_field_val
                                    custom = st.text_input(f"↳ If Other, specify {flabel.split('(')[0].strip()}:", placeholder="e.g. Lead Coordinator / External Auditor", key=custom_k)
                                    if "other" in str(sel).lower() and custom.strip():
                                        return custom.strip()
                                return sel

                            elif ftype == "textarea":
                                if k not in st.session_state and existing_field_val:
                                    st.session_state[k] = existing_field_val
                                return st.text_area(flabel, placeholder=field_dict.get("placeholder", ""), height=80, key=k, help=fhelp)
                            else:
                                if k not in st.session_state and existing_field_val:
                                    st.session_state[k] = existing_field_val
                                return st.text_input(flabel, placeholder=field_dict.get("placeholder", ""), key=k, help=fhelp)

                        def get_qa_answer(field_dict):
                            fid = field_dict["id"]
                            k = f"qa_{sec_id}_{fid}"
                            val = render_qa_widget(field_dict)
                            if (val is None or (isinstance(val, str) and not val.strip())) and k in st.session_state:
                                if st.session_state[k]:
                                    val = st.session_state[k]
                            return str(val).strip() if val is not None else ""

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
                                    answers[f["id"]] = get_qa_answer(f)
                                with col2:
                                    answers[next_f["id"]] = get_qa_answer(next_f)
                                i += 2
                            else:
                                answers[f["id"]] = get_qa_answer(f)
                                i += 1

                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    
                    # Action buttons depending on section type inside the form
                    apply_btn = False
                    append_btn = False
                    flow_btn = False
                    apply_text_btn = False
                    ai_text_btn = False

                    if sec_config["type"] == "table":
                        multi_row_sections = ["1.12", "1.13", "1.5", "1.14", "1.15", "1.16", "1.17", "1.18", "1.19", "1.20", "1.21", "1.22"]
                        apply_btn = False
                        append_btn = False

                        existing_rows = existing_sec.structured_data if (existing_sec and existing_sec.structured_data) else []
                        num_existing = len(existing_rows)

                        if sec_id in multi_row_sections and num_existing > 0:
                            st.warning(
                                f"⚠️ **Table currently contains {num_existing} row{'s' if num_existing > 1 else ''}.**\n\n"
                                f"• **➕ Add as New Row (Recommended)**: Refines your answers with AI and appends as a new row (preserves existing {num_existing} rows).\n"
                                f"• **⚠️ Overwrite Entire Table**: Wipes out all {num_existing} row{'s' if num_existing > 1 else ''} and resets the table to only this single row."
                            )
                            confirm_overwrite = False
                            if num_existing >= 2:
                                confirm_overwrite = st.checkbox(
                                    f"⚠️ Confirm overwrite: Delete all {num_existing} existing rows and replace with this 1 row",
                                    key=f"confirm_overwrite_{sec_id}",
                                    value=False,
                                    help="Check this box only if you intentionally want to delete all current rows and replace them."
                                )
                            else:
                                confirm_overwrite = True

                            col_btn1, col_btn2 = st.columns([1, 1])
                            with col_btn1:
                                append_btn = st.form_submit_button(
                                    f"➕ Add as New Row (Keep {num_existing} rows)",
                                    type="primary",
                                    use_container_width=True,
                                    help="Refines your answers with AI and appends as a new row to the existing table."
                                )
                            with col_btn2:
                                apply_btn = st.form_submit_button(
                                    f"⚠️ Overwrite Entire Table ({num_existing} ➔ 1 row)",
                                    use_container_width=True,
                                    help=f"WARNING: Wipes out all {num_existing} rows and replaces with this single row."
                                )
                        elif sec_id in multi_row_sections:
                            col_btn1, col_btn2 = st.columns([1, 1])
                            with col_btn1:
                                apply_btn = st.form_submit_button("✨ Set Table (1st Row)", type="primary", use_container_width=True, help="Refines your answers with AI and populates the table.")
                            with col_btn2:
                                append_btn = st.form_submit_button("➕ Add as New Row", use_container_width=True, help="Refines your answers with AI and appends as a new row to the existing table.")
                            confirm_overwrite = True
                        else:
                            apply_btn = st.form_submit_button(f"✨ Apply to {sec_config['name']}", type="primary", use_container_width=True, help="Refines your answers with AI and populates the table.")
                            confirm_overwrite = True

                        # Handle Set / Overwrite Table
                        if apply_btn:
                            if num_existing >= 2 and not confirm_overwrite:
                                st.error(
                                    f"🛑 Overwrite Blocked to Prevent Data Loss: Your table currently has {num_existing} rows! "
                                    f"To keep your existing rows and add this new activity, please click '➕ Add as New Row'. "
                                    f"If you intentionally want to wipe all {num_existing} rows, check the 'Confirm overwrite' checkbox above and submit again."
                                )
                            else:
                                raw_rows = build_table_rows_from_answers(sec_id, answers)
                                with st.spinner("🤖 Refining answers, correcting typos, and setting table..."):
                                    from services.llm_service import get_llm_provider
                                    llm = get_llm_provider()
                                    final_rows = llm.refine_table_rows_with_ai(
                                        section_id=sec_id,
                                        section_config=sec_config,
                                        raw_rows=raw_rows,
                                        answers_dict=answers,
                                        process_name=current_note.process_name,
                                        team_name=current_note.team
                                    )

                                from core.rule_validator import RuleValidator
                                from models.schemas import ProcessSectionSchema
                                sec_schema = ProcessSectionSchema(section_id=sec_id, content="", structured_data=final_rows)
                                issues = RuleValidator().validate(sec_schema, config)
                                if issues:
                                    for issue in issues:
                                        st.error(f"❌ Validation Error: {issue}")
                                    if sec_id == "1.8":
                                        st.info("💡 **Requirement for End Point:** Exit Criteria must be descriptive (at least 4 words). Simply typing 'abc' or vague text is not accepted — specify what deliverable, authorization, or sign-off confirms completion.")
                                    elif sec_id == "1.7":
                                        st.info("💡 **Requirement for Start Point:** Entry Criteria must be descriptive (at least 4 words) describing verified prerequisite documents or authorizations.")
                                else:
                                    import copy
                                    # Snapshot existing rows for Undo
                                    if existing_sec and existing_sec.structured_data:
                                        st.session_state[f"undo_table_{sec_id}"] = copy.deepcopy(existing_sec.structured_data)

                                    if not existing_sec:
                                        existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=final_rows)
                                        db.add(existing_sec)
                                        existing_sections[sec_id] = existing_sec
                                    else:
                                        existing_sec.structured_data = final_rows
                                    db.commit()
                                    is_completed = True
                                    st.session_state[f"show_guide_{sec_id}"] = False
                                    st.session_state[f"is_editing_{sec_id}"] = False
                                    st.success(f"✅ {sec_config['name']} refined and saved to table!")
                                    st.rerun()

                        # Handle Add Row to Table
                        if append_btn:
                            raw_rows = build_table_rows_from_answers(sec_id, answers)
                            with st.spinner("🤖 Refining answers, correcting typos, and adding new row..."):
                                from services.llm_service import get_llm_provider
                                llm = get_llm_provider()
                                final_rows = llm.refine_table_rows_with_ai(
                                    section_id=sec_id,
                                    section_config=sec_config,
                                    raw_rows=raw_rows,
                                    answers_dict=answers,
                                    process_name=current_note.process_name,
                                    team_name=current_note.team
                                )

                            existing_rows = existing_sec.structured_data if (existing_sec and existing_sec.structured_data) else []
                            if sec_id == "1.13" and final_rows:
                                final_rows[0]["Sr. No."] = len(existing_rows) + 1
                            combined_rows = existing_rows + final_rows
                            from core.rule_validator import RuleValidator
                            from models.schemas import ProcessSectionSchema
                            sec_schema = ProcessSectionSchema(section_id=sec_id, content="", structured_data=combined_rows)
                            issues = RuleValidator().validate(sec_schema, config)
                            if issues:
                                for issue in issues:
                                    st.error(f"❌ Validation Error: {issue}")
                            else:
                                import copy
                                # Snapshot existing rows for Undo
                                if existing_sec and existing_sec.structured_data:
                                    st.session_state[f"undo_table_{sec_id}"] = copy.deepcopy(existing_sec.structured_data)

                                if not existing_sec:
                                    existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=combined_rows)
                                    db.add(existing_sec)
                                    existing_sections[sec_id] = existing_sec
                                else:
                                    existing_sec.structured_data = combined_rows
                                db.commit()
                                is_completed = True
                                st.session_state[f"show_guide_{sec_id}"] = False
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success(f"✅ New refined row added to {sec_config['name']} table!")
                                st.rerun()

                    elif sec_config["type"] == "flowchart":
                        col_fl1, col_fl2 = st.columns([1, 1])
                        with col_fl1:
                            flow_btn = st.form_submit_button("✨ Standard Generate from Steps", type="primary", use_container_width=True)
                        with col_fl2:
                            ai_flow_btn = st.form_submit_button("🤖 Ask AI to Draft & Polish Flowchart", use_container_width=True)

                        if flow_btn:
                            mermaid_code = build_mermaid_flowchart_from_answers(answers)
                            while "&amp;" in mermaid_code:
                                mermaid_code = mermaid_code.replace("&amp;", "&")
                            from core.rule_validator import RuleValidator
                            from models.schemas import ProcessSectionSchema
                            sec_schema = ProcessSectionSchema(section_id=sec_id, content=mermaid_code, structured_data=[])
                            issues = RuleValidator().validate(sec_schema, config)
                            if issues:
                                for issue in issues:
                                    st.error(f"❌ Validation Error: {issue}")
                            else:
                                if not existing_sec:
                                    existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=mermaid_code)
                                    db.add(existing_sec)
                                    existing_sections[sec_id] = existing_sec
                                else:
                                    existing_sec.content = mermaid_code
                                db.commit()
                                is_completed = True
                                st.session_state[f"show_guide_{sec_id}"] = False
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success("✅ Flowchart updated from your steps! Check preview below.")

                        if ai_flow_btn:
                            with st.spinner("🤖 AI is synthesizing an enterprise BPMN flowchart with boxes and decision diamonds..."):
                                from services.llm_service import get_llm_provider
                                llm = get_llm_provider()
                                raw_steps = answers.get("steps", "")
                                decisions = answers.get("decisions", "")
                                roles = answers.get("roles", "")
                                
                                # If raw_steps is brief, enrich with Section 1.12 Process Description if present
                                desc_sec = existing_sections.get("1.12")
                                if (not raw_steps or len(raw_steps.split()) < 5) and desc_sec and desc_sec.structured_data:
                                    steps_summary = "\n".join([f"Step {i}: {row.get('Activity', '')} ({row.get('Owner/Role', '')}) - {row.get('Description', '')[:100]}" for i, row in enumerate(desc_sec.structured_data, 1)])
                                    raw_steps = f"{raw_steps}\n\nActivities from Section 1.12:\n{steps_summary}"

                                mermaid_code = llm.assist_flowchart(
                                    draft_steps=raw_steps,
                                    decisions=decisions,
                                    roles=roles,
                                    process_name=current_note.process_name,
                                    team_name=current_note.team
                                )
                                while "&amp;" in mermaid_code:
                                    mermaid_code = mermaid_code.replace("&amp;", "&")

                                from core.rule_validator import RuleValidator
                                from models.schemas import ProcessSectionSchema
                                sec_schema = ProcessSectionSchema(section_id=sec_id, content=mermaid_code, structured_data=[])
                                issues = RuleValidator().validate(sec_schema, config)
                                if issues:
                                    for issue in issues:
                                        st.warning(f"⚠️ Note: {issue}")
                                if not existing_sec:
                                    existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=mermaid_code)
                                    db.add(existing_sec)
                                    existing_sections[sec_id] = existing_sec
                                else:
                                    existing_sec.content = mermaid_code
                                db.commit()
                                is_completed = True
                                st.session_state[f"show_guide_{sec_id}"] = False
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success("✅ Flowchart synthesized and polished by AI! Check the diagram below.")

                    elif sec_config["type"] == "text":
                        col_t1, col_t2 = st.columns([1, 1])
                        with col_t1:
                            apply_text_btn = st.form_submit_button("✨ Apply Answers to Section", type="primary", use_container_width=True)
                        with col_t2:
                            ai_text_btn = st.form_submit_button("🤖 Polish & Synthesize with AI", use_container_width=True)

                        if apply_text_btn:
                            from config.guided_questions import clean_heading_hashes
                            formatted_content = clean_heading_hashes(build_text_summary_from_answers(sec_id, answers), sec_id, sec_config['name'])
                            from core.rule_validator import RuleValidator
                            from models.schemas import ProcessSectionSchema
                            sec_schema = ProcessSectionSchema(section_id=sec_id, content=formatted_content, structured_data=[])
                            issues = RuleValidator().validate(sec_schema, config)
                            if issues:
                                for issue in issues:
                                    st.error(f"❌ Validation Error: {issue}")
                            else:
                                if not existing_sec:
                                    existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=formatted_content)
                                    db.add(existing_sec)
                                    existing_sections[sec_id] = existing_sec
                                else:
                                    existing_sec.content = formatted_content
                                db.commit()
                                is_completed = True
                                st.session_state[f"show_guide_{sec_id}"] = False
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success("✅ Section content updated from your answers! Check preview below.")
                                st.rerun()

                        if ai_text_btn:
                            from services.llm_service import get_llm_provider
                            llm = get_llm_provider()
                            raw_notes = build_text_summary_from_answers(sec_id, answers)
                            with st.spinner("AI is analyzing your input for completeness..."):
                                clarifications = llm.detect_clarifications_needed(sec_id, sec_config, raw_notes, team_name=current_note.team)

                            if clarifications:
                                st.session_state[f"qa_clarify_{sec_id}"] = {
                                    "questions": clarifications,
                                    "raw_notes": raw_notes
                                }
                                st.rerun()
                            else:
                                with st.spinner("AI is synthesizing professional enterprise content..."):
                                    from config.guided_questions import clean_heading_hashes
                                    gen_result = clean_heading_hashes(llm.generate_section_from_qa(sec_id, sec_config, raw_notes, team_name=current_note.team), sec_id, sec_config['name'])
                                    if not existing_sec:
                                        existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=gen_result)
                                        db.add(existing_sec)
                                        existing_sections[sec_id] = existing_sec
                                    else:
                                        existing_sec.content = gen_result
                                    db.commit()
                                    is_completed = True
                                    st.session_state[f"show_guide_{sec_id}"] = False
                                    st.session_state[f"is_editing_{sec_id}"] = False
                                    st.session_state.pop(f"qa_clarify_{sec_id}", None)
                                    st.success("✅ Section synthesized with AI! Check preview below.")
                                    st.rerun()

                active_clarify = st.session_state.get(f"qa_clarify_{sec_id}")
                if active_clarify and active_clarify.get("questions"):
                    questions = active_clarify["questions"]
                    raw_notes = active_clarify["raw_notes"]

                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%); border: 1.5px solid #F59E0B; border-radius: 8px; padding: 14px 18px; margin: 14px 0 10px 0;">
                            <div style="font-weight: 700; color: #92400E; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                                <span>💡</span> <span>AI Co-pilot: Clarification Needed for {sec_config['name']}</span>
                            </div>
                            <div style="font-size: 12.5px; color: #78350F; margin-top: 4px; line-height: 1.5;">
                                To customize this section specifically to your organization and achieve audit compliance, please provide quick answers:
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    for idx, q in enumerate(questions, start=1):
                        st.markdown(f"<div style='font-size: 13px; font-weight: 600; color: #1E293B; margin: 6px 0 3px 0;'>{idx}. {q}</div>", unsafe_allow_html=True)

                    clarify_answer = st.text_area(
                        "Your quick answers or extra keywords:",
                        key=f"input_clarify_{sec_id}",
                        placeholder="e.g., Covers Nashik and Thane rural districts; final authorization by Program Director.",
                        height=90
                    )

                    c_col1, c_col2, c_col3 = st.columns([2, 2, 1])
                    with c_col1:
                        if st.button("✨ Synthesize with Clarifications", key=f"btn_apply_clarify_{sec_id}", type="primary", use_container_width=True):
                            from services.llm_service import get_llm_provider
                            from config.guided_questions import clean_heading_hashes
                            llm = get_llm_provider()

                            enriched_notes = raw_notes
                            if clarify_answer.strip():
                                q_summary = "\\n".join([f"- Q: {q}" for q in questions])
                                enriched_notes += f"\\n\\nClarification Answers Provided by Creator:\\n{q_summary}\\nCreator Responses: {clarify_answer.strip()}"

                            with st.spinner("AI is synthesizing customized enterprise content..."):
                                gen_result = clean_heading_hashes(llm.generate_section_from_qa(sec_id, sec_config, enriched_notes, team_name=current_note.team), sec_id, sec_config['name'])
                                if not existing_sec:
                                    existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=gen_result)
                                    db.add(existing_sec)
                                    existing_sections[sec_id] = existing_sec
                                else:
                                    existing_sec.content = gen_result
                                db.commit()
                                is_completed = True
                                st.session_state[f"show_guide_{sec_id}"] = False
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.session_state.pop(f"qa_clarify_{sec_id}", None)
                                st.success("✅ Section synthesized with your clarifications! Check preview below.")
                                st.rerun()

                    with c_col2:
                        if st.button("⏩ Skip & Use Standard Defaults", key=f"btn_skip_clarify_{sec_id}", use_container_width=True):
                            from services.llm_service import get_llm_provider
                            from config.guided_questions import clean_heading_hashes
                            llm = get_llm_provider()
                            with st.spinner("AI is synthesizing standard enterprise content..."):
                                gen_result = clean_heading_hashes(llm.generate_section_from_qa(sec_id, sec_config, raw_notes, team_name=current_note.team), sec_id, sec_config['name'])
                                if not existing_sec:
                                    existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=gen_result)
                                    db.add(existing_sec)
                                    existing_sections[sec_id] = existing_sec
                                else:
                                    existing_sec.content = gen_result
                                db.commit()
                                is_completed = True
                                st.session_state[f"show_guide_{sec_id}"] = False
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.session_state.pop(f"qa_clarify_{sec_id}", None)
                                st.success("✅ Section synthesized with AI! Check preview below.")
                                st.rerun()

                    with c_col3:
                        if st.button("✖️ Cancel", key=f"btn_cancel_clarify_{sec_id}", use_container_width=True):
                            st.session_state.pop(f"qa_clarify_{sec_id}", None)
                            st.rerun()

                if is_completed:
                    if st.button("✖️ Collapse Guided Form", key=f"btn_close_expander_{sec_id}"):
                        st.session_state[f"show_guide_{sec_id}"] = False
                        st.session_state.pop(f"qa_clarify_{sec_id}", None)
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
                    from config.guided_questions import clean_heading_hashes, render_section_preview_html
                    clean_display = clean_heading_hashes(existing_sec.content, sec_id, sec_config['name'])
                    preview_html = render_section_preview_html(clean_display)
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
                        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px; line-height: 1.6; color: #1E293B; font-size: 13.5px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">{preview_html}</div>
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
                        st.markdown(f'<div style="font-weight: 700; font-size: 15px; color: #1E293B; margin-bottom: 8px;">✏️ Editing {sec_config["name"]}:</div>', unsafe_allow_html=True)
                    with col_h2:
                        if is_completed and st.button("✖️ Cancel / Done", key=f"btn_cancel_txt_{sec_id}", use_container_width=True):
                            st.session_state[f"is_editing_{sec_id}"] = False
                            st.rerun()

                    with st.form(f"form_{sec_id}"):
                        from config.guided_questions import clean_heading_hashes
                        val = clean_heading_hashes(existing_sec.content, sec_id, sec_config['name']) if existing_sec else ""
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
                                raw_suggestion = llm.generate_suggestion(sec_config, context_list, user_draft=content)
                                suggestion = clean_heading_hashes(raw_suggestion, sec_id, sec_config['name'])
                                st.session_state[f"ai_suggestion_{sec_id}"] = suggestion

                        curr_sug = st.session_state.get(f"ai_suggestion_{sec_id}")
                        if curr_sug:
                            st.info("💡 **AI Suggestion:** Click the copy button (`📋`) in the top-right corner of the box below to copy, then paste it into the editor above:")
                            st.code(curr_sug, language=None)

                        if save_btn:
                            from core.rule_validator import RuleValidator
                            from models.schemas import ProcessSectionSchema
                            cleaned_content = clean_heading_hashes(content, sec_id, sec_config['name'])
                            sec_schema = ProcessSectionSchema(section_id=sec_id, content=cleaned_content, structured_data=[])
                            issues = RuleValidator().validate(sec_schema, config)
                
                            if issues:
                                for issue in issues:
                                    st.error(f"Validation Error: {issue}")
                            else:
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=cleaned_content)
                                    db.add(new_sec)
                                else:
                                    existing_sec.content = cleaned_content
                                db.commit()
                                st.session_state.pop(f"ai_suggestion_{sec_id}", None)
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success(f"Section {sec_id} saved successfully!")
                                st.rerun()

            elif sec_config["type"] == "table":
                # Table Undo & Redo Banner
                undo_rows = st.session_state.get(f"undo_table_{sec_id}")
                redo_rows = st.session_state.get(f"redo_table_{sec_id}")
                if undo_rows is not None:
                    u_col1, u_col2 = st.columns([3, 1])
                    with u_col1:
                        st.warning(f"↩️ **Undo Snapshot Available:** A previous table version with **{len(undo_rows)} rows** is saved. Did you overwrite or lose rows by mistake?")
                    with u_col2:
                        if st.button(f"↩️ Undo & Restore ({len(undo_rows)} rows)", key=f"btn_undo_tbl_main_{sec_id}", type="secondary", use_container_width=True):
                            import copy
                            st.session_state[f"redo_table_{sec_id}"] = copy.deepcopy(existing_sec.structured_data if (existing_sec and existing_sec.structured_data) else [])
                            existing_sec.structured_data = copy.deepcopy(undo_rows)
                            db.commit()
                            del st.session_state[f"undo_table_{sec_id}"]
                            st.success(f"✅ Successfully restored previous table with {len(undo_rows)} rows!")
                            st.rerun()
                elif redo_rows is not None:
                    r_col1, r_col2 = st.columns([3, 1])
                    with r_col1:
                        st.info(f"↪️ **Redo Snapshot Available:** You can reapply the state with **{len(redo_rows)} rows**.")
                    with r_col2:
                        if st.button(f"↪️ Redo ({len(redo_rows)} rows)", key=f"btn_redo_tbl_main_{sec_id}", type="secondary", use_container_width=True):
                            import copy
                            st.session_state[f"undo_table_{sec_id}"] = copy.deepcopy(existing_sec.structured_data if (existing_sec and existing_sec.structured_data) else [])
                            existing_sec.structured_data = copy.deepcopy(redo_rows)
                            db.commit()
                            del st.session_state[f"redo_table_{sec_id}"]
                            st.success(f"✅ Reapplied table with {len(redo_rows)} rows!")
                            st.rerun()

                # Special Quick-Recovery for Process Description (1.12) from Flowchart (1.11) or RACI Matrix (1.13)
                if sec_id == "1.12":
                    desc_rows = existing_sec.structured_data if (existing_sec and existing_sec.structured_data) else []
                    flow_sec = existing_sections.get("1.11")
                    f_steps = []
                    if flow_sec and flow_sec.content:
                        try:
                            from config.guided_questions import parse_flowchart_steps
                            res = parse_flowchart_steps(flow_sec.content)
                            if isinstance(res, (tuple, list)) and len(res) == 2:
                                f_steps, _ = res
                        except Exception:
                            pass

                    raci_sec = existing_sections.get("1.13")
                    raci_rows = raci_sec.structured_data if (raci_sec and raci_sec.structured_data) else []

                    if len(f_steps) >= 2 or len(raci_rows) >= 2:
                        cols_rec = st.columns(2 if (len(f_steps) >= 2 and len(raci_rows) >= 2) else 1)
                        col_idx = 0
                        if len(f_steps) >= 2:
                            with cols_rec[col_idx]:
                                if st.button(f"🔄 Recover All {len(f_steps)} Activities from Flowchart (1.11)", key="btn_rec_112_from_flow", use_container_width=True, help="Reconstructs all activities and roles from your Flowchart into Section 1.12 with full standard details"):
                                    import copy
                                    import re
                                    if existing_sec and existing_sec.structured_data:
                                        st.session_state["undo_table_1.12"] = copy.deepcopy(existing_sec.structured_data)
                                    recovered = []
                                    for i, raw_step in enumerate(f_steps, start=1):
                                        m = re.match(r'^(?:\d+[\.\)]\s*)?(.*?)(?:<br\s*/?>\s*Owner:\s*(.*?))?$', raw_step, re.IGNORECASE)
                                        act_name = m.group(1).strip() if m else raw_step.strip()
                                        act_owner = m.group(2).strip() if (m and m.group(2)) else "Operations Lead"
                                        recovered.append({
                                            "Activity": act_name,
                                            "Description": (
                                                f"1. Inputs: District school registry, application records, and prerequisite authorizations.\n"
                                                f"2. Sub-steps:\n1. Verify stage prerequisites.\n2. Execute {act_name} per established protocol.\n3. Log progress in MIS.\n"
                                                f"3. Tools & Systems: Partner School Portal, Excel Tracker, MIS\n"
                                                f"4. Stakeholders & Hand-offs: Handed over from stage executor to next sequential milestone owner\n"
                                                f"5. Expected Deliverable: Verified and approved {act_name} dossier\n"
                                                f"6. Checks & Validations: Managerial sign-off and validation against standard checklist"
                                            ),
                                            "Owner/Role": act_owner,
                                            "TAT": "2 Business Days"
                                        })
                                    if not existing_sec:
                                        existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id="1.12", structured_data=recovered)
                                        db.add(existing_sec)
                                        existing_sections["1.12"] = existing_sec
                                    else:
                                        existing_sec.structured_data = recovered
                                    db.commit()
                                    st.success(f"✅ Reconstructed all {len(recovered)} activities from Flowchart into Section 1.12!")
                                    st.rerun()
                            col_idx += 1
                        if len(raci_rows) >= 2 and col_idx < len(cols_rec):
                            with cols_rec[col_idx]:
                                if st.button(f"🔄 Recover All {len(raci_rows)} Activities from RACI Matrix (1.13)", key="btn_rec_112_from_raci", use_container_width=True, help="Reconstructs Section 1.12 activities from RACI"):
                                    import copy
                                    if existing_sec and existing_sec.structured_data:
                                        st.session_state["undo_table_1.12"] = copy.deepcopy(existing_sec.structured_data)
                                    recovered = []
                                    for i, r_item in enumerate(raci_rows, start=1):
                                        act_name = r_item.get("Activity name") or r_item.get("Activity") or f"Activity {i}"
                                        act_desc = r_item.get("Activity description") or f"Execute {act_name} per operating protocol."
                                        act_owner = r_item.get("Responsible") or "Operations Lead"
                                        act_tat = r_item.get("Timeline") or "2 Business Days"
                                        recovered.append({
                                            "Activity": act_name,
                                            "Description": act_desc if len(str(act_desc).split()) >= 10 else (
                                                f"1. Inputs: District school registry, application records, and prerequisite authorizations.\n"
                                                f"2. Sub-steps:\n1. Execute {act_name}.\n2. Log progress.\n"
                                                f"3. Tools & Systems: Operations MIS, Excel\n"
                                                f"4. Stakeholders & Hand-offs: Handed to next stage owner\n"
                                                f"5. Expected Deliverable: Verified {act_name} dossier\n"
                                                f"6. Checks & Validations: Managerial verification"
                                            ),
                                            "Owner/Role": act_owner,
                                            "TAT": act_tat
                                        })
                                    if not existing_sec:
                                        existing_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id="1.12", structured_data=recovered)
                                        db.add(existing_sec)
                                        existing_sections["1.12"] = existing_sec
                                    else:
                                        existing_sec.structured_data = recovered
                                    db.commit()
                                    st.success(f"✅ Reconstructed all {len(recovered)} activities from RACI into Section 1.12!")
                                    st.rerun()

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
                            import copy
                            if existing_sec and existing_sec.structured_data:
                                st.session_state[f"undo_table_{sec_id}"] = copy.deepcopy(existing_sec.structured_data)
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
                        st.markdown(f'<div style="font-weight: 700; font-size: 15px; color: #1E293B; margin-bottom: 8px;">✏️ Editing {sec_config["name"]} Table:</div>', unsafe_allow_html=True)
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
                                import copy
                                if existing_sec and existing_sec.structured_data:
                                    st.session_state[f"undo_table_{sec_id}"] = copy.deepcopy(existing_sec.structured_data)
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
                        while "&amp;" in current_chart:
                            current_chart = current_chart.replace("&amp;", "&")
                        render_mermaid_flowchart(current_chart)

                        from config.guided_questions import parse_flowchart_steps, build_mermaid_flowchart_from_answers
                        p_steps, p_decs = [], []
                        try:
                            res = parse_flowchart_steps(current_chart)
                            if isinstance(res, (tuple, list)) and len(res) == 2:
                                p_steps, p_decs = res
                        except Exception:
                            pass
                        if p_steps:
                            with st.expander("✏️ Quick Edit Flowchart Step Text & Labels (No Code Required)", expanded=True):
                                st.markdown("Modify the text inside any flowchart box below. Long conversational sentences can be split into crisp steps automatically with AI:")
                                with st.form(f"form_quick_flow_edit_{sec_id}"):
                                    updated_steps = []
                                    for s_i, s_t in enumerate(p_steps):
                                        clean_s_t = str(s_t).replace("&amp;", "&")
                                        new_t = st.text_input(f"Step {s_i + 1} Text:", value=clean_s_t, key=f"qe_step_txt_{sec_id}_{s_i}", help="Edit the wording inside this process step box.")
                                        updated_steps.append(new_t.replace("&amp;", "&"))
                                    
                                    curr_dec = p_decs[0].replace("&amp;", "&") if p_decs else "Verification Criteria Met?"
                                    updated_dec = st.text_input("Decision Diamond Criteria:", value=curr_dec, key=f"qe_dec_txt_{sec_id}", help="Edit the question inside the decision diamond.").replace("&amp;", "&")
                                    
                                    qe_c1, qe_c2 = st.columns([1, 1])
                                    with qe_c1:
                                        qe_save = st.form_submit_button("💾 Save Updated Step Text", type="primary", use_container_width=True)
                                    with qe_c2:
                                        qe_ai = st.form_submit_button("🤖 AI Shorten & Split Big Sentences", use_container_width=True)
                                    
                                    if qe_save:
                                        valid_steps = [st.strip().replace("&amp;", "&") for st in updated_steps if st.strip()]
                                        new_flow_code = build_mermaid_flowchart_from_answers({
                                            "steps": "\n".join(valid_steps),
                                            "decisions": updated_dec
                                        })
                                        while "&amp;" in new_flow_code:
                                            new_flow_code = new_flow_code.replace("&amp;", "&")
                                        if existing_sec:
                                            existing_sec.content = new_flow_code
                                        else:
                                            new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=new_flow_code)
                                            db.add(new_sec)
                                        db.commit()
                                        st.success("✅ Flowchart steps updated successfully!")
                                        st.rerun()

                                    if qe_ai:
                                        with st.spinner("🤖 AI is splitting big sentences and refining flowchart boxes..."):
                                            from services.llm_service import get_llm_provider
                                            llm = get_llm_provider()
                                            valid_steps = [st.strip().replace("&amp;", "&") for st in updated_steps if st.strip()]
                                            improved_flow_code = llm.assist_flowchart(
                                                draft_steps="\n".join(valid_steps),
                                                decisions=updated_dec,
                                                process_name=current_note.process_name,
                                                team_name=current_note.team
                                            )
                                            while "&amp;" in improved_flow_code:
                                                improved_flow_code = improved_flow_code.replace("&amp;", "&")
                                            if existing_sec:
                                                existing_sec.content = improved_flow_code
                                            else:
                                                new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=improved_flow_code)
                                                db.add(new_sec)
                                            db.commit()
                                            st.success("✅ Flowchart polished and split with AI!")
                                            st.rerun()

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
                            try:
                                from config.guided_questions import parse_flowchart_steps
                                res = parse_flowchart_steps(current_chart)
                                if isinstance(res, (tuple, list)) and len(res) == 2:
                                    p_steps, p_decs = res
                                    if p_steps:
                                        st.session_state[f"qa_{sec_id}_steps"] = "\n".join(p_steps)
                                    if p_decs:
                                        st.session_state[f"qa_{sec_id}_decisions"] = "\n".join(p_decs)
                            except Exception:
                                pass
                            st.session_state[f"show_guide_{sec_id}"] = True
                            st.rerun()
                else:
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.markdown(f'<div style="font-weight: 700; font-size: 15px; color: #1E293B; margin-bottom: 8px;">✏️ Editing {sec_config["name"]}:</div>', unsafe_allow_html=True)
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
                                        while "&amp;" in mermaid_code:
                                            mermaid_code = mermaid_code.replace("&amp;", "&")
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
                                key=f"txt_manual_mermaid_{sec_id}",
                                help="Edit the diagram nodes, decision branches, and handoffs."
                            )
                            col_sc1, col_sc2 = st.columns([1, 1])
                            with col_sc1:
                                save_chart_btn = st.form_submit_button("Save Flowchart Diagram", type="primary", use_container_width=True)
                            with col_sc2:
                                ai_assist_btn = st.form_submit_button("🤖 AI Assistant (Refine / Convert Notes to Flowchart)", use_container_width=True)

                            if save_chart_btn:
                                while "&amp;" in chart_content:
                                    chart_content = chart_content.replace("&amp;", "&")
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=chart_content)
                                    db.add(new_sec)
                                else:
                                    existing_sec.content = chart_content
                                db.commit()
                                st.session_state[f"is_editing_{sec_id}"] = False
                                st.success("Flowchart saved successfully!")
                                st.rerun()

                            if ai_assist_btn:
                                with st.spinner("🤖 AI is refining your flowchart syntax, boxes, and decision diamonds..."):
                                    from services.llm_service import get_llm_provider
                                    llm = get_llm_provider()
                                    improved_code = llm.assist_flowchart(
                                        draft_steps=chart_content,
                                        process_name=current_note.process_name,
                                        team_name=current_note.team
                                    )
                                    while "&amp;" in improved_code:
                                        improved_code = improved_code.replace("&amp;", "&")
                                    if not existing_sec:
                                        new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=improved_code)
                                        db.add(new_sec)
                                    else:
                                        existing_sec.content = improved_code
                                    db.commit()
                                    st.session_state[f"is_editing_{sec_id}"] = False
                                    st.success("Flowchart polished with AI and saved successfully!")
                                    st.rerun()

                        if current_chart and not current_chart.endswith(('.png', '.jpg', '.pdf', '.docx', '.vsdx')):
                            st.markdown('<div style="font-weight: 700; font-size: 14px; color: #1E293B; margin: 10px 0 6px 0;">📊 Live Flowchart Preview:</div>', unsafe_allow_html=True)
                            render_mermaid_flowchart(current_chart)

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
                    set_active_section(tab_names[current_idx + 1])
                st.button("Next Section ➔", type="primary", use_container_width=True, on_click=go_next)
            else:
                if completed_count < total_count:
                    st.warning(f"You have entered data for {completed_count}/{total_count} sections ({pending_count} pending). Any section left blank will receive a 0% score in the audit.")
                elif needs_rev_count > 0:
                    st.info(f"💡 Note: {needs_rev_count} section(s) have detail gaps. Addressing them now will significantly improve your audit score.")
                if st.button("Proceed to Validation ➔", type="primary", use_container_width=True):
                    if current_note:
                        st.session_state.selected_note_id = current_note.id
                    st.switch_page("pages/3_Validation.py")

finally:
    db.close()
