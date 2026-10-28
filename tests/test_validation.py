import pytest
import os
from unittest.mock import patch, MagicMock
from models.schemas import ProcessNoteSchema, ProcessSectionSchema
from core.validation_engine import ValidationEngine

@patch('core.validation_engine.os.getenv')
def test_validation_engine_thresholds(mock_getenv):
    # Set thresholds
    def getenv_side_effect(key, default=None):
        if key == "PASS_THRESHOLD":
            return "85.0"
        elif key == "WARNING_THRESHOLD":
            return "65.0"
        return default
    
    mock_getenv.side_effect = getenv_side_effect
    
    engine = ValidationEngine()
    engine.sections_config = {"sections": [{"id": "1.1", "name": "Test Section"}]}
    engine.rules_config = {}
    
    # Mock validators to return specific scores
    engine.rule_validator.validate = MagicMock(return_value=[])
    engine.cross_validator = MagicMock()
    engine.cross_validator.validate = MagicMock(return_value=[])
    
    note = ProcessNoteSchema(
        process_note_id=1,
        process_name="Test Note",
        team="Test Team",
        version="1.0",
        sections=[ProcessSectionSchema(section_id="1.1", content="Test content", structured_data=[])]
    )
    
    from models.schemas import SectionValidationResult
    
    # Test PASS (Overall Score 100 >= 85)
    mock_ai_result = SectionValidationResult(
        section="Test Section",
        status="PASS",
        score=100.0,
        severity="LOW",
        issues=[],
        recommendations=[]
    )
    engine.ai_validator.validate = MagicMock(return_value=mock_ai_result)
    
    result = engine.run_validation(note)
    assert result.overall_status == "PASS"
    assert result.section_results[0].status == "PASS"
    
    # Test WARNING (Overall Score 75: one 100, one 50. 65 <= 75 < 85)
    note.sections.append(ProcessSectionSchema(section_id="1.2", content="Test content 2", structured_data=[]))
    
    def mock_validate(section, *args):
        if section.section_id == "1.1":
            return SectionValidationResult(section="Test Section 1", status="PASS", score=100.0, severity="LOW", issues=[], recommendations=[])
        else:
            return SectionValidationResult(section="Test Section 2", status="WARNING", score=50.0, severity="MEDIUM", issues=["Minor issue"], recommendations=[])
            
    engine.ai_validator.validate = MagicMock(side_effect=mock_validate)
    result = engine.run_validation(note)
    assert result.overall_status == "WARNING"
    # One is PASS, one is WARNING
    statuses = [s.status for s in result.section_results]
    assert "PASS" in statuses
    assert "WARNING" in statuses
    
    # Test NEEDS_REVISION (Overall Score 25: one 50, one 0. 25 < 65)
    def mock_validate_fail(section, *args):
        if section.section_id == "1.1":
            return SectionValidationResult(section="Test Section 1", status="WARNING", score=50.0, severity="MEDIUM", issues=[], recommendations=[])
        else:
            return SectionValidationResult(section="Test Section 2", status="NEEDS_REVISION", score=0.0, severity="HIGH", issues=["Major issue"], recommendations=[])
            
    engine.ai_validator.validate = MagicMock(side_effect=mock_validate_fail)
    result = engine.run_validation(note)
    assert result.overall_status == "NEEDS_REVISION"
    statuses = [s.status for s in result.section_results]
    assert "WARNING" in statuses
    assert "NEEDS_REVISION" in statuses

def test_rule_validator_basic():
    from core.rule_validator import RuleValidator
    validator = RuleValidator()
    
    section = ProcessSectionSchema(section_id="1.1", content="", structured_data=[])
    config = {"sections": [{"id": "1.1", "type": "text", "required": True}]}
    
    # Test required text field empty
    issues = validator.validate(section, config)
    assert len(issues) > 0
    assert "content is empty" in issues[0].lower()
    
    # Test required text field filled with brief text (should flag as too brief)
    section.content = "Some text"
    issues = validator.validate(section, config)
    assert len(issues) > 0
    assert "too brief" in issues[0].lower()

    # Test substantive text passes
    section.content = "This section establishes the operational protocol for onboarding partner schools with full stakeholder accountability and audit compliance across the foundation program."
    issues = validator.validate(section, config)
    assert len(issues) == 0


