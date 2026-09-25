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
            "status": "DRAFT",
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
                    {"Process / Policy ID": "PT-001", "Document Name": "PedTech Content Management Policy"}
                ]},
                {"id": "1.5", "structured_data": [
                    {"Description": "Video Translation TAT", "Owner": "Translator", "Target": "48 Hours", "Maker": "Translator", "Checker": "Lead", "Data Source": "CMS", "Report Name": "Translation Metrics", "Report Frequency": "Weekly", "Review Frequency": "Monthly"},
                    {"Description": "Rubric Accuracy", "Owner": "Evaluator", "Target": "95%", "Maker": "Evaluator", "Checker": "Quality", "Data Source": "LMS", "Report Name": "Quality Report", "Report Frequency": "Monthly", "Review Frequency": "Quarterly"}
                ]},
                {"id": "1.6", "content": "This process note comprehensively covers the workflows for 'Video Translation' and 'Rubrics Evaluation' ensuring consistency across all pedagogical technologies deployed in the organization."},
                {"id": "1.7", "structured_data": [
                    {"Activity": "Receive English Video", "Entry Criteria": "Final English video uploaded to CMS by production team"},
                    {"Activity": "Receive Course Plan", "Entry Criteria": "Curriculum plan finalized and approved by academic head"}
                ]},
                {"id": "1.8", "structured_data": [
                    {"Activity": "Publish Localized Video", "Exit Criteria": "Translated video is live on LMS and verified"},
                    {"Activity": "Upload Rubric", "Exit Criteria": "Rubric is attached to course modules in LMS"}
                ]},
                {"id": "1.9", "content": "PedTech frequently creates localized video content and complex evaluation rubrics to ensure standardized learning across all centers globally. Quality and speed are paramount to ensure smooth academic operations."},
                {"id": "1.10", "content": "The objective is to standardize the translation of educational videos and the creation of learning rubrics within the PedTech team, reducing turnaround time while improving overall educational outcomes."},
                {"id": "1.11", "content": "The scope of this process covers all internal PedTech translation efforts for global courses, and rubric creations for internal assessments. Excludes external vendor translations."},
                {"id": "1.12", "structured_data": [
                    {"Activity": "Draft Script", "Description": "Translate the original English script to local language.", "Owner/Role": "Translator", "TAT": "24 hours"},
                    {"Activity": "Draft Rubric", "Description": "Identify key scoring areas and draft the evaluation rubric.", "Owner/Role": "Evaluator", "TAT": "48 hours"}
                ]},
                {"id": "1.13", "structured_data": [
                    {"Roles": "Translator", "Responsible ( R )": "Yes", "Accountable ( A )": "Yes", "Consulted ( C )": "No", "Informed ( I )": "No", "TAT": "24 hours"},
                    {"Roles": "Evaluator", "Responsible ( R )": "Yes", "Accountable ( A )": "Yes", "Consulted ( C )": "No", "Informed ( I )": "No", "TAT": "48 hours"}
                ]},
                {"id": "1.14", "structured_data": [
                    {"Business Rules": "All translated scripts must pass a peer grammar check before recording."},
                    {"Business Rules": "Rubrics must cover at least 4 learning outcomes per course."}
                ]},
                {"id": "1.15", "structured_data": [
                    {"Area of Exception": "Voice Artist Unavailable", "Exception Description": "Assigned voice artist is sick or on leave.", "Exception Mitigation": "Use AI voice generator temporarily.", "Prop By": "Translator", "Recom By": "Lead", "Approved By": "Director", "Informed to": "Team", "Remarks": "Only applicable for non-flagship, supplementary courses."}
                ]},
                {"id": "1.16", "structured_data": [
                    {"Sub Process": "Video Translation", "Risk Description": "Inaccurate translation", "Root Cause": "Lack of context or poor language skills", "Type of Risk": "Quality", "Risk Impact": "High", "Level of Risk": "Medium", "Control Description": "Peer review and SME sign-off", "Control frequency": "Per video"},
                    {"Sub Process": "Rubrics Evaluation", "Risk Description": "Subjective scoring", "Root Cause": "Vague rubric descriptors", "Type of Risk": "Quality", "Risk Impact": "Medium", "Level of Risk": "Low", "Control Description": "Standardized metric templates and calibration sessions", "Control frequency": "Quarterly"}
                ]},
                {"id": "1.17", "structured_data": [
                    {"Sub Process": "Video Translation", "Compliance particulars": "Adhere to regional accessibility guidelines (e.g., Closed Captions)", "Target date": "Pre-publish"}
                ]},
                {"id": "1.18", "structured_data": [
                    {"Sub Process": "Video Translation", "Financial Year": "2026-27", "Document Title": "Translated Video File", "Criticality": "High", "Storage Type": "Soft", "Cut off Period": "1 Year", "Retention period": "5 Years", "Location - hard copy": "Not Applicable", "Folder link - soft copy": "/pedtech/videos/translated"}
                ]},
                {"id": "1.19", "structured_data": [
                    {"Abbreviation": "CMS", "Definition": "Content Management System"},
                    {"Abbreviation": "LMS", "Definition": "Learning Management System"},
                    {"Abbreviation": "TAT", "Definition": "Turn Around Time"}
                ]},
                {"id": "1.20", "structured_data": [
                    {"Best Practices Followed (suggested list)": "Use of Translation Memory tools", "Envisaged/Planned": "Implement fully automated initial translation", "Tentative Timelines": "Q4 2026"}
                ]},
                {"id": "1.21", "structured_data": [
                    {"Innovations Implemented": "Dynamic rubrics integration in LMS", "Envisaged/Planned": "AI-assisted rubric generation", "TENTATIVE TIMELINES": "Q1 2027"}
                ]},
                {"id": "1.22", "structured_data": [
                    {"Supplier (Dept)": "Content Production Team", "Input": "Approved English Script & Video", "Key Process Step": "Translate & Voiceover", "Output": "Localized Video", "Customer (dept)": "Regional Student Body"}
                ]}
            ]
        },
        {
            "name": "CCT Annual Training Camp Workflow",
            "team": "CCT Training",
            "sme": "Alice Johnson",
            "owner": "Bob Martin",
            "status": "DRAFT",
            "sections": [
                {"id": "1.1", "structured_data": [
                    {"Name": "Bob Martin", "Role": "Process Owner", "Function": "Training Lead", "Sign": "BM", "Date": "2026-10-01"},
                    {"Name": "Alice Johnson", "Role": "Process Reviewer", "Function": "SME", "Sign": "AJ", "Date": "2026-10-02"},
                    {"Name": "Charlie Director", "Role": "Process Approver", "Function": "Director", "Sign": "CD", "Date": "2026-10-03"}
                ]},
                {"id": "1.2", "structured_data": [
                    {"Version No.": "1.0", "Effective Date": "2026-10-01", "Change Date": "2026-10-01", "Change Request By": "Bob Martin", "Change Made By": "Alice Johnson", "Amendment": "Initial Document Creation"}
                ]},
                {"id": "1.3", "structured_data": [
                    {"Effective Date": "2026-10-01", "Next Review Date": "2027-10-01", "Process Owner": "Bob Martin", "Name": "Bob Martin", "Sign": "BM"}
                ]},
                {"id": "1.4", "structured_data": [
                    {"Process / Policy ID": "CCT-TR-002", "Document Name": "CCT Training Camp Guidelines"}
                ]},
                {"id": "1.5", "structured_data": [
                    {"Description": "Trainer Attendance", "Owner": "Trainer", "Target": "100%", "Maker": "Trainer", "Checker": "Manager", "Data Source": "Attendance Register", "Report Name": "Daily Attendance", "Report Frequency": "Daily", "Review Frequency": "Weekly"},
                    {"Description": "Trainee Satisfaction", "Owner": "Feedback Coordinator", "Target": "90%", "Maker": "Coordinator", "Checker": "Training Lead", "Data Source": "Survey tool", "Report Name": "Feedback Summary", "Report Frequency": "Post-Camp", "Review Frequency": "Annual"}
                ]},
                {"id": "1.6", "content": "This note details the end-to-end process for planning, executing, and evaluating the annual CCT training camp for educators."},
                {"id": "1.7", "structured_data": [
                    {"Activity": "Approve Budget", "Entry Criteria": "Annual training budget cleared and allocated by Finance"},
                    {"Activity": "Participant Check-in", "Entry Criteria": "Participants arrive at venue on Day 1"}
                ]},
                {"id": "1.8", "structured_data": [
                    {"Activity": "Finalize Venue", "Exit Criteria": "Venue contract signed and advance paid"},
                    {"Activity": "Camp Concludes", "Exit Criteria": "All feedback forms collected and departure confirmed"}
                ]},
                {"id": "1.9", "content": "The annual training camp aligns all educators on the latest curriculum updates, teaching methodologies, and organizational goals. It is a critical event for maintaining educational quality."},
                {"id": "1.10", "content": "The objective is to successfully organize and execute the 5-day annual training camp for all new and existing educators within the approved budget and schedule."},
                {"id": "1.11", "content": "The scope includes venue booking, travel logistics, content creation, session delivery, and post-camp feedback analysis. Excludes regular weekly training sessions."},
                {"id": "1.12", "structured_data": [
                    {"Activity": "Book Venue", "Description": "Identify, negotiate, and book the training venue.", "Owner/Role": "Logistics Coordinator", "TAT": "10 days"},
                    {"Activity": "Deliver Sessions", "Description": "Execute the training sessions as per the agenda.", "Owner/Role": "Master Trainer", "TAT": "5 days"},
                    {"Activity": "Collect Feedback", "Description": "Gather trainee satisfaction feedback.", "Owner/Role": "Feedback Coordinator", "TAT": "1 day"}
                ]},
                {"id": "1.13", "structured_data": [
                    {"Roles": "Logistics Coordinator", "Responsible ( R )": "Yes", "Accountable ( A )": "Yes", "Consulted ( C )": "No", "Informed ( I )": "No", "TAT": "10 days"},
                    {"Roles": "Master Trainer", "Responsible ( R )": "Yes", "Accountable ( A )": "Yes", "Consulted ( C )": "Yes", "Informed ( I )": "No", "TAT": "5 days"},
                    {"Roles": "Feedback Coordinator", "Responsible ( R )": "Yes", "Accountable ( A )": "Yes", "Consulted ( C )": "No", "Informed ( I )": "Yes", "TAT": "1 day"}
                ]},
                {"id": "1.14", "structured_data": [
                    {"Business Rules": "All selected venues must be within 10km of a major transport hub and within the budget limit per head."}
                ]},
                {"id": "1.15", "structured_data": [
                    {"Area of Exception": "Venue Cost Exceeds Budget", "Exception Description": "No suitable venue available within the standard per-head budget.", "Exception Mitigation": "Reduce camp duration by half a day to offset costs.", "Prop By": "Logistics Coordinator", "Recom By": "Training Lead", "Approved By": "Finance Director", "Informed to": "Participants", "Remarks": "Requires written justification."}
                ]},
                {"id": "1.16", "structured_data": [
                    {"Sub Process": "Camp Planning", "Risk Description": "Venue cancels last minute", "Root Cause": "Overbooking by hotel", "Type of Risk": "Operational", "Risk Impact": "High", "Level of Risk": "Medium", "Control Description": "Sign strict SLA with penalty clauses and identify backup venue", "Control frequency": "Annual"},
                    {"Sub Process": "Camp Execution", "Risk Description": "Low participant attendance", "Root Cause": "Travel delays or illness", "Type of Risk": "Operational", "Risk Impact": "Medium", "Level of Risk": "Low", "Control Description": "Mandatory RSVP and travel coordination assistance", "Control frequency": "Annual"}
                ]},
                {"id": "1.17", "structured_data": [
                    {"Sub Process": "Camp Execution", "Compliance particulars": "Local fire and safety codes at the venue, plus health guidelines", "Target date": "Pre-camp Day 1"}
                ]},
                {"id": "1.18", "structured_data": [
                    {"Sub Process": "Camp Execution", "Financial Year": "2026-27", "Document Title": "Participant Attendance Record", "Criticality": "Medium", "Storage Type": "Soft", "Cut off Period": "1 Year", "Retention period": "3 Years", "Location - hard copy": "Not Applicable", "Folder link - soft copy": "/cct/camp_attendance_2026"}
                ]},
                {"id": "1.19", "structured_data": [
                    {"Abbreviation": "CCT", "Definition": "Core Content Team"},
                    {"Abbreviation": "SLA", "Definition": "Service Level Agreement"}
                ]},
                {"id": "1.20", "structured_data": [
                    {"Best Practices Followed (suggested list)": "Digital feedback collection at the end of each day", "Envisaged/Planned": "Real-time feedback dashboards", "Tentative Timelines": "Next Camp Cycle"}
                ]},
                {"id": "1.21", "structured_data": [
                    {"Innovations Implemented": "App-based personalized agenda for participants", "Envisaged/Planned": "Gamified learning modules during camp", "TENTATIVE TIMELINES": "Next Year"}
                ]},
                {"id": "1.22", "structured_data": [
                    {"Supplier (Dept)": "HR / Recruitment", "Input": "Final Headcount of New Hires", "Key Process Step": "Book Hotel & Logistics", "Output": "Confirmed room allocation", "Customer (dept)": "Camp Attendees"}
                ]}
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
