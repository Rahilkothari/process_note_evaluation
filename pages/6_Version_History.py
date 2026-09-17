import streamlit as st
import pandas as pd
from models.database import get_db, ProcessNote, ProcessSection
from sqlalchemy.orm import Session
import difflib

st.title("Version History & Diffs")
st.markdown("Compare different versions of process notes.")

db: Session = next(get_db())

@st.cache_data(ttl=60)
def get_all_notes_history_metadata(_db: Session):
    notes = _db.query(ProcessNote.id, ProcessNote.process_name, ProcessNote.version, ProcessNote.status, ProcessNote.created_at).all()
    return [{"id": n.id, "process_name": n.process_name, "version": n.version, "status": n.status, "created_at": n.created_at} for n in notes]

notes_meta = get_all_notes_history_metadata(db)

if not notes_meta:
    st.info("No process notes found.")
    st.stop()

# Group by process_name (or document_id)
groups = {}
for n in notes_meta:
    key = n["process_name"]
    if key not in groups:
        groups[key] = []
    groups[key].append(n)

# Filter groups that have more than 1 version
multi_version_groups = {k: v for k, v in groups.items() if len(v) > 1}

if not multi_version_groups:
    st.info("No process notes with multiple versions found. (A note must be revised to have history).")
    st.stop()

selected_process = st.selectbox("Select Process", list(multi_version_groups.keys()))
process_notes = multi_version_groups[selected_process]
process_notes.sort(key=lambda x: x["created_at"])

options = [f"Version {n['version']} ({n['status']})" for n in process_notes]

col1, col2 = st.columns(2)
with col1:
    v1_idx = st.selectbox("Select Base Version", range(len(options)), format_func=lambda x: options[x], index=0)
with col2:
    v2_idx = st.selectbox("Select Compare Version", range(len(options)), format_func=lambda x: options[x], index=len(options)-1)

if v1_idx == v2_idx:
    st.warning("Please select two different versions to compare.")
    st.stop()

base_note_meta = process_notes[v1_idx]
compare_note_meta = process_notes[v2_idx]

base_note = db.query(ProcessNote).filter(ProcessNote.id == base_note_meta['id']).first()
compare_note = db.query(ProcessNote).filter(ProcessNote.id == compare_note_meta['id']).first()

st.markdown("---")
st.subheader("Comparison")

# Collect sections
base_sections = {s.section_id: s for s in base_note.sections}
compare_sections = {s.section_id: s for s in compare_note.sections}

all_section_ids = sorted(list(set(base_sections.keys()).union(set(compare_sections.keys()))), key=lambda x: float(x) if x.replace('.', '', 1).isdigit() else 999)

differ = difflib.HtmlDiff()

for sec_id in all_section_ids:
    s1 = base_sections.get(sec_id)
    s2 = compare_sections.get(sec_id)
    
    st.markdown(f"#### Section {sec_id}")
    
    c1 = s1.content if s1 and s1.content else ""
    c2 = s2.content if s2 and s2.content else ""
    
    if c1 != c2:
        st.markdown("**Content Changes:**")
        html_diff = differ.make_file(c1.splitlines(), c2.splitlines(), fromdesc=f"v{base_note.version}", todesc=f"v{compare_note.version}", context=True)
        # Clean up some html for streamlit display
        st.components.v1.html(html_diff, height=200, scrolling=True)
    else:
        st.write("*(No text changes)*")
        
    d1 = s1.structured_data if s1 and s1.structured_data else []
    d2 = s2.structured_data if s2 and s2.structured_data else []
    
    if d1 != d2:
        st.markdown("**Data Changes:**")
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption(f"v{base_note.version}")
            if d1:
                st.dataframe(pd.DataFrame(d1))
            else:
                st.write("Empty")
        with col_b:
            st.caption(f"v{compare_note.version}")
            if d2:
                st.dataframe(pd.DataFrame(d2))
            else:
                st.write("Empty")
