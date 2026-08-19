import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from models.database import get_db, ProcessNote, ProcessSection
db = next(get_db())

def fill_excellent_note():
    note = db.query(ProcessNote).filter(ProcessNote.process_name == "New Employee Onboarding - EXCELLENT").first()
    if not note:
        print("Excellent note not found!")
        return

    # Delete existing sections to start fresh
    db.query(ProcessSection).filter(ProcessSection.process_note_id == note.id).delete()
    db.commit()

    sections = []
    
    def add_text(sec_id, text):
        sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id=sec_id, content=text))
        
    def add_table(sec_id, data):
        sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id=sec_id, structured_data=data))

    # 1.1 Approval Matrix
    add_table("1.1", [
        {"Name": "John Smith", "Role": "Process Owner", "Function": "HR", "Sign": "JS", "Date": str(date.today())},
        {"Name": "Bob Reviewer", "Role": "Process Reviewer", "Function": "Compliance", "Sign": "BR", "Date": str(date.today())},
        {"Name": "Eve Approver", "Role": "Process Approver", "Function": "CHRO", "Sign": "EA", "Date": str(date.today())}
    ])
    
    # 1.2 Document Change History
    add_table("1.2", [
        {"Version No.": "1.0", "Effective Date": str(date.today()), "Change Date": str(date.today()), "Change Request By": "Jane Doe", "Change Made By": "Jane Doe", "Amendment": "Initial Draft Creation"}
    ])

    # 1.3 Document Review Cycle
    add_table("1.3", [
        {"Sr. No.": 1, "Effective Date": str(date.today()), "Next Review Date": "2027-01-01", "Process Owner": "John Smith", "Name": "John Smith", "Sign": "JS"}
    ])

    # 1.4 Related Documents
    add_table("1.4", [
        {"Process / Policy ID": "POL-HR-001", "Document Name": "Corporate Employee Handbook"},
        {"Process / Policy ID": "POL-IT-042", "Document Name": "IT Asset Provisioning Policy"}
    ])

    # 1.5 Process Performance Parameters / KPIs
    add_table("1.5", [
        {"Sr. No.": 1, "Description": "Complete all IT provisioning before Day 1", "Owner": "IT Helpdesk", "Target": "100%", "Maker": "IT Tech", "Checker": "IT Manager", "Data Source": "Jira Service Desk", "Report Name": "SLA Report", "Report Frequency": "Weekly", "Review Frequency": "Monthly"},
        {"Sr. No.": 2, "Description": "Completion of Compliance Training within 72 hours", "Owner": "Compliance Officer", "Target": "95%", "Maker": "LMS Admin", "Checker": "Compliance Officer", "Data Source": "LMS", "Report Name": "Training Completion", "Report Frequency": "Weekly", "Review Frequency": "Monthly"}
    ])

    # 1.6 Process Coverage / Scope
    add_text("1.6", "This process applies to all full-time and part-time internal employees joining the company globally. It excludes contractors, freelancers, and temporary staff, who fall under the Vendor Onboarding Process (POL-HR-005).")

    # 1.7 Start Point
    add_table("1.7", [
        {"Activity": "Offer Acceptance", "Entry Criteria": "Candidate signs the offer letter and clears the background verification checks."}
    ])

    # 1.8 End Point
    add_table("1.8", [
        {"Activity": "Onboarding Completion", "Entry Criteria": "Employee completes mandatory compliance training and is handed over to the hiring manager for role-specific training."}
    ])

    # 1.9 Introduction
    add_text("1.9", "A seamless onboarding experience is critical for early employee engagement and rapid time-to-productivity. This process governs the cross-departmental coordination required to successfully integrate a new hire into the organization.")

    # 1.10 Objective
    add_text("1.10", "To establish a standardized, compliant, and efficient onboarding process for all new hires, ensuring they receive necessary IT assets, compliance training, and HR orientation within their first 48 hours, thereby minimizing time-to-productivity.")

    # 1.12 Process Description
    add_table("1.12", [
        {"Sr. No.": 1, "Activity": "Pre-Onboarding Communication", "Description": "HR Coordinator dispatches the standardized welcome packet, including day-1 itinerary and required compliance forms.", "Owner/Role": "HR Coordinator", "TAT": 24},
        {"Sr. No.": 2, "Activity": "IT Hardware Provisioning", "Description": "IT Helpdesk configures the assigned laptop with MDM profiles and provisions SSO access based on role RBAC matrix.", "Owner/Role": "IT Helpdesk", "TAT": 48},
        {"Sr. No.": 3, "Activity": "Compliance Orientation", "Description": "Conduct mandatory 2-hour orientation covering InfoSec and Code of Conduct policies.", "Owner/Role": "Compliance Officer", "TAT": 72}
    ])

    # 1.13 RACI Matrix
    add_table("1.13", [
        {"Roles": "HR Coordinator", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "Yes", "TAT": 24},
        {"Roles": "VP HR", "Responsible (R)": "No", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "Yes", "TAT": 24},
        {"Roles": "IT Helpdesk", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "Yes", "Informed (I)": "No", "TAT": 48},
        {"Roles": "Compliance Officer", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "No", "TAT": 72}
    ])

    # 1.14 Business Rules
    add_table("1.14", [
        {"Sr. No.": 1, "Business Rule": "No IT hardware can be shipped without a cleared background check status from the vendor."},
        {"Sr. No.": 2, "Business Rule": "Role-specific application access must be approved by the Department Head via the IAM portal."}
    ])

    # 1.15 Exception and Change Management
    add_table("1.15", [
        {"Sr. No.": 1, "Area of Exception": "IT Provisioning", "Exception Description": "Laptop unavailable due to supply chain issues.", "Exception Mitigation": "Provide cloud virtual desktop (VDI) access temporarily.", "Proposed By": "IT Head", "Recommended By": "VP HR", "Approved By": "CIO", "Informed To": "Hiring Manager", "Remarks": "Standard fallback."}
    ])

    # 1.16 Risk Management
    add_table("1.16", [
        {"Sub Process": "IT Provisioning", "Risk Description": "Incorrect access rights granted to the new employee.", "Root Cause": "Manual error in IAM group assignment.", "Type of Risk": "Operational", "Risk Impact": "High", "Level of Risk": "High", "Control Description": "Automated RBAC provisioning tied directly to the Workday Job Code.", "Control Frequency": "Daily"}
    ])

    # 1.17 Compliance Management
    add_table("1.17", [
        {"Sub Process": "Compliance Training", "Compliance Particulars": "Mandatory Anti-Bribery & Corruption (ABC) training signature.", "Target Date": "Day 3"}
    ])

    # 1.18 Data Archival
    add_table("1.18", [
        {"Sub Process": "Document Collection", "Financial Year": "All", "Document Title": "Signed Offer Letter & NDA", "Criticality": "High", "Storage Type": "Digital", "Cut-off Period": "Immediate", "Retention Period": "7 Years post-termination", "Location - hard copy": "N/A", "Folder link - soft copy": "Workday Document Vault"}
    ])

    # 1.19 Abbreviations & Acronyms
    add_table("1.19", [
        {"Abbreviation": "RBAC", "Definition": "Role-Based Access Control"},
        {"Abbreviation": "IAM", "Definition": "Identity and Access Management"},
        {"Abbreviation": "MDM", "Definition": "Mobile Device Management"}
    ])

    # 1.20 Best Practices Summary
    add_table("1.20", [
        {"Best Practice Followed": "Automated welcome email via HRIS", "Envisaged/Planned": "Integrate welcome video from CEO", "Tentative Timelines": "Q3 2026"}
    ])

    # 1.21 Innovations
    add_table("1.21", [
        {"Innovations Implemented": "Zero-touch IT provisioning via Intune", "Envisaged/Planned": "AI chatbot for Day-1 queries", "Tentative Timelines": "Q4 2026"}
    ])

    # 1.22 SIPOC
    add_table("1.22", [
        {"Supplier (Dept)": "Recruitment", "Input": "Signed Offer Letter", "Key Process Step": "Trigger Onboarding workflow in HRIS", "Output": "Employee ID generated", "Customer (Dept)": "HR Ops"}
    ])

    db.add_all(sections)
    db.commit()
    print("Successfully populated all 22 sections for the EXCELLENT note!")

if __name__ == "__main__":
    fill_excellent_note()
