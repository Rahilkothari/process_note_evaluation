import os
import sys
from datetime import datetime
import uuid

# Add root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.database import SessionLocal, User, ProcessNote, ProcessSection, Notification

def clean_and_seed():
    db = SessionLocal()
    
    # 1. Clean DB except "video translation"
    print("Cleaning database...")
    all_notes = db.query(ProcessNote).all()
    deleted_count = 0
    for note in all_notes:
        if "video translation" not in note.process_name.lower():
            # Delete associated notifications
            db.query(Notification).filter(Notification.process_note_id == note.id).delete()
            # Delete associated sections
            db.query(ProcessSection).filter(ProcessSection.process_note_id == note.id).delete()
            # Delete the note
            db.delete(note)
            deleted_count += 1
            
    db.commit()
    print(f"Deleted {deleted_count} old dummy notes.")
    
    # Ensure users exist
    creator_email = "rahilkothari99@gmail.com"
    reviewer_email = "rahilkk07@gmail.com"
    
    creator = db.query(User).filter(User.email == creator_email).first()
    if not creator:
        creator = User(name="Rahil (Creator)", email=creator_email, role="creator")
        db.add(creator)
        db.commit()
        db.refresh(creator)
        
    reviewer = db.query(User).filter(User.email == reviewer_email).first()
    if not reviewer:
        reviewer = User(name="Rahil (Reviewer)", email=reviewer_email, role="reviewer")
        db.add(reviewer)
        db.commit()

    # 2. Seed 2 new dummy process notes perfectly filled for all 22 sections
    notes_data = [
        {
            "name": "PedTech Content Workflows",
            "team": "PedTech",
            "sme": "Jane Doe",
            "owner": "John Smith",
            "status": "DRAFT",  # Set to DRAFT so user can test UI
            "sections": [
                {"id": "1.1", "structured_data": [
                    {"Name": "John Smith", "Role": "Process Owner", "Function": "PedTech Lead", "Sign": "JS", "Date": "2026-10-01"},
                    {"Name": "Jane Reviewer", "Role": "Process Reviewer", "Function": "Quality Head", "Sign": "JR", "Date": "2026-10-02"},
                    {"Name": "Boss Man", "Role": "Process Approver", "Function": "Director", "Sign": "BM", "Date": "2026-10-03"}
                ]},
                {"id": "1.2", "structured_data": [
                    {"Version No.": "1.0", "Effective Date": "2026-10-01", "Change Date": "2026-10-01", "Change Request By": "Jane Doe", "Change Made By": "John Smith", "Amendment": "Initial Draft"}
                ]},
                {"id": "1.3", "structured_data": [
                    {"Effective Date": "2026-10-01", "Next Review Date": "2027-10-01", "Process Owner": "John Smith", "Name": "John Smith", "Sign": "JS"}
                ]},
                {"id": "1.4", "structured_data": [
                    {"Process / Policy ID": "N/A", "Document Name": "N/A"}
                ]},
                {"id": "1.5", "structured_data": [
                    {"Description": "Video Translation TAT", "Owner": "Translator", "Target": "48 Hours", "Maker": "Translator", "Checker": "Lead", "Data Source": "CMS", "Report Name": "Translation Metrics", "Report Frequency": "Weekly", "Review Frequency": "Monthly"},
                    {"Description": "Rubric Accuracy", "Owner": "Evaluator", "Target": "95%", "Maker": "Evaluator", "Checker": "Quality", "Data Source": "LMS", "Report Name": "Quality Report", "Report Frequency": "Monthly", "Review Frequency": "Quarterly"}
                ]},
                {"id": "1.6", "content": "This process note covers two main sub-processes: 'Video Translation' and 'Rubrics Evaluation'."},
                {"id": "1.7", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Activity": "Receive English Video", "Entry Criteria": "Final video uploaded to CMS"},
                    {"Sub-Process Name": "Rubrics Evaluation", "Activity": "Receive Course Plan", "Entry Criteria": "Curriculum finalized"}
                ]},
                {"id": "1.8", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Activity": "Publish Localized Video", "Exit Criteria": "Video live on LMS"},
                    {"Sub-Process Name": "Rubrics Evaluation", "Activity": "Upload Rubric", "Exit Criteria": "Rubric attached to course modules"}
                ]},
                {"id": "1.9", "content": "PedTech frequently creates localized video content and complex evaluation rubrics to ensure standardized learning across all centers."},
                {"id": "1.10", "content": "To standardize the translation of educational videos and the creation of learning rubrics within the PedTech team."},
                {"id": "1.11", "content": ""},
                {"id": "1.12", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Activity": "Draft Script", "Description": "", "Owner/Role": "Translator", "TAT": ""},
                    {"Sub-Process Name": "Rubrics Evaluation", "Activity": "", "Description": "Identify key scoring areas.", "Owner/Role": "", "TAT": "1 day"}
                ]},
                {"id": "1.13", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Roles": "Translator", "Responsible (R)": "Yes", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "No", "TAT": "2 days"},
                    {"Sub-Process Name": "Rubrics Evaluation", "Roles": "Evaluator", "Responsible (R)": "Yes", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "No", "TAT": "2 days"}
                ]},
                {"id": "1.14", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Business Rule": "All translated scripts must pass a peer grammar check before recording."},
                    {"Sub-Process Name": "Rubrics Evaluation", "Business Rule": "N/A"}
                ]},
                {"id": "1.15", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Area of Exception": "Voice Artist Unavailable", "Exception Description": "Artist is sick.", "Exception Mitigation": "Use AI voice generator temporarily.", "Proposed By": "Translator", "Recommended By": "Lead", "Approved By": "Director", "Informed To": "Team", "Remarks": "Only for non-flagship courses."}
                ]},
                {"id": "1.16", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Risk Description": "Inaccurate translation", "Root Cause": "Lack of context", "Type of Risk": "Quality", "Risk Impact": "High", "Level of Risk": "Medium", "Control Description": "", "Control Frequency": ""},
                    {"Sub-Process Name": "Rubrics Evaluation", "Risk Description": "Subjective scoring", "Root Cause": "", "Type of Risk": "", "Risk Impact": "Medium", "Level of Risk": "Low", "Control Description": "Standardized metric templates", "Control Frequency": ""}
                ]},
                {"id": "1.17", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Compliance Particulars": "Copyright law for background music", "Target Date": "Pre-publish"}
                ]},
                {"id": "1.18", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Financial Year": "2026-27", "Document Title": "Translated Video", "Criticality": "High", "Storage Type": "Soft", "Cut-off Period": "1 Year", "Retention Period": "5 Years", "Location - hard copy": "N/A", "Folder link - soft copy": "/pedtech/videos"}
                ]},
                {"id": "1.19", "structured_data": [
                    {"Abbreviation": "CMS", "Definition": "Content Management System"},
                    {"Abbreviation": "LMS", "Definition": "Learning Management System"}
                ]},
                {"id": "1.20", "structured_data": []},
                {"id": "1.21", "structured_data": []},
                {"id": "1.22", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Supplier (Dept)": "Content Team", "Input": "English Script", "Key Process Step": "Translate", "Output": "Local Script", "Customer (Dept)": "Students"}
                ]}
            ]
        },
        {
            "name": "CCT Annual Training Camp",
            "team": "CCT Training",
            "sme": "Alice Johnson",
            "owner": "Bob Martin",
            "status": "DRAFT",
            "sections": [
                {"id": "1.1", "structured_data": [{"Name": "Bob", "Role": "Process Owner", "Function": "Training", "Sign": "BM", "Date": "2026-10-01"}]},
                {"id": "1.2", "structured_data": [{"Version No.": "1.0", "Effective Date": "2026-10-01", "Change Date": "2026-10-01", "Change Request By": "Bob", "Change Made By": "Alice", "Amendment": "Initial"}]},
                {"id": "1.3", "structured_data": [{"Effective Date": "2026-10-01", "Next Review Date": "2027-10-01", "Process Owner": "Bob", "Name": "Bob", "Sign": "BM"}]},
                {"id": "1.4", "structured_data": [{"Process / Policy ID": "N/A", "Document Name": "N/A"}]},
                {"id": "1.5", "structured_data": [{"Description": "Attendance", "Owner": "Trainer", "Target": "100%", "Maker": "Trainer", "Checker": "Manager", "Data Source": "Register", "Report Name": "Daily Attendance", "Report Frequency": "Daily", "Review Frequency": "Weekly"}]},
                {"id": "1.6", "content": "This note covers the single main process of organizing the annual CCT training camp."},
                {"id": "1.7", "structured_data": [{"Sub-Process Name": "N/A", "Activity": "Approve Budget", "Entry Criteria": "Annual budget cleared"}]},
                {"id": "1.8", "structured_data": [{"Sub-Process Name": "N/A", "Activity": "Camp Concludes", "Exit Criteria": "Feedback forms collected"}]},
                {"id": "1.9", "content": "The annual training camp aligns all educators on the latest curriculum updates."},
                {"id": "1.10", "content": "To successfully organize and execute the 5-day annual training camp for all new hires."},
                {"id": "1.11", "content": "N/A"},
                {"id": "1.12", "structured_data": [{"Sub-Process Name": "N/A", "Activity": "Book Venue", "Description": "Book the hotel.", "Owner/Role": "Logistics", "TAT": "10 days"}]},
                {"id": "1.13", "structured_data": [{"Sub-Process Name": "N/A", "Roles": "Logistics", "Responsible (R)": "Yes", "Accountable (A)": "Yes", "Consulted (C)": "No", "Informed (I)": "No", "TAT": "10 days"}]},
                {"id": "1.14", "structured_data": [{"Sub-Process Name": "N/A", "Business Rule": "All venues must be within 10km of head office."}]},
                {"id": "1.15", "structured_data": [{"Sub-Process Name": "N/A", "Area of Exception": "N/A", "Exception Description": "N/A", "Exception Mitigation": "N/A", "Proposed By": "N/A", "Recommended By": "N/A", "Approved By": "N/A", "Informed To": "N/A", "Remarks": "N/A"}]},
                {"id": "1.16", "structured_data": [{"Sub-Process Name": "N/A", "Risk Description": "Venue cancels", "Root Cause": "Overbooking", "Type of Risk": "Logistics", "Risk Impact": "High", "Level of Risk": "Low", "Control Description": "Sign strict SLA", "Control Frequency": "Annual"}]},
                {"id": "1.17", "structured_data": [{"Sub-Process Name": "N/A", "Compliance Particulars": "Fire safety code", "Target Date": "Pre-camp"}]},
                {"id": "1.18", "structured_data": [{"Sub-Process Name": "N/A", "Financial Year": "2026-27", "Document Title": "Attendance", "Criticality": "Medium", "Storage Type": "Soft", "Cut-off Period": "1 Yr", "Retention Period": "3 Yrs", "Location - hard copy": "N/A", "Folder link - soft copy": "/camp"}]},
                {"id": "1.19", "structured_data": [{"Abbreviation": "CCT", "Definition": "Core Content Team"}]},
                {"id": "1.20", "structured_data": [{"Sub-Process Name": "N/A", "Best Practice Followed": "Digital feedback", "Envisaged/Planned": "N/A", "Tentative Timelines": "N/A"}]},
                {"id": "1.21", "structured_data": [{"Sub-Process Name": "N/A", "Innovations Implemented": "App-based agenda", "Envisaged/Planned": "N/A", "Tentative Timelines": "N/A"}]},
                {"id": "1.22", "structured_data": [{"Sub-Process Name": "N/A", "Supplier (Dept)": "HR", "Input": "Headcount", "Key Process Step": "Book Hotel", "Output": "Confirmed rooms", "Customer (Dept)": "Attendees"}]}
            ]
        }
    ]

    print("Seeding completely filled 22-section standard process notes...")
    for data in notes_data:
        doc_id = str(uuid.uuid4())
        note = ProcessNote(
            document_id=doc_id,
            process_name=data["name"],
            team=data["team"],
            version="1.0",
            status=data["status"],
            subject_matter_expert=data["sme"],
            process_owner=data["owner"],
            process_champion="TBD",
            process_reviewer="Jane Reviewer",
            process_approver="Boss Man",
            effective_date="2026-01-01",
            next_review_date="2027-01-01",
            created_by=creator.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(note)
        db.flush()
        
        for sec in data["sections"]:
            section = ProcessSection(
                process_note_id=note.id,
                process_name=note.process_name,
                section_id=sec["id"],
                content=sec.get("content"),
                structured_data=sec.get("structured_data")
            )
            db.add(section)

    db.commit()
    print("Successfully cleaned DB and seeded 2 fully-populated standard process notes!")

if __name__ == "__main__":
    clean_and_seed()
