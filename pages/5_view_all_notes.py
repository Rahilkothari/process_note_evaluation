import streamlit as st
from models.database import get_db, ProcessNote, ProcessSection
from sqlalchemy.orm import Session
import pandas as pd

st.set_page_config(page_title="View All Notes", layout="wide")
from core.ui_utils import inject_custom_css
from core.ui_utils import inject_custom_css


st.title("View All Process Notes")
st.markdown("Read-only access to all process notes in the system.")

db: Session = next(get_db())

# Fetch all notes
notes = db.query(ProcessNote).all()

if not notes:
    st.info("No process notes found in the database.")
    st.stop()

note_options = {f"[{n.id}] {n.process_name} (v{n.version}) - {n.status.replace('_', ' ')}": n for n in notes}

default_idx = 0
if "selected_note_id" in st.session_state:
    for i, key in enumerate(note_options.keys()):
        if note_options[key].id == st.session_state.selected_note_id:
            default_idx = i
            break
            
selected = st.selectbox("Select Process Note to View", list(note_options.keys()), index=default_idx)
current_note = note_options[selected]

st.markdown("<hr>", unsafe_allow_html=True)

# Determine badge class based on status
status_class = "badge-draft"
if current_note.status == "APPROVED": status_class = "badge-pass"
elif current_note.status == "WARNING": status_class = "badge-warning"
elif current_note.status == "NEEDS_REVISION": status_class = "badge-fail"
elif current_note.status == "UNDER_REVIEW": status_class = "badge-review"

st.markdown(f"### {current_note.process_name}")
st.markdown(f"**Status:** <span class='badge {status_class}'>{current_note.status.replace('_', ' ')}</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Team:** {current_note.team}")
    st.write(f"**Version:** {current_note.version}")
    st.write(f"**Effective Date:** {current_note.effective_date}")
    st.write(f"**Next Review:** {current_note.next_review_date}")
with col2:
    st.write(f"**Owner:** {current_note.process_owner}")
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
            df.index = df.index + 1
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Section saved but empty.")
    else:
        st.info("Not filled.")
    st.markdown("<br>", unsafe_allow_html=True)
