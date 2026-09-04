import streamlit as st
import yaml
import os
import pandas as pd
import json
from models.database import get_db, ProcessNote, ProcessSection, User
from sqlalchemy.orm import Session


from core.ui_utils import inject_custom_css
from core.ui_utils import inject_custom_css


st.title("Create / Edit Process Note")
st.markdown("Follow the instructions in each section to accurately document your team's process.")

def load_sections_config():
    with open("config/sections.yaml", "r") as f:
        return yaml.safe_load(f)

config = load_sections_config()
sections = config.get("sections", [])

db: Session = next(get_db())

# Select existing draft or create new
st.markdown("### Note Selection")
existing_notes = db.query(ProcessNote).filter(ProcessNote.status.in_(["DRAFT", "NEEDS_REVISION"])).all()
note_options = {"Create New Process Note": None}
for n in existing_notes:
    note_options[f"[{n.id}] {n.process_name} (v{n.version}) - {n.status}"] = n

note_keys = list(note_options.keys())
default_key = st.session_state.get("selected_note_key", "Create New Process Note")
try:
    default_index = note_keys.index(default_key)
except ValueError:
    default_index = 0

selected_option = st.selectbox("Select a Note to Edit or Create a New One", note_keys, index=default_index)
st.session_state.selected_note_key = selected_option
current_note = note_options[selected_option]

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
        
        st.markdown("<p style='font-size: 13px; color: #64748B; margin-top: 8px;'>* Required fields</p>", unsafe_allow_html=True)
        save_basic = st.form_submit_button("Next ➔", type="primary")

if save_basic:
    if not process_name or not process_name.strip():
        st.error("Process Name is a required field. Please provide it before proceeding.")
        st.stop()
    if not team or not team.strip():
        st.error("Team is a required field. Please provide it before proceeding.")
        st.stop()
        
    # Validation passed
    if current_note is None:
        current_note = ProcessNote(
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
            created_by=st.session_state.current_user_id
        )
        db.add(current_note)
        db.commit()
        db.refresh(current_note)
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
    st.markdown("Scroll down to fill out all sections of the process note. **Read the instruction box** in each section before entering data.")
    
    existing_sections = {s.section_id: s for s in current_note.sections}
    
    if "current_section_index" not in st.session_state:
        st.session_state.current_section_index = 0

    st.progress((st.session_state.current_section_index + 1) / len(sections))
    st.markdown(f"**Section {st.session_state.current_section_index + 1} of {len(sections)}**")
    
    sec_config = sections[st.session_state.current_section_index]
    
    st.markdown(f"### {sec_config['id']} {sec_config['name']}")
    
    help_text = sec_config.get('help_text', 'No instructions provided.')
    example_text = sec_config.get('example', '')
    
    example_html = ""
    if example_text:
        example_html = f"""<div style="margin-top: 12px; background-color: #EEF2FF; padding: 8px 12px; border-radius: 6px; font-style: italic; color: #3730A3; white-space: pre-wrap; font-size: 13px;">
{example_text}
</div>"""
        
    st.markdown(f"""<div style="background-color: #F8FAFC; border-left: 4px solid #4F46E5; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px; font-size: 14px; color: #334155;">
<div style="margin-bottom: 4px;"><b>Instructions:</b> {help_text}</div>
{example_html}
</div>""", unsafe_allow_html=True)
    
    sec_id = sec_config['id']
    existing_sec = existing_sections.get(sec_id)
    
    with st.container():
        with st.form(f"form_{sec_id}"):
            if sec_config["type"] == "text":
                val = existing_sec.content if existing_sec else ""
                content = st.text_area("Provide your detailed response below:", value=val, height=250)
                if st.form_submit_button("Save Section", type="primary"):
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
                    df.loc[1] = [None for _ in fields]
                
                column_config = {}
                for f in fields:
                    f_lower = f.lower()
                    if "date" in f_lower:
                        column_config[f] = st.column_config.DateColumn(f, format="YYYY-MM-DD")
                        # Strictly cast to datetime so Streamlit recognizes it as a DateColumn
                        df[f] = pd.to_datetime(df[f], errors='coerce').dt.date
                    elif "no." in f_lower or "tat" in f_lower:
                        column_config[f] = st.column_config.NumberColumn(f, step=1)
                        # Force pandas numeric type for Streamlit compatibility
                        df[f] = pd.to_numeric(df[f], errors='coerce')
                    elif f in ["Responsible (R)", "Accountable (A)", "Consulted (C)", "Informed (I)"]:
                        column_config[f] = st.column_config.SelectboxColumn(f, options=["Yes", "No"])
                    elif "level of risk" in f_lower:
                        column_config[f] = st.column_config.SelectboxColumn(f, options=["High", "Medium", "Low"])
                    else:
                        column_config[f] = st.column_config.TextColumn(f)

                st.markdown("Edit the table below:")
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"editor_{sec_id}", column_config=column_config)
                
                if st.form_submit_button("Save Section", type="primary"):
                    json_data = edited_df.to_dict(orient="records")
                    
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
            
            elif sec_config["type"] == "file":
                uploaded_file = st.file_uploader("Upload Process Flowchart", type=["png", "jpg", "jpeg", "pdf", "vsdx", "drawio", "docx"])
                if existing_sec and existing_sec.content:
                    st.info(f"Currently uploaded: {existing_sec.content}")
                    
                if st.form_submit_button("Save Section", type="primary"):
                    if uploaded_file is not None:
                        import os
                        os.makedirs("uploads", exist_ok=True)
                        file_path = os.path.join("uploads", uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        content_val = uploaded_file.name
                    else:
                        content_val = existing_sec.content if existing_sec else ""
                        
                    if not existing_sec:
                        new_sec = ProcessSection(process_note_id=current_note.id, process_name=current_note.process_name, section_id=sec_id, content=content_val)
                        db.add(new_sec)
                    else:
                        existing_sec.content = content_val
                    db.commit()
                    st.success(f"Section {sec_id} saved successfully! File: {content_val}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_space, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.session_state.current_section_index > 0:
            if st.button("Previous"):
                st.session_state.current_section_index -= 1
                st.rerun()
    with col_next:
        if st.session_state.current_section_index < len(sections) - 1:
            if st.button("Next", type="primary"):
                st.session_state.current_section_index += 1
                st.rerun()
        else:
            if st.button("Proceed to Validation", type="primary"):
                st.switch_page("pages/3_Validation.py")