def test_objective_depth_validation():
    from core.rule_validator import RuleValidator
    validator = RuleValidator()
    config = {"sections": [{"id": "1.10", "name": "Objective", "type": "text"}]}

    # 1. Superficial objective (< 20 words)
    short_sec = ProcessSectionSchema(section_id="1.10", content="To onboard schools.", structured_data=[])
    issues = validator.validate(short_sec, config)
    assert any("too brief" in iss.lower() for iss in issues)

    # 2. Objective without measurable outcome
    vague_sec = ProcessSectionSchema(
        section_id="1.10",
        content="The objective of this process note is to define how partner schools are managed and handled by our team members during each school term across the region.",
        structured_data=[]
    )
    issues = validator.validate(vague_sec, config)
    assert any("lacks tangible business outcomes" in iss.lower() or "measurable" in iss.lower() for iss in issues)

    # 3. Substantive objective with measurable targets
    good_sec = ProcessSectionSchema(
        section_id="1.10",
        content="To establish a standardized, error-free onboarding mechanism for 200+ partner schools, ensuring 100% compliance with statutory norms and delivering completed agreements within a target 5-day TAT.",
        structured_data=[]
    )
    issues = validator.validate(good_sec, config)
    assert len(issues) == 0

def test_start_and_end_point_criteria_validation():
    from core.rule_validator import RuleValidator
    from config.guided_questions import build_table_rows_from_answers
    validator = RuleValidator()
    config = {
        "sections": [
            {"id": "1.7", "name": "Start Point", "type": "table"},
            {"id": "1.8", "name": "End Point", "type": "table"}
        ]
    }

    # 1. End point with "abc" exit criteria fails
    bad_rows = build_table_rows_from_answers("1.8", {"activity": "MOU handover", "exit_criteria": "abc"})
    bad_sec = ProcessSectionSchema(section_id="1.8", content="", structured_data=bad_rows)
    issues = validator.validate(bad_sec, config)
    assert len(issues) > 0
    assert any("Exit Criteria is too brief" in iss for iss in issues)

    # 2. End point with proper 4+ word criteria passes
    good_rows = build_table_rows_from_answers("1.8", {"activity": "MOU handover", "exit_criteria": "Signed agreement uploaded and ERP verification complete"})
    good_sec = ProcessSectionSchema(section_id="1.8", content="", structured_data=good_rows)
    good_issues = validator.validate(good_sec, config)
    assert len(good_issues) == 0

def test_clean_heading_hashes_removes_hashes_and_stars():
    from config.guided_questions import clean_heading_hashes
    raw = (
        "### 1.9 Introduction\n"
        "**Background & Context:**\n"
        "Establishing structured relationships is key.\n\n"
        "* Criteria 1\n"
        "* Criteria 2\n\n"
        "### Strategic & Operational Purpose:\n"
        "This note defines procedures."
    )
    cleaned = clean_heading_hashes(raw, "1.9", "Introduction")
    assert "#" not in cleaned
    assert "*" not in cleaned
    assert "Background & Context:" in cleaned
    assert "Strategic & Operational Purpose:" in cleaned
    assert "- Criteria 1" in cleaned
    assert "1.9 Introduction" not in cleaned

def test_heading_deduplication_and_preview_html():
    from config.guided_questions import clean_heading_hashes, render_section_preview_html
    duplicate_header_sample = (
        "Background Context:\n"
        "Background & Context:\n"
        "Operational framework for school onboarding.\n\n"
        "Strategic & Operational Purpose:\n"
        "To standardize partner onboarding.\n\n\n\n"
        "•  Verifiable Vetting Benchmarks: Objective criteria."
    )
    cleaned = clean_heading_hashes(duplicate_header_sample, "1.9", "Introduction")
    # Must only have one Background header, not both
    assert cleaned.count("Background") == 1
    assert "Background & Context:" in cleaned
    assert "- Verifiable Vetting Benchmarks: Objective criteria." in cleaned
    assert "\n\n\n" not in cleaned

    html_out = render_section_preview_html(cleaned)
    assert '<strong style="color: #0F172A;">Verifiable Vetting Benchmarks:</strong>' in html_out
    assert "<ul" in html_out
    assert "<li" in html_out

def test_detect_clarifications_needed():
    from services.llm_service import MockProvider
    provider = MockProvider()
    
    # Short/vague keywords should trigger clarification questions
    brief_answers = "school onboarding, safety compliance"
    questions = provider.detect_clarifications_needed("1.9", {"name": "Introduction"}, brief_answers)
    assert len(questions) > 0
    assert any("districts" in q.lower() or "categories" in q.lower() for q in questions)
    
    # Detailed comprehensive answers should not trigger clarification questions
    detailed_answers = (
        "Kotak Education Foundation establishes institutional partnerships across 200+ municipal schools "
        "in Mumbai, Thane, and Nashik districts. The operational objective is to ensure 100% adherence to "
        "safety benchmarks, facility vetting norms, and statutory permissions overseen by the Program Director."
    )
    questions_detailed = provider.detect_clarifications_needed("1.9", {"name": "Introduction"}, detailed_answers)
    assert len(questions_detailed) == 0





