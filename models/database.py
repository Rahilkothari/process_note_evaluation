from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./process_notes.db")

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String)  # 'creator', 'reviewer', 'admin'

class ProcessNote(Base):
    __tablename__ = "process_notes"

    id = Column(Integer, primary_key=True, index=True)
    process_name = Column(String, index=True)
    team = Column(String)
    version = Column(String)
    status = Column(String)  # DRAFT, NEEDS_REVISION, UNDER_REVIEW, APPROVED
    document_type = Column(String, default="PROCESS_NOTE") # PROCESS_NOTE or NEW_INITIATIVE
    
    # Metadata fields
    subject_matter_expert = Column(String, nullable=True)
    process_owner = Column(String, nullable=True)
    process_champion = Column(String, nullable=True)
    process_reviewer = Column(String, nullable=True)
    process_approver = Column(String, nullable=True)
    effective_date = Column(String, nullable=True)
    next_review_date = Column(String, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sections = relationship("ProcessSection", back_populates="process_note", cascade="all, delete-orphan")
    validations = relationship("ValidationRun", back_populates="process_note", cascade="all, delete-orphan")
    reviews = relationship("ReviewHistory", back_populates="process_note", cascade="all, delete-orphan")

class ProcessSection(Base):
    __tablename__ = "process_sections"

    id = Column(Integer, primary_key=True, index=True)
    process_note_id = Column(Integer, ForeignKey("process_notes.id"))
    process_name = Column(String)  # Denormalized for easier querying
    section_id = Column(String)  # e.g. "1.1", "1.10"
    content = Column(Text, nullable=True)  # For large text areas
    structured_data = Column(JSON, nullable=True)  # For tables and structured input

    process_note = relationship("ProcessNote", back_populates="sections")

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    process_note_id = Column(Integer, ForeignKey("process_notes.id"))
    process_name = Column(String)  # Denormalized for easier querying
    timestamp = Column(DateTime, default=datetime.utcnow)
    overall_score = Column(Float, nullable=True)
    status = Column(String)  # PASS, NEEDS_REVISION
    model_used = Column(String)

    process_note = relationship("ProcessNote", back_populates="validations")
    findings = relationship("ValidationFinding", back_populates="validation_run", cascade="all, delete-orphan")

class ValidationFinding(Base):
    __tablename__ = "validation_findings"

    id = Column(Integer, primary_key=True, index=True)
    validation_id = Column(Integer, ForeignKey("validation_runs.id"))
    process_name = Column(String)  # Denormalized for easier querying
    section_id = Column(String, nullable=True)  # Can be None if it's a cross-section finding
    severity = Column(String)  # LOW, MEDIUM, HIGH
    status = Column(String)  # PASS, WARNING, NEEDS_REVISION
    score = Column(Float, nullable=True)
    issue = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    is_cross_section = Column(Integer, default=0) # 1 if True

    validation_run = relationship("ValidationRun", back_populates="findings")

class ReviewHistory(Base):
    __tablename__ = "review_history"

    id = Column(Integer, primary_key=True, index=True)
    process_note_id = Column(Integer, ForeignKey("process_notes.id"))
    process_name = Column(String)  # Denormalized for easier querying
    reviewer = Column(String)
    action = Column(String)  # SUBMITTED, APPROVED, SENT_BACK
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    process_note = relationship("ProcessNote", back_populates="reviews")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    is_read = Column(Integer, default=0) # 0 for False, 1 for True
    process_note_id = Column(Integer, ForeignKey("process_notes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="notifications")
    process_note = relationship("ProcessNote")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
