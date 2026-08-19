from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class SectionValidationResult(BaseModel):
    section: str
    status: str  # PASS, WARNING, NEEDS_REVISION
    score: float
    issues: List[str] = []
    recommendations: List[str] = []
    severity: str  # LOW, MEDIUM, HIGH

class ValidationResponse(BaseModel):
    overall_score: float
    overall_status: str
    critical_issues: int
    warnings: int
    sections_passed: int
    sections_needing_revision: int
    section_results: List[SectionValidationResult]
    cross_section_issues: List[Dict[str, str]] = [] # [{'issue': '...', 'severity': '...'}]

class ProcessSectionSchema(BaseModel):
    section_id: str
    content: Optional[str] = None
    structured_data: Optional[List[Dict[str, Any]]] = None

class ProcessNoteSchema(BaseModel):
    process_name: str
    team: str
    version: str
    subject_matter_expert: Optional[str] = None
    process_owner: Optional[str] = None
    process_champion: Optional[str] = None
    process_reviewer: Optional[str] = None
    process_approver: Optional[str] = None
    effective_date: Optional[str] = None
    next_review_date: Optional[str] = None
    sections: List[ProcessSectionSchema] = []
