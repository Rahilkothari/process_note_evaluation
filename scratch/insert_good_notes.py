import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, ProcessNote, ProcessSection, User
import uuid

def create_good_notes():
    db = SessionLocal()
    
    # Get any user or create one
    user = db.query(User).first()
    if not user:
        user = User(name="Rahil", email="rahilkk07@gmail.com", role="admin")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Note 1: Volunteering
    note1 = ProcessNote(
        document_id=str(uuid.uuid4()),
        process_name="Volunteer Management & Deployment",
        team="Volunteering",
        version="1.0",
        status="DRAFT",
        subject_matter_expert="Jane Doe",
        process_owner="John Smith",
        process_champion="Alice Johnson",
        process_reviewer="Bob Williams",
        process_approver="Rahil Kothari",
        effective_date="2024-01-01",
        next_review_date="2025-01-01",
        created_by=user.id
    )
    db.add(note1)
    db.flush()

    sections_note1 = [
        ProcessSection(
            process_note_id=note1.id,
            process_name=note1.process_name,
            section_id="1.1",
            structured_data=[
                {"Name": "John Smith", "Role": "Process Owner", "Function": "Volunteering Head", "Sign": "JS", "Date": "2024-01-01"},
                {"Name": "Bob Williams", "Role": "Reviewer", "Function": "Compliance", "Sign": "BW", "Date": "2024-01-02"},
                {"Name": "Rahil Kothari", "Role": "Approver", "Function": "Director", "Sign": "RK", "Date": "2024-01-03"}
            ]
        ),
        ProcessSection(
            process_note_id=note1.id,
            process_name=note1.process_name,
            section_id="1.6",
            content="This process covers the end-to-end volunteer management lifecycle including types of volunteering, onboarding, registration, eligibility criteria, allocation, engagement, attendance tracking, training, grievance handling, and the volunteer exit process across all organizational programmes. It explicitly includes background verification and safeguarding requirements."
        ),
        ProcessSection(
            process_note_id=note1.id,
            process_name=note1.process_name,
            section_id="1.10",
            content="To ensure a standardized, compliant, and engaging volunteering experience that aligns with our organizational goals, while ensuring all volunteers are properly vetted, trained, deployed, and tracked."
        ),
        ProcessSection(
            process_note_id=note1.id,
            process_name=note1.process_name,
            section_id="1.12",
            structured_data=[
                {"Sr. No.": 1, "Activity": "Registration", "Description": "Volunteer signs up and provides eligibility info", "Owner/Role": "Volunteer Coord", "TAT": "1 day"},
                {"Sr. No.": 2, "Activity": "Background Check", "Description": "Conduct safeguarding and background verification", "Owner/Role": "Compliance", "TAT": "5 days"},
                {"Sr. No.": 3, "Activity": "Orientation", "Description": "Provide capacity building and training to volunteer", "Owner/Role": "Trainer", "TAT": "2 days"},
                {"Sr. No.": 4, "Activity": "Deployment", "Description": "Allocate volunteer to programme and track attendance", "Owner/Role": "Programme Mgr", "TAT": "Ongoing"},
                {"Sr. No.": 5, "Activity": "Grievance Handling", "Description": "Escalation mechanism for volunteer issues", "Owner/Role": "HR", "TAT": "3 days"},
                {"Sr. No.": 6, "Activity": "Exit & Certification", "Description": "Exit process and issuance of certificates based on eligibility", "Owner/Role": "Volunteer Coord", "TAT": "7 days"}
            ]
        ),
        ProcessSection(
            process_note_id=note1.id,
            process_name=note1.process_name,
            section_id="1.16",
            structured_data=[
                {"Sub Process": "Background Check", "Risk Description": "Volunteer deployed without verification", "Root Cause": "Process gap", "Type of Risk": "Compliance", "Risk Impact": "High", "Level of Risk": "High", "Control Description": "System block prevents deployment if verification status is not Approved", "Control Frequency": "Per volunteer"}
            ]
        ),
        ProcessSection(
            process_note_id=note1.id,
            process_name=note1.process_name,
            section_id="1.22",
            structured_data=[
                {"Supplier (Dept)": "External", "Input": "Volunteer Profile", "Key Process Step": "Registration", "Output": "Registered Volunteer", "Customer (Dept)": "Volunteer Coord"},
                {"Supplier (Dept)": "Compliance", "Input": "Background Report", "Key Process Step": "Background Check", "Output": "Vetted Volunteer", "Customer (Dept)": "Programme Mgr"}
            ]
        )
    ]
    db.add_all(sections_note1)


    # Note 2: Communications
    note2 = ProcessNote(
        document_id=str(uuid.uuid4()),
        process_name="Corporate Communications & Branding",
        team="Communications",
        version="1.0",
        status="DRAFT",
        subject_matter_expert="Sarah Lee",
        process_owner="Mike Davis",
        process_champion="Emma Wilson",
        process_reviewer="Bob Williams",
        process_approver="Rahil Kothari",
        effective_date="2024-01-01",
        next_review_date="2025-01-01",
        created_by=user.id
    )
    db.add(note2)
    db.flush()

    sections_note2 = [
        ProcessSection(
            process_note_id=note2.id,
            process_name=note2.process_name,
            section_id="1.1",
            structured_data=[
                {"Name": "Mike Davis", "Role": "Process Owner", "Function": "Comms Head", "Sign": "MD", "Date": "2024-01-01"},
                {"Name": "Bob Williams", "Role": "Reviewer", "Function": "Compliance", "Sign": "BW", "Date": "2024-01-02"},
                {"Name": "Rahil Kothari", "Role": "Approver", "Function": "Director", "Sign": "RK", "Date": "2024-01-03"}
            ]
        ),
        ProcessSection(
            process_note_id=note2.id,
            process_name=note2.process_name,
            section_id="1.6",
            content="This process covers branding guidelines, brand approval process, communication strategy, content development, social media management, event communications, PR, creative design, photography/videography consent management, collateral development, and communication budget management for all internal and external communications."
        ),
        ProcessSection(
            process_note_id=note2.id,
            process_name=note2.process_name,
            section_id="1.10",
            content="To ensure consistent, compliant, and effective brand messaging across all channels, while maintaining strict adherence to brand guidelines, budget controls, and legal consent management for media usage."
        ),
        ProcessSection(
            process_note_id=note2.id,
            process_name=note2.process_name,
            section_id="1.12",
            structured_data=[
                {"Sr. No.": 1, "Activity": "Strategy Planning", "Description": "Develop communication strategy and annual calendar", "Owner/Role": "Comms Head", "TAT": "30 days"},
                {"Sr. No.": 2, "Activity": "Content & Creative", "Description": "Develop content and creatives with agency coordination", "Owner/Role": "Content Mgr", "TAT": "10 days"},
                {"Sr. No.": 3, "Activity": "Brand Approval", "Description": "Approval process for logos, creatives and collateral", "Owner/Role": "Brand Mgr", "TAT": "3 days"},
                {"Sr. No.": 4, "Activity": "Media & PR", "Description": "Media engagement and press release external approvals", "Owner/Role": "PR Exec", "TAT": "2 days"},
                {"Sr. No.": 5, "Activity": "Consent Management", "Description": "Obtain and record consent for use of images/videos", "Owner/Role": "Legal/Comms", "TAT": "Prior to pub"},
                {"Sr. No.": 6, "Activity": "Vendor & Budget", "Description": "Vendor management and payment approval process", "Owner/Role": "Finance/Comms", "TAT": "15 days"}
            ]
        ),
        ProcessSection(
            process_note_id=note2.id,
            process_name=note2.process_name,
            section_id="1.16",
            structured_data=[
                {"Sub Process": "Consent Management", "Risk Description": "Using images without consent leading to legal action", "Root Cause": "Lack of tracking", "Type of Risk": "Legal", "Risk Impact": "High", "Level of Risk": "High", "Control Description": "Mandatory digital consent form attached to all media assets in the DAM system", "Control Frequency": "Per asset"}
            ]
        ),
        ProcessSection(
            process_note_id=note2.id,
            process_name=note2.process_name,
            section_id="1.22",
            structured_data=[
                {"Supplier (Dept)": "Programme", "Input": "Event details", "Key Process Step": "Content & Creative", "Output": "Draft collateral", "Customer (Dept)": "Brand Mgr"},
                {"Supplier (Dept)": "Brand Mgr", "Input": "Draft collateral", "Key Process Step": "Brand Approval", "Output": "Approved collateral", "Customer (Dept)": "Public"}
            ]
        )
    ]
    db.add_all(sections_note2)
    db.commit()

    print("Successfully created 2 high-quality process notes!")

if __name__ == "__main__":
    create_good_notes()
