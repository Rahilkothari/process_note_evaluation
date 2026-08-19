import os
import sys
import json
from datetime import datetime, date
from dotenv import load_dotenv

# Ensure we can import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from models.database import get_db, ProcessNote, ProcessSection, User, ValidationRun, ValidationFinding, ReviewHistory

db = next(get_db())

def clear_database():
    print("Clearing old process notes...")
    db.query(ValidationFinding).delete()
    db.query(ValidationRun).delete()
    db.query(ReviewHistory).delete()
    db.query(ProcessSection).delete()
    db.query(ProcessNote).delete()
    db.commit()

def create_note(admin_id, name, quality):
    print(f"Creating '{name}' ({quality} quality)...")
    
    # Base attributes
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
    else: # Excellent
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

    # 1.10 Objective
    if quality == "Bad":
        obj = "To onboard."
    elif quality == "Average":
        obj = "To successfully onboard new employees into the company and provide them with laptops."
    else:
        obj = "To establish a standardized, compliant, and efficient onboarding process for all new hires, ensuring they receive necessary IT assets, compliance training, and HR orientation within their first 48 hours, thereby minimizing time-to-productivity."

    sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id="1.10", content=obj))

    # 1.12 Process Description
    if quality == "Bad":
        desc = [
            {"Sr. No.": 1, "Activity": "Email", "Description": "Send email", "Owner/Role": "HR", "TAT": None},
            {"Sr. No.": 2, "Activity": "Laptop", "Description": "Give laptop", "Owner/Role": "", "TAT": None}
        ]
    elif quality == "Average":
        desc = [
            {"Sr. No.": 1, "Activity": "Welcome Email", "Description": "Send the standard welcome email to the new joiner's personal address.", "Owner/Role": "HR Executive", "TAT": 24},
            {"Sr. No.": 2, "Activity": "IT Provisioning", "Description": "Provide laptop and configure basic accounts.", "Owner/Role": "IT Support", "TAT": 48}
        ]
    else:
        desc = [
            {"Sr. No.": 1, "Activity": "Pre-Onboarding Communication", "Description": "HR Coordinator dispatches the standardized welcome packet, including day-1 itinerary and required compliance forms.", "Owner/Role": "HR Coordinator", "TAT": 24},
            {"Sr. No.": 2, "Activity": "IT Hardware Provisioning", "Description": "IT Helpdesk configures the assigned laptop with MDM profiles and provisions SSO access based on role RBAC matrix.", "Owner/Role": "IT Helpdesk", "TAT": 48},
            {"Sr. No.": 3, "Activity": "Compliance Orientation", "Description": "Conduct mandatory 2-hour orientation covering InfoSec and Code of Conduct policies.", "Owner/Role": "Compliance Officer", "TAT": 72}
        ]
    
    sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id="1.12", structured_data=desc))

    # 1.13 RACI Matrix
    if quality == "Bad":
        raci = [
            {"Roles": "HR", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "No", "TAT": None}
        ]
    elif quality == "Average":
        raci = [
            {"Roles": "HR Exec", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "No", "TAT": 24},
            {"Roles": "HR Manager", "Responsible (R)": "No", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "No", "TAT": 24}
        ]
    else:
        raci = [
            {"Roles": "HR Coordinator", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "No", "Informed (I)": "Yes", "TAT": 24},
            {"Roles": "VP HR", "Responsible (R)": "No", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "Yes", "TAT": 24},
            {"Roles": "IT Helpdesk", "Responsible (R)": "Yes", "Accountable (A)": "No", "Consulted (C)": "Yes", "Informed (I)": "No", "TAT": 48}
        ]
        
    sections.append(ProcessSection(process_note_id=note.id, process_name=note.process_name, section_id="1.13", structured_data=raci))

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
    
    print("Successfully seeded all 3 notes!")

if __name__ == "__main__":
    clear_database()
    seed_dummy_notes()
