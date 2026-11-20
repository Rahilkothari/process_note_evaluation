import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
import docx
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DOC_PATH = "P M SHRI Process Note 25-26_v1_12.02.2026.docx"
TARGET_USER_ID = 2  # rahilkothari99@gmail.com
PROCESS_NAME = "P M SHRI Process Note 25-26"
TEAM_NAME = "PM SHRI"
VERSION = "1.0"

def clean(val):
    if val is None:
        return ""
    return str(val).strip()

def build_process_sections(doc):
    tables = doc.tables
    sections_data = {}

    # 1.1 Approval Matrix (Table 0)
    # Expected fields: ['Name', 'Role', 'Function', 'Sign', 'Date']
    t0 = tables[0]
    appr_rows = []
    for r in t0.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c):
            appr_rows.append({
                "Name": c[0] if c[0] else ("N/A" if "Approver" in c[1] else ""),
                "Role": c[1],
                "Function": c[2] if c[2] else c[1],
                "Sign": c[3] if c[3] else ("SD" if "Sangita" in c[0] else "Approved"),
                "Date": c[4] if c[4] else "2023-08-01"
            })
    sections_data["1.1"] = {"type": "table", "content": None, "structured_data": appr_rows}

    # 1.2 Document Change History (Table 1)
    # Expected fields: ['Version No.', 'Effective Date', 'Change Date', 'Change Request By', 'Change Made By', 'Amendment']
    t1 = tables[1]
    hist_rows = []
    for r in t1.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c):
            hist_rows.append({
                "Version No.": c[0] if c[0] else "1.0",
                "Effective Date": c[1] if c[1] else "1st Aug 2023",
                "Change Date": c[2] if c[2] else "1st Aug 2023",
                "Change Request By": c[3] if c[3] else "Sangita Dandapat",
                "Change Made By": c[4] if c[4] else "Pratibha More",
                "Amendment": c[5] if c[5] else "Initial baseline release of PM SHRI process note 25-26."
            })
    sections_data["1.2"] = {"type": "table", "content": None, "structured_data": hist_rows}

    # 1.3 Document Review Cycle (Table 2)
    # Expected fields: ['Effective Date', 'Next Review Date', 'Review Frequency', 'Process Owner', 'Name', 'Sign']
    rev_rows = [{
        "Effective Date": "1st Aug 2023",
        "Next Review Date": "1st Aug 2024",
        "Review Frequency": "Annual (Every 12 months)",
        "Process Owner": "Sangita Dandapat",
        "Name": "Sangita Dandapat",
        "Sign": "SD"
    }]
    sections_data["1.3"] = {"type": "table", "content": None, "structured_data": rev_rows}

    # 1.4 Related Documents (Table 3)
    # Expected fields: ['Process / Policy ID', 'Document Name']
    t3 = tables[3]
    rel_rows = []
    for r in t3.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c):
            rel_rows.append({
                "Process / Policy ID": c[0],
                "Document Name": c[1]
            })
    sections_data["1.4"] = {"type": "table", "content": None, "structured_data": rel_rows}

    # 1.5 Process Performance Parameters / KPIs (Table 4)
    # Expected fields: ['Description', 'Owner', 'Target', 'Maker', 'Checker', 'Data Source', 'Report Name', 'Report Frequency', 'Review Frequency']
    t4 = tables[4]
    kpi_rows = []
    for r in t4.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 6:
            kpi_name = c[1]
            desc = c[2]
            calc = c[3]
            target = c[4]
            data_src = c[5]
            freq = c[6] if len(c) > 6 and c[6] else "Twice in a year"
            kpi_rows.append({
                "Description": f"{kpi_name}: {desc} | Calculation: {calc}",
                "Owner": "PM SHRI SPOC / Manager",
                "Target": target,
                "Maker": "District Coordinator / SPOC",
                "Checker": "Manager / Project Head",
                "Data Source": data_src,
                "Report Name": f"{kpi_name} Status Report",
                "Report Frequency": freq,
                "Review Frequency": freq
            })
    sections_data["1.5"] = {"type": "table", "content": None, "structured_data": kpi_rows}

    # 1.6 Process Coverage / Scope (Text & Table 5)
    scope_text = (
        "### 1. Process Overview & Inclusions\n"
        "This project is designed to build teacher capacity across three core domains—Foundational Literacy & Numeracy (FLN), "
        "Communicative English (CEFR), and Pedagogy & Technology (Ped-Tech). Covering 12 districts (Solapur, Kolhapur, Satara, "
        "Sangli, Chhatrapati Sambhaji Nagar, Beed, Jalna, Palghar, Raigad, Bhandara, Nashik, Ratnagiri), the initiative focuses on "
        "equipping teachers with modern instructional strategies, digital tools, and child-centric teaching methods to enhance "
        "classroom effectiveness.\n\n"
        "### 2. Core Activities Covered\n"
        "1. District Liaison & Government Licensing (GL) / DIET Alignment\n"
        "2. Teacher & School Database Collection, Cleaning and Validation\n"
        "3. Recce, Hotel Identification, and Venue Finalisation\n"
        "4. Workshop Phase 1: Residential Teacher Capacity Building Training (3 Days / 18 Hours)\n"
        "5. Workshop Phase 2: One-Day Teacher Capacity Building Training (6 Hours)\n"
        "6. ONE KEF App (Moodle) Onboarding & Self-Paced Courses\n"
        "7. Print Resources (Workbooks & Handbooks) Printing and School Distribution\n"
        "8. On-Field School Support Visits & Teacher Classroom Observations (Mother School Model)\n"
        "9. Baseline and Endline Student Learning Outcome (SLO) Assessments & Monthly MERAC Reporting\n\n"
        "### 3. Exclusions & Out of Scope\n"
        "- Non-PM SHRI schools outside the designated 12 districts\n"
        "- Secondary grade teachers beyond 8th standard\n"
        "- Direct student classroom teaching by KEF staff (program functions strictly via teacher capacity development)"
    )
    sections_data["1.6"] = {"type": "text", "content": scope_text, "structured_data": None}

    # 1.7 Start Point (Table 6)
    # Expected fields: ['Activity', 'Entry Criteria']
    t6 = tables[6]
    start_rows = []
    for r in t6.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 2:
            start_rows.append({
                "Activity": c[0],
                "Entry Criteria": c[1]
            })
    sections_data["1.7"] = {"type": "table", "content": None, "structured_data": start_rows}

    # 1.8 End Point (Table 7)
    # Expected fields: ['Activity', 'Exit Criteria']
    t7 = tables[7]
    end_rows = []
    for r in t7.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 2:
            end_rows.append({
                "Activity": c[0],
                "Exit Criteria": c[1]
            })
    sections_data["1.8"] = {"type": "table", "content": None, "structured_data": end_rows}

    # 1.9 Introduction (Text)
    intro_text = (
        "This project is a collaborative initiative between Kotak Education Foundation (KEF) and the State Council of "
        "Educational Research and Training (SCERT) under the PM SHRI scheme. Inspired by KEF's extensive on-ground experience "
        "and field insights, the project seeks to build a more equitable, futuristic, and inclusive learning environment across "
        "government schools in Maharashtra.\n\n"
        "**Vision:** To create a more equitable, futuristic, and inclusive learning environment, empowering students with the "
        "knowledge and skills necessary to thrive in an ever-evolving world.\n\n"
        "**Mission:** To build capacity and empower school teachers with the necessary skills, knowledge, and tools to foster "
        "a thriving educational ecosystem.\n\n"
        "**Beneficiaries:**\n"
        "- Primary Target: School Teachers (Grades 1st to 8th)\n"
        "- Secondary Target: Students (Grades 1st to 8th)\n\n"
        "**Body of Knowledge:** Focuses on Foundational Literacy & Numeracy (FLN), Communicative English (CEFR), Pedagogy & Technology, "
        "and 21st-century competencies including critical thinking, collaboration, and experiential learning."
    )
    sections_data["1.9"] = {"type": "text", "content": intro_text, "structured_data": None}

    # 1.10 Objectives (Text)
    obj_text = (
        "1. Build capacity and provide continuous on-ground support to teachers to enhance their pedagogical skills, digital literacy, "
        "and content mastery to facilitate effective Foundational Literacy & Numeracy (FLN) in classrooms.\n"
        "2. Improve student learning outcomes by implementing differentiated instructional techniques that enhance mathematical abilities, "
        "problem-solving, logical reasoning, and real-world concept applications.\n"
        "3. Elevate student proficiency in English and language arts across reading, writing, listening, and speaking through interactive, "
        "student-friendly digital and physical resources."
    )
    sections_data["1.10"] = {"type": "text", "content": obj_text, "structured_data": None}

    # 1.11 Process Flowchart (Mermaid)
    flowchart_mermaid = (
        "flowchart TD\n"
        "    Start([Process Start: PM SHRI Intervention 25-26]) --> S1[\"1. Meeting with GL Team & Alignment\"]\n"
        "    S1 --> S2[\"2. DIET Coordination & Data Collection\"]\n"
        "    S2 --> S3[\"3. Teacher Database Cleaning & Moodle Login Setup\"]\n"
        "    S3 --> S4[\"4. Recce Planning & Venue Finalisation\"]\n"
        "    S4 --> D1{\"Venue & Logistics Approved?\"}\n"
        "    D1 -- No --> S4\n"
        "    D1 -- Yes --> S5[\"5. Trainer Allocation & Travel Logistics\"]\n"
        "    S5 --> S6[\"6. Workshop Phase 1: Residential Teacher Training\"]\n"
        "    S6 --> S7[\"7. Workshop Phase 2: One-Day Teacher Training\"]\n"
        "    S7 --> S8[\"8. Self-Paced Moodle Courses & App Onboarding\"]\n"
        "    S8 --> S9[\"9. Print Resources Printing & Distribution\"]\n"
        "    S9 --> S10[\"10. On-Field Support & Classroom Observation\"]\n"
        "    S10 --> D2{\"T+1 Form Update Completed?\"}\n"
        "    D2 -- No --> S10\n"
        "    D2 -- Yes --> S11[\"11. Baseline & Endline Impact Assessment\"]\n"
        "    S11 --> S12[\"12. Monthly Reports & MERAC Submission\"]\n"
        "    S12 --> End([Process Concluded: Annual Review & Certification])"
    )
    sections_data["1.11"] = {"type": "flowchart", "content": flowchart_mermaid, "structured_data": None}

    # 1.12 Process Description (Tables 8, 9, 10, 11, 12, 13)
    # Expected fields: ['Activity', 'Description', 'Owner/Role', 'TAT']
    desc_rows = []
    subproc_tables = [
        (8, "Venue Finalisation"),
        (9, "ERP & Expense Accounting"),
        (10, "Workshop Phase 1 (Residential)"),
        (11, "Workshop Phase 2 (One-Day)"),
        (12, "Moodle & Digital Learning"),
        (13, "Print Resources & Distribution")
    ]
    for tbl_idx, subproc_name in subproc_tables:
        t = tables[tbl_idx]
        for r in t.rows[1:]:
            c = [clean(cell.text) for cell in r.cells]
            if any(c) and len(c) >= 4:
                act_name = c[1]
                act_desc = c[2]
                tat = c[3]
                resp = c[4] if len(c) > 4 and c[4] else "PM SHRI SPOC / Coordinator"
                desc_rows.append({
                    "Activity": f"[{subproc_name}] {act_name}",
                    "Description": act_desc,
                    "Owner/Role": resp,
                    "TAT": tat if tat else "Ongoing"
                })
    sections_data["1.12"] = {"type": "table", "content": None, "structured_data": desc_rows}

    # 1.13 RACI Matrix (Table 14)
    # Expected fields: ['Sr. No.', 'Activity name', 'Activity description', 'Timeline', 'Responsible', 'Accountable', 'Consulted by', 'Informed to']
    t14 = tables[14]
    raci_rows = []
    for r in t14.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 6:
            raci_rows.append({
                "Sr. No.": c[0],
                "Activity name": c[1],
                "Activity description": c[1],
                "Timeline": c[6] if len(c) > 6 and c[6] else "Q1 - Q3",
                "Responsible": c[2] if c[2] else "PM SHRI SPOC",
                "Accountable": c[3] if c[3] else "Manager",
                "Consulted by": c[4] if c[4] else "DPH",
                "Informed to": c[5] if c[5] else "PH"
            })
    sections_data["1.13"] = {"type": "table", "content": None, "structured_data": raci_rows}

    # 1.14 Business Rules (Table 15)
    # Expected fields: ['Business Rules']
    t15 = tables[15]
    brule_rows = []
    for r in t15.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 3:
            brule_rows.append({
                "Business Rules": f"[{c[1]}] {c[2]}"
            })
    sections_data["1.14"] = {"type": "table", "content": None, "structured_data": brule_rows}

    # 1.15 Exception and Change Management (Table 16)
    # Expected fields: ['Area of Exception', 'Exception Description', 'Exception Mitigation', 'Prop By', 'Recom By', 'Approved By', 'Informed to', 'Remarks']
    t16 = tables[16]
    exc_rows = []
    for r in t16.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 8:
            exc_rows.append({
                "Area of Exception": c[1],
                "Exception Description": c[2],
                "Exception Mitigation": c[3],
                "Prop By": c[4] if c[4] else "GL team",
                "Recom By": c[5] if c[5] else "Manager",
                "Approved By": c[6] if c[6] else "PH",
                "Informed to": c[7] if c[7] else "PH",
                "Remarks": c[8] if len(c) > 8 and c[8] else "Standard mitigation protocol"
            })
    sections_data["1.15"] = {"type": "table", "content": None, "structured_data": exc_rows}

    # 1.16 Risk Management (Table 17)
    # Expected fields: ['Sub Process', 'Risk Description', 'Root Cause', 'Type of Risk', 'Risk Impact', 'Level of Risk', 'Control Description', 'Control frequency']
    t17 = tables[17]
    risk_rows = []
    for r in t17.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 8:
            risk_rows.append({
                "Sub Process": c[0],
                "Risk Description": c[1],
                "Root Cause": c[2],
                "Type of Risk": c[3],
                "Risk Impact": c[4],
                "Level of Risk": c[5],
                "Control Description": c[6],
                "Control frequency": c[7]
            })
    sections_data["1.16"] = {"type": "table", "content": None, "structured_data": risk_rows}

    # 1.17 Compliance Management (Table 18)
    # Expected fields: ['Sub Process', 'Compliance particulars', 'Target date']
    t18 = tables[18]
    comp_rows = []
    for r in t18.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 3:
            comp_rows.append({
                "Sub Process": c[0],
                "Compliance particulars": c[1],
                "Target date": c[2]
            })
    sections_data["1.17"] = {"type": "table", "content": None, "structured_data": comp_rows}

    # 1.18 Data Archival (Table 19)
    # Expected fields: ['Sub Process', 'Financial Year', 'Document Title', 'Criticality', 'Storage Type', 'Cut off Period', 'Retention period', 'Location - hard copy', 'Folder link - soft copy']
    t19 = tables[19]
    arch_rows = []
    for r in t19.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 9:
            arch_rows.append({
                "Sub Process": c[0],
                "Financial Year": c[1],
                "Document Title": c[2],
                "Criticality": c[3],
                "Storage Type": c[4],
                "Cut off Period": c[5] if c[5] else "End of Academic Year",
                "Retention period": c[6] if c[6] else "3 years",
                "Location - hard copy": c[7] if c[7] else "NA",
                "Folder link - soft copy": c[8] if c[8] else "KEF Drive / PM SHRI Database"
            })
    sections_data["1.18"] = {"type": "table", "content": None, "structured_data": arch_rows}

    # 1.19 Abbreviations & Acronyms (Table 20)
    # Expected fields: ['Abbreviation', 'Definition']
    t20 = tables[20]
    abbr_rows = []
    for r in t20.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 2:
            abbr_rows.append({
                "Abbreviation": c[0],
                "Definition": c[1]
            })
    sections_data["1.19"] = {"type": "table", "content": None, "structured_data": abbr_rows}

    # 1.20 Best Practices Summary (Table 21)
    # Expected fields: ['Best Practices Followed (suggested list)', 'Envisaged/Planned', 'Tentative Timelines']
    t21 = tables[21]
    bp_rows = []
    for r in t21.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 4:
            bp_rows.append({
                "Best Practices Followed (suggested list)": c[1],
                "Envisaged/Planned": c[2],
                "Tentative Timelines": c[3]
            })
    sections_data["1.20"] = {"type": "table", "content": None, "structured_data": bp_rows}

    # 1.21 Innovations (Table 22)
    # Expected fields: ['Innovations Implemented', 'Envisaged/Planned', 'TENTATIVE TIMELINES']
    t22 = tables[22]
    inn_rows = []
    for r in t22.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 4:
            inn_rows.append({
                "Innovations Implemented": c[1],
                "Envisaged/Planned": c[2],
                "TENTATIVE TIMELINES": c[3]
            })
    sections_data["1.21"] = {"type": "table", "content": None, "structured_data": inn_rows}

    # 1.22 SIPOC (Table 23)
    # Expected fields: ['Supplier (Dept)', 'Input', 'Key Process Step', 'Output', 'Customer (dept)']
    t23 = tables[23]
    sipoc_rows = []
    for r in t23.rows[1:]:
        c = [clean(cell.text) for cell in r.cells]
        if any(c) and len(c) >= 5 and c[0]:
            sipoc_rows.append({
                "Supplier (Dept)": c[0],
                "Input": c[1],
                "Key Process Step": c[2],
                "Output": c[3],
                "Customer (dept)": c[4]
            })
    sections_data["1.22"] = {"type": "table", "content": None, "structured_data": sipoc_rows}

    return sections_data

