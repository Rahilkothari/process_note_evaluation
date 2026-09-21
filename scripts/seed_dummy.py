import os
import sys

# Add root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.database import SessionLocal, get_db, User, ProcessNote, ProcessSection
from datetime import datetime
import uuid

def seed_data():
    db = SessionLocal()
    
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

    notes_data = [
        {
            "name": "Employee Onboarding Process",
            "team": "HR",
            "sme": "Jane Doe",
            "owner": "John Smith",
            "status": "APPROVED",
            "sections": [
                {"id": "1.1", "content": "The purpose of this process is to ensure all new employees are successfully integrated into the company culture and have the necessary tools to begin work."},
                {"id": "1.2", "content": "This process covers all full-time and part-time employees hired globally."},
            ]
        },
        {
            "name": "Payroll Processing",
            "team": "Finance",
            "sme": "Alice Johnson",
            "owner": "Bob Martin",
            "status": "UNDER_REVIEW",
            "sections": [
                {"id": "1.1", "content": "To accurately and timely process bi-weekly payroll for all salaried and hourly employees."},
                {"id": "1.2", "content": "Applies to the US domestic payroll processing activities."},
            ]
        },
        {
            "name": "Vendor Payment Process",
            "team": "Finance",
            "sme": "Charlie Brown",
            "owner": "Bob Martin",
            "status": "NEEDS_REVISION",
            "sections": [
                {"id": "1.1", "content": "This process ensures that all verified vendor invoices are paid within net-30 terms."},
            ]
        },
        {
            "name": "Annual Performance Review",
            "team": "HR",
            "sme": "Jane Doe",
            "owner": "John Smith",
            "status": "DRAFT",
            "sections": [
                {"id": "1.1", "content": "Define the structured steps for conducting the end-of-year performance evaluations."},
            ]
        }
    ]

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
                content=sec["content"]
            )
            db.add(section)

    db.commit()
    print("Successfully seeded 4 process notes!")

if __name__ == "__main__":
    seed_data()
