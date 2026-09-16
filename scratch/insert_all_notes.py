import sys
import os
import uuid
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, ProcessNote, ProcessSection, User

def generate_table_data(section_id, team, quality):
    # Depending on the section, return a list of dicts matching the fields
    if section_id == "1.1":
        return [
            {"Name": "John Doe", "Role": "Process Owner", "Function": "Head", "Sign": "JD", "Date": "2024-01-01"},
            {"Name": "Jane Smith", "Role": "Process Reviewer", "Function": "Manager", "Sign": "JS", "Date": "2024-01-02"},
            {"Name": "Rahil Kothari", "Role": "Process Approver", "Function": "Director", "Sign": "RK", "Date": "2024-01-03"}
        ]
    elif section_id == "1.2":
        return [{"Version No.": "1.0", "Effective Date": "2024-01-01", "Change Date": "2024-01-01", "Change Request By": "JD", "Change Made By": "JS", "Amendment": "Initial Draft"}]
    elif section_id == "1.3":
        return [{"Sr. No.": 1, "Effective Date": "2024-01-01", "Next Review Date": "2025-01-01", "Process Owner": "John Doe", "Name": "John Doe", "Sign": "JD"}]
    elif section_id == "1.4":
        return [{"Process / Policy ID": "POL-001", "Document Name": f"{team} Master Policy"}]
    elif section_id == "1.5":
        desc = "High compliance rate and strict adherence to TAT." if quality == "Excellent" else "General compliance."
        return [{"Sr. No.": 1, "Description": f"{team} Turnaround Time", "Owner": "Ops", "Target": "< 2 Days", "Maker": "Exec", "Checker": "Mgr", "Data Source": "System", "Report Name": "Monthly TAT", "Report Frequency": "Monthly", "Review Frequency": "Quarterly"}]
    elif section_id == "1.7":
        return [{"Activity": "Request Received", "Entry Criteria": "Valid form submitted"}]
    elif section_id == "1.8":
        return [{"Activity": "Process Complete", "Exit Criteria": "Approval recorded in system"}]
    elif section_id == "1.12":
        if team == "Volunteering":
            if quality == "Excellent":
                return [
                    {"Sr. No.": 1, "Activity": "Registration", "Description": "Volunteer signs up and provides complete eligibility info", "Owner/Role": "Volunteer Coord", "TAT": "1 day"},
                    {"Sr. No.": 2, "Activity": "Background Check", "Description": "Conduct strict safeguarding and background verification", "Owner/Role": "Compliance", "TAT": "5 days"},
                    {"Sr. No.": 3, "Activity": "Deployment", "Description": "Allocate volunteer to programme and track attendance meticulously", "Owner/Role": "Programme Mgr", "TAT": "2 days"},
                    {"Sr. No.": 4, "Activity": "Grievance", "Description": "Escalation mechanism for volunteer issues", "Owner/Role": "HR", "TAT": "3 days"},
                    {"Sr. No.": 5, "Activity": "Exit", "Description": "Volunteer exit process and records retention", "Owner/Role": "Volunteer Coord", "TAT": "7 days"}
                ]
            else:
                return [{"Sr. No.": 1, "Activity": "Registration", "Description": "Volunteer signs up", "Owner/Role": "Coord", "TAT": "2 days"}, {"Sr. No.": 2, "Activity": "Verification", "Description": "Background check done", "Owner/Role": "HR", "TAT": "5 days"}]
        else: # Finance
            return [
                {"Sr. No.": 1, "Activity": "Invoice Receipt", "Description": "Receive and log vendor invoice", "Owner/Role": "AP Clerk", "TAT": "1 day"},
                {"Sr. No.": 2, "Activity": "Verification", "Description": "3-way matching of PO, Invoice, and GRN", "Owner/Role": "AP Mgr", "TAT": "2 days"},
                {"Sr. No.": 3, "Activity": "Payment Execution", "Description": "Process bank transfer with dual approvals", "Owner/Role": "Finance Head", "TAT": "3 days"}
            ]
    elif section_id == "1.13":
        return [{"Roles": "Manager", "Responsible (R)": "Yes", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "Yes", "TAT": "2 days"}]
    elif section_id == "1.14":
        return [{"Sr. No.": 1, "Business Rule": f"Strict adherence to {team} governance manual."}]
    elif section_id == "1.15":
        return [{"Sr. No.": 1, "Area of Exception": "System Downtime", "Exception Description": "System offline", "Exception Mitigation": "Manual fallback", "Proposed By": "IT", "Recommended By": "Mgr", "Approved By": "Head", "Informed To": "All", "Remarks": "Rare"}]
    elif section_id == "1.16":
        desc = "System block prevents deployment if verification fails." if quality == "Excellent" else "Manual checks."
        return [{"Sub Process": "Verification", "Risk Description": "Unauthorized approval", "Root Cause": "Human error", "Type of Risk": "Operational", "Risk Impact": "High", "Level of Risk": "Medium", "Control Description": desc, "Control Frequency": "Per request"}]
    elif section_id == "1.17":
        return [{"Sub Process": "Audit", "Compliance Particulars": "Annual ISO audit", "Target Date": "Dec 31"}]
    elif section_id == "1.18":
        return [{"Sub Process": "Records", "Financial Year": "2024", "Document Title": "Logs", "Criticality": "High", "Storage Type": "Digital", "Cut-off Period": "1 yr", "Retention Period": "7 yrs", "Location - hard copy": "N/A", "Folder link - soft copy": "/drive/logs"}]
    elif section_id == "1.19":
        return [{"Abbreviation": "TAT", "Definition": "Turnaround Time"}]
    elif section_id == "1.20":
        return [{"Best Practice Followed": "Digital workflows", "Envisaged/Planned": "AI Automation", "Tentative Timelines": "Q4 2024"}]
    elif section_id == "1.21":
        return [{"Innovations Implemented": "Cloud storage", "Envisaged/Planned": "Blockchain verification", "Tentative Timelines": "2025"}]
    elif section_id == "1.22":
        return [{"Supplier (Dept)": "Internal", "Input": "Data", "Key Process Step": "Processing", "Output": "Report", "Customer (Dept)": "Management"}]
    return []

