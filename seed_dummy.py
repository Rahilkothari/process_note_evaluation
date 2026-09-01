import os
import sys
import json
from datetime import datetime, date
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from models.database import get_db, ProcessNote, ProcessSection, User, ValidationRun, ValidationFinding, ReviewHistory

db = next(get_db())

def clear_database():
    db.query(ValidationFinding).delete()
    db.query(ValidationRun).delete()
    db.query(ReviewHistory).delete()
    db.query(ProcessSection).delete()
    db.query(ProcessNote).delete()
    db.commit()

def create_note(admin_id, name, quality):
    if quality == "Bad":
        note = ProcessNote(
            process_name=name, team="HR", version="1.0", status="DRAFT",
            subject_matter_expert="", process_owner="John",
            process_champion="", process_reviewer="", process_approver="",
            effective_date="", next_review_date="2099-01-01",
            created_by=admin_id
        )
    elif quality == "Average":
        note = ProcessNote(
            process_name=name, team="Human Resources", version="1.0", status="DRAFT",
            subject_matter_expert="Jane Doe", process_owner="John Smith",
            process_champion="", process_reviewer="Bob Reviewer", process_approver="Alice Johnson",
            effective_date=str(date.today()), next_review_date="2027-01-01",
            created_by=admin_id
        )
    else: 
        note = ProcessNote(
            process_name=name, team="Human Resources", version="1.0", status="DRAFT",
            subject_matter_expert="Jane Doe (Sr. HR Manager)", process_owner="John Smith (VP HR)",
            process_champion="Alice Johnson (HR Ops)", process_reviewer="Bob Reviewer (Compliance)", process_approver="Eve Approver (CHRO)",
            effective_date=str(date.today()), next_review_date="2027-01-01",
            created_by=admin_id
        )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    sections = []

    def add_section(sec_id, content=None, data=None):
        sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id=sec_id, content=content, structured_data=data))

    if quality == "Excellent":
        add_section("1.9", content="The onboarding process is critical to ensure new employees are fully integrated, compliant, and productive as quickly as possible. This document outlines the end-to-end flow from offer acceptance to the end of week one.")
        add_section("1.10", content="To establish a standardized, compliant, and efficient onboarding process for all new hires, ensuring they receive necessary IT assets, compliance training, and HR orientation within their first 48 hours, thereby minimizing time-to-productivity.")
        add_section("1.6", content="INCLUDED: All full-time and part-time employees joining the corporate office. EXCLUDED: Contractors, freelancers, and temporary staff.")
        add_section("1.7", data=[{"Activity": "Offer Accepted", "Entry Criteria": "Candidate signs the digital offer letter and background check clears."}])
        add_section("1.8", data=[{"Activity": "Week 1 Check-in", "Exit Criteria": "Employee completes all mandatory training and signs the acknowledgment form."}])
        add_section("1.11", content="flowchart_v1.png")
        add_section("1.12", data=[
            {"Sr. No.": 1, "Activity": "Pre-Onboarding", "Description": "HR Coordinator dispatches welcome packet.", "Owner/Role": "HR Coordinator", "TAT": 24},
            {"Sr. No.": 2, "Activity": "IT Provisioning", "Description": "IT Helpdesk configures laptop and SSO.", "Owner/Role": "IT Helpdesk", "TAT": 48},
            {"Sr. No.": 3, "Activity": "Orientation", "Description": "Conduct mandatory 2-hour orientation.", "Owner/Role": "Compliance Officer", "TAT": 72}
        ])
        add_section("1.13", data=[
            {"Roles": "HR Coordinator", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "Yes", "TAT": 24},
            {"Roles": "VP HR", "Responsible (R)": "No", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "Yes", "TAT": 24},
            {"Roles": "IT Helpdesk", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "Yes", "Informed (I)": "No", "TAT": 48}
        ])
        add_section("1.14", data=[{"Sr. No.": 1, "Business Rule": "All laptops must have MDM installed before handover."}])
        add_section("1.15", data=[{"Sr. No.": 1, "Area of Exception": "Background check delay", "Exception Description": "BG check takes longer than 5 days", "Exception Mitigation": "Conditional start with restricted access", "Proposed By": "HR", "Recommended By": "Legal", "Approved By": "VP HR", "Informed To": "Hiring Manager", "Remarks": ""}])
        add_section("1.16", data=[{"Sub Process": "IT Provisioning", "Risk Description": "Laptop not ready on day 1", "Root Cause": "Supply chain issues", "Type of Risk": "Operational", "Risk Impact": "High", "Level of Risk": "Medium", "Control Description": "Maintain a buffer stock of 5 laptops at all times.", "Control Frequency": "Monthly"}])
        add_section("1.17", data=[{"Sub Process": "Orientation", "Compliance Particulars": "InfoSec Acknowledgment Sign-off", "Target Date": "Day 2"}])
        add_section("1.18", data=[{"Sub Process": "Orientation", "Financial Year": "All", "Document Title": "Signed NDA", "Criticality": "High", "Storage Type": "Soft Copy", "Cut-off Period": "Immediate", "Retention Period": "7 Years", "Location - hard copy": "NA", "Folder link - soft copy": "SharePoint/HR"}])
        add_section("1.5", data=[{"Sr. No.": 1, "Description": "Turnaround time for IT provisioning", "Owner": "IT Manager", "Target": "< 48 hours", "Maker": "IT Exec", "Checker": "IT Manager", "Data Source": "Jira Service Desk", "Report Name": "SLA Report", "Report Frequency": "Weekly", "Review Frequency": "Monthly"}])
        add_section("1.19", data=[{"Abbreviation": "MDM", "Definition": "Mobile Device Management"}])
        add_section("1.20", data=[{"Best Practice Followed": "Automated welcome emails", "Envisaged/Planned": "Existing", "Tentative Timelines": "NA"}])
        add_section("1.21", data=[{"Innovations Implemented": "Self-service IT portal for day 1", "Envisaged/Planned": "Planned", "Tentative Timelines": "Q3 2026"}])
        add_section("1.22", data=[{"Supplier (Dept)": "Recruitment", "Input": "Signed Offer", "Key Process Step": "Pre-Onboarding", "Output": "Welcome Packet", "Customer (Dept)": "New Hire"}])
        add_section("1.4", data=[{"Process / Policy ID": "POL-HR-001", "Document Name": "Employee Handbook"}])
        add_section("1.1", data=[{"Name": "John Smith", "Role": "Process Owner", "Function": "HR", "Sign": "JS", "Date": "2026-08-27"}, {"Name": "Bob", "Role": "Process Reviewer", "Function": "Compliance", "Sign": "BR", "Date": "2026-08-27"}, {"Name": "Eve", "Role": "Process Approver", "Function": "Leadership", "Sign": "EA", "Date": "2026-08-27"}])
        add_section("1.2", data=[{"Version No.": "1.0", "Effective Date": "2026-08-27", "Change Date": "2026-08-27", "Change Request By": "NA", "Change Made By": "Jane Doe", "Amendment": "Initial Draft"}])
        add_section("1.3", data=[{"Sr. No.": 1, "Effective Date": "2026-08-27", "Next Review Date": "2027-08-27", "Process Owner": "John Smith", "Name": "John Smith", "Sign": "JS"}])

    elif quality == "Average":
        add_section("1.9", content="Onboarding is an operational excellence process that is very important for the company. We do this to onboard people.")
        add_section("1.10", content="To successfully onboard new employees into the company and provide them with laptops.")
        add_section("1.6", content="This applies to all new employees.")
        add_section("1.7", data=[{"Activity": "They join", "Entry Criteria": "They sign"}])
        add_section("1.8", data=[{"Activity": "They work", "Exit Criteria": "Done"}])
        add_section("1.12", data=[
            {"Sr. No.": 1, "Activity": "Welcome Email", "Description": "Send the standard welcome email to the new joiner's personal address.", "Owner/Role": "HR Executive", "TAT": 24},
            {"Sr. No.": 2, "Activity": "IT Provisioning", "Description": "Provide laptop and configure basic accounts.", "Owner/Role": "IT Support", "TAT": 48}
        ])
        add_section("1.13", data=[
            {"Roles": "HR Exec", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "No", "TAT": 24},
            {"Roles": "HR Manager", "Responsible (R)": "No", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "No", "TAT": 24}
        ])
        add_section("1.14", data=[{"Sr. No.": 1, "Business Rule": "Give laptops to people"}])
        add_section("1.16", data=[{"Sub Process": "IT", "Risk Description": "Laptop breaks", "Root Cause": "Bad laptop", "Type of Risk": "Operational", "Risk Impact": "Medium", "Level of Risk": "Medium", "Control Description": "Fix it", "Control Frequency": "Daily"}])
        add_section("1.1", data=[{"Name": "John Smith", "Role": "Owner", "Function": "HR", "Sign": "JS", "Date": "2026-08-27"}])
        add_section("1.5", data=[{"Sr. No.": 1, "Description": "Fast onboarding", "Owner": "HR", "Target": "Fast", "Maker": "HR", "Checker": "HR", "Data Source": "Excel", "Report Name": "Report", "Report Frequency": "Weekly", "Review Frequency": "Weekly"}])

    elif quality == "Bad":
        add_section("1.9", content="Onboarding")
        add_section("1.10", content="To onboard.")
        add_section("1.6", content="everyone")
        add_section("1.7", data=[{"Activity": "start", "Entry Criteria": ""}])
        add_section("1.8", data=[{"Activity": "end", "Exit Criteria": ""}])
        add_section("1.12", data=[
            {"Sr. No.": 1, "Activity": "Email", "Description": "Send email", "Owner/Role": "HR", "TAT": None},
            {"Sr. No.": 2, "Activity": "Laptop", "Description": "Give laptop", "Owner/Role": "", "TAT": None}
        ])
        add_section("1.13", data=[
            {"Roles": "HR", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "No", "TAT": None}
        ])
        add_section("1.1", data=[{"Name": "", "Role": "", "Function": "", "Sign": "", "Date": ""}])

    db.add_all(sections)
    db.commit()

def seed_dummy_notes():
    admin_user = db.query(User).filter(User.email == "rahillkk07@gmail.com").first()
    if not admin_user:
        admin_user = User(name="Rahil Admin", email="rahillkk07@gmail.com", role="admin")
        db.add(admin_user)
        db.commit()

    create_note(admin_user.id, "New Employee Onboarding - BAD", "Bad")
    create_note(admin_user.id, "New Employee Onboarding - AVERAGE", "Average")
    create_note(admin_user.id, "New Employee Onboarding - EXCELLENT", "Excellent")
    
if __name__ == "__main__":
    clear_database()
    seed_dummy_notes()
