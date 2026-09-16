from models.database import get_db, ProcessNote, ProcessSection
from services.rag_service import rag_service
from sqlalchemy.orm import Session

def seed_rag():
    print("Connecting to database...")
    db: Session = next(get_db())
    
    print("Looking for APPROVED notes...")
    approved_notes = db.query(ProcessNote).filter(ProcessNote.status == "APPROVED").all()
    
    if not approved_notes:
        print("No APPROVED notes found in the database. Generating mock data for ChromaDB directly...")
        
        # Inject some mock data directly into RAG for testing
        mock_data = [
            {
                "note_id": 9991,
                "team": "Finance",
                "section_id": "1.1",
                "content": "The objective of the Payroll Process is to ensure all employees are compensated accurately and timely. This involves calculating wages, deducting taxes, and remitting payments to respective accounts on the last working day of the month."
            },
            {
                "note_id": 9992,
                "team": "HR",
                "section_id": "1.1",
                "content": "The Employee Onboarding objective is to seamlessly integrate new hires into the company culture, ensure all legal documentation is signed, and provide necessary equipment by Day 1."
            },
            {
                "note_id": 9991,
                "team": "Finance",
                "section_id": "1.2",
                "content": "Scope includes all full-time, part-time, and contract employees. Excludes third-party vendor payments which are handled by the Accounts Payable team."
            }
        ]
        
        for md in mock_data:
            rag_service.ingest_section(
                note_id=md["note_id"],
                team=md["team"],
                section_id=md["section_id"],
                content=md["content"]
            )
        print("Mock data ingested successfully into ChromaDB!")
        return

    print(f"Found {len(approved_notes)} approved notes. Ingesting sections...")
    count = 0
    for note in approved_notes:
        for section in note.sections:
            if section.content:
                rag_service.ingest_section(
                    note_id=note.id,
                    team=note.team,
                    section_id=section.section_id,
                    content=section.content
                )
                count += 1
                
    print(f"Successfully ingested {count} sections into ChromaDB!")

if __name__ == "__main__":
    seed_rag()