def generate_text_data(section_id, team, quality):
    if section_id == "1.6":
        if team == "Volunteering":
            return "This process covers the end-to-end volunteer management lifecycle including types of volunteering, onboarding, registration, eligibility criteria, allocation, engagement, attendance tracking, training, grievance handling, and the volunteer exit process across all organizational programmes."
        return "This process covers the end-to-end lifecycle for the Finance department, encompassing invoice processing, vendor payments, and reconciliation."
    elif section_id == "1.9":
        return f"A robust {team} process is essential for organizational efficiency and risk mitigation."
    elif section_id == "1.10":
        if team == "Volunteering":
            return "To ensure a standardized, compliant, and engaging volunteering experience that aligns with our organizational goals, while ensuring all volunteers are properly vetted, trained, deployed, and tracked."
        return "To ensure timely, accurate, and compliant financial operations with strict internal controls and dual-approval mechanisms."
    elif section_id == "1.11":
        return "flowchart.pdf"
    return ""

def create_note(db, user_id, title, team, quality):
    note = ProcessNote(
        document_id=str(uuid.uuid4()),
        process_name=f"[{quality}] {title}",
        team=team,
        version="1.0",
        status="DRAFT",
        subject_matter_expert="Jane Doe",
        process_owner="John Smith",
        process_champion="Alice Johnson",
        process_reviewer="Bob Williams",
        process_approver="Rahil Kothari",
        effective_date="2024-01-01",
        next_review_date="2025-01-01",
        created_by=user_id
    )
    db.add(note)
    db.flush()

    sections = []
    # 22 sections
    text_sections = ["1.6", "1.9", "1.10"]
    file_sections = ["1.11"]
    table_sections = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.7", "1.8", "1.12", "1.13", "1.14", "1.15", "1.16", "1.17", "1.18", "1.19", "1.20", "1.21", "1.22"]

    for sec_id in text_sections:
        sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id=sec_id, content=generate_text_data(sec_id, team, quality)))
        
    for sec_id in file_sections:
        sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id=sec_id, content="flowchart_upload.pdf"))

    for sec_id in table_sections:
        sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id=sec_id, structured_data=generate_table_data(sec_id, team, quality)))
        
    db.add_all(sections)
    return note

def main():
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        user = User(name="Rahil", email="rahilkk07@gmail.com", role="admin")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Excellent Volunteering
    create_note(db, user.id, "Volunteering Deployment", "Volunteering", "Excellent")
    # Good Volunteering
    create_note(db, user.id, "Volunteering Basics", "Volunteering", "Good")
    # Excellent Finance
    create_note(db, user.id, "Vendor Payment Control", "Finance", "Excellent")
    # Good Finance
    create_note(db, user.id, "Expense Management", "Finance", "Good")

    db.commit()
    print("Created 4 notes with ALL 22 sections filled.")

if __name__ == "__main__":
    main()
