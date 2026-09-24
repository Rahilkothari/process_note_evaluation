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

    # 2. Seed 2 new dummy process notes
    notes_data = [
        {
            "name": "PedTech Content Workflows",
            "team": "PedTech",
            "sme": "Jane Doe",
            "owner": "John Smith",
            "status": "APPROVED",
            "sections": [
                {"id": "1.6", "content": "This process note covers two main sub-processes: 'Video Translation' and 'Rubrics Evaluation'."},
                {"id": "1.10", "content": "To standardize the translation of educational videos and the evaluation of learning rubrics."},
                {"id": "1.12", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Activity": "Draft Script", "Description": "Draft the translated script.", "Owner/Role": "Translator", "TAT": "2 days"},
                    {"Sub-Process Name": "Rubrics Evaluation", "Activity": "Score Rubric", "Description": "Score the student rubric.", "Owner/Role": "Evaluator", "TAT": "1 day"}
                ]},
                {"id": "1.16", "structured_data": [
                    {"Sub-Process Name": "Video Translation", "Risk Description": "Inaccurate translation", "Root Cause": "Lack of context", "Type of Risk": "Quality", "Risk Impact": "High", "Level of Risk": "Medium", "Control Description": "Peer review", "Control Frequency": "Per video"},
                    {"Sub-Process Name": "Rubrics Evaluation", "Risk Description": "N/A", "Root Cause": "N/A", "Type of Risk": "N/A", "Risk Impact": "N/A", "Level of Risk": "N/A", "Control Description": "N/A", "Control Frequency": "N/A"}
                ]}
            ]
        },
        {
            "name": "CCT Annual Training Camp",
            "team": "CCT Training",
            "sme": "Alice Johnson",
            "owner": "Bob Martin",
            "status": "UNDER_REVIEW",
            "sections": [
                {"id": "1.6", "content": "This note covers the single main process of organizing the annual CCT training camp."},
                {"id": "1.10", "content": "To successfully organize and execute the 5-day annual training camp for all new hires."},
                {"id": "1.12", "structured_data": [
                    {"Sub-Process Name": "", "Activity": "Book Venue", "Description": "Book the hotel for the camp.", "Owner/Role": "Logistics", "TAT": "10 days"},
                    {"Sub-Process Name": "", "Activity": "Finalize Agenda", "Description": "Finalize the 5-day training agenda.", "Owner/Role": "Training Manager", "TAT": "5 days"}
                ]}
            ]
        }
    ]

    print("Seeding new 22-section standard process notes...")
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
    print("Successfully cleaned DB and seeded 2 new standard process notes!")

if __name__ == "__main__":
    clean_and_seed()
