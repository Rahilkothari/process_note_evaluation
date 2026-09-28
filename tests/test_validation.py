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
    
    # Test required text field filled
    section.content = "Some text"
    issues = validator.validate(section, config)
    assert len(issues) == 0