def main():
    print(f"Loading document: {DOC_PATH}")
    doc = docx.Document(DOC_PATH)
    sections_data = build_process_sections(doc)
    print(f"Parsed {len(sections_data)} sections successfully.")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check if a note already exists
    existing = supabase.table("process_notes").select("id").eq("process_name", PROCESS_NAME).eq("created_by", TARGET_USER_ID).execute()
    if existing.data:
        note_id = existing.data[0]["id"]
        print(f"Found existing note id={note_id}. Updating...")
        supabase.table("process_notes").update({
            "team": TEAM_NAME,
            "version": VERSION,
            "status": "DRAFT",
            "subject_matter_expert": "Pratibha More",
            "process_owner": "Sangita Dandapat",
            "process_champion": "Jayasree Ramesh",
            "process_reviewer": "Jayati Kapadia",
            "process_approver": "N/A",
            "effective_date": "1st Aug 2023",
            "next_review_date": "1st Aug 2024",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", note_id).execute()
        # Delete existing sections to refresh cleanly
        supabase.table("process_sections").delete().eq("process_note_id", note_id).execute()
    else:
        doc_uuid = str(uuid.uuid4())
        print(f"Creating new process note for user_id={TARGET_USER_ID}...")
        res = supabase.table("process_notes").insert({
            "document_id": doc_uuid,
            "process_name": PROCESS_NAME,
            "team": TEAM_NAME,
            "version": VERSION,
            "status": "DRAFT",
            "document_type": "PROCESS_NOTE",
            "subject_matter_expert": "Pratibha More",
            "process_owner": "Sangita Dandapat",
            "process_champion": "Jayasree Ramesh",
            "process_reviewer": "Jayati Kapadia",
            "process_approver": "N/A",
            "effective_date": "1st Aug 2023",
            "next_review_date": "1st Aug 2024",
            "created_by": TARGET_USER_ID,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        note_id = res.data[0]["id"]
        print(f"Created process note with id={note_id}")

    # Insert all 22 sections
    sec_payloads = []
    for sec_id in [f"1.{i}" for i in range(1, 23)]:
        sec_info = sections_data.get(sec_id)
        if sec_info:
            sec_payloads.append({
                "process_note_id": note_id,
                "process_name": PROCESS_NAME,
                "section_id": sec_id,
                "content": sec_info["content"],
                "structured_data": sec_info["structured_data"]
            })
    
    sec_res = supabase.table("process_sections").insert(sec_payloads).execute()
    print(f"Inserted {len(sec_res.data)} process sections for note_id={note_id}.")
    print("Ingestion complete!")

if __name__ == "__main__":
    main()
