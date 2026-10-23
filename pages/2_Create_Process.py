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
    
        existing_sections = {s.section_id: s for s in current_note.sections}
        completed_count = len(existing_sections)
        total_count = len(sections)
    
        st.markdown(f"**Progress:** {completed_count} / {total_count} Sections Completed")
        st.progress(completed_count / total_count)
    
        if "current_section_edit" not in st.session_state:
            st.session_state["current_section_edit"] = f"{sections[0]['id']} {sections[0]['name']}"

        tab_names = [f"{sec['id']} {sec['name']}" for sec in sections]
    
        # Ensure current state is valid
        if st.session_state["current_section_edit"] not in tab_names:
            st.session_state["current_section_edit"] = tab_names[0]
        
        selected_tab = st.selectbox("📌 Select a Section to Fill Out:", tab_names, key="current_section_edit")
    
        sec_config = sections[tab_names.index(selected_tab)]
    
        help_text = sec_config.get('help_text', 'No instructions provided.')
        example_text = sec_config.get('example', '')

        st.info(f"**Instructions for {sec_config['name']}:** {help_text}")
        if example_text:
            st.markdown(f"> *{example_text}*")

        sec_id = sec_config['id']
        existing_sec = existing_sections.get(sec_id)

        # AI Process Co-pilot: Guided Q&A Assistant for Creator
        from config.guided_questions import SECTION_GUIDED_QUESTIONS
        gq = SECTION_GUIDED_QUESTIONS.get(sec_id)
        if gq:
            with st.expander(f"💡 Need Help? AI Process Co-pilot ({gq['title']})", expanded=False):
                st.markdown("**Answer these simple questions to auto-generate this section:**")
                for q in gq["questions"]:
                    st.markdown(f"- *{q}*")
                
                qa_text = st.text_area(
                    "Your rough notes / answers to the above questions:",
                    placeholder=gq.get("placeholder", "Type your points or bullets here..."),
                    key=f"qa_input_{sec_id}",
                    height=110
                )
                if st.button("✨ Auto-Generate & Apply to Section", key=f"btn_qa_{sec_id}", type="secondary"):
                    if not qa_text.strip():
                        st.warning("Please type your rough notes or answers before generating.")
                    else:
                        with st.spinner("AI is synthesizing professional enterprise content..."):
                            from services.llm_service import get_llm_provider
                            llm = get_llm_provider()
                            gen_result = llm.generate_section_from_qa(sec_id, sec_config, qa_text, team_name=current_note.team)
                            
                            if sec_config["type"] == "text":
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=gen_result)
                                    db.add(new_sec)
                                else:
                                    existing_sec.content = gen_result
                                db.commit()
                            elif sec_config["type"] == "table" and isinstance(gen_result, list):
                                if not existing_sec:
                                    new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, structured_data=gen_result)
                                    db.add(new_sec)
                                else:
                                    existing_sec.structured_data = gen_result
                                db.commit()
                            st.success("Section updated successfully from your answers! Review below.")
                            st.rerun()

        with st.container():
            if sec_config["type"] == "text":
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
                            st.success(f"Section {sec_id} saved successfully!")

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
                            if "Sr. No." in df.columns: df.at[1, "Sr. No."] = 1
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
                    elif f in ["Responsible", "Accountable", "Consulted by", "Informed to"]:
                        column_config[f] = st.column_config.TextColumn(f, help=f"Enter designation/job title for {f} (e.g. Manager, PH, Vertical Lead)")
                    else:
                        column_config[f] = st.column_config.TextColumn(f)

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
                            st.success(f"Section {sec_id} saved successfully!")

            elif sec_config["type"] in ["file", "flowchart"]:
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
                                    st.success("Flowchart generated successfully!")
                                    st.rerun()

                    current_chart = existing_sec.content if existing_sec else ""
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
