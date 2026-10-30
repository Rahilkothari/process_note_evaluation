import pytest
from services.llm_service import MockProvider
from config.guided_questions import build_table_rows_from_answers
from models.schemas import ProcessSectionSchema
from core.rule_validator import RuleValidator

def test_audit_guided_approval_matrix_segregation_of_duties():
    provider = MockProvider()
    answers = {
        "owner": "Aarav Sharma",
        "reviewer": "Aarav Sharma",
        "approver": "Aarav Sharma"
    }
    res = provider.audit_guided_input("1.1", {"name": "Approval Matrix", "type": "table"}, answers, "School Onboarding", "Operations")
    assert res["status"] == "CRITICAL"
    assert any("Governance Conflict" in issue for issue in res["issues"])
    assert any("owner" in k for k in res["autofill_fixes"].keys())

def test_audit_guided_criteria_placeholder():
    provider = MockProvider()
    answers = {"entry_criteria": "start"}
    res = provider.audit_guided_input("1.7", {"name": "Start Point", "type": "table"}, answers, "School Onboarding", "Operations")
    assert res["status"] == "CRITICAL"
    assert any("meaningful operational milestone" in issue for issue in res["issues"])

def test_audit_guided_compliant_matrix():
    provider = MockProvider()
    answers = {
        "owner": "John Doe | Operations | JD",
        "reviewer": "Jane Smith | Quality | JS",
        "approver": "Robert Brown | Director | RB"
    }
    res = provider.audit_guided_input("1.1", {"name": "Approval Matrix", "type": "table"}, answers, "School Onboarding", "Operations")
    assert res["status"] == "COMPLIANT"
    assert len(res["issues"]) == 0

def test_optional_reviewer_handling():
    # 1. When reviewer is left blank, build_table_rows_from_answers generates 2-row table (Owner + Approver)
    answers = {
        "owner_name": "Aarav Sharma",
        "owner_func": "Operations",
        "owner_sign": "AS",
        "owner_date": "2026-10-01",
        "reviewer_name": "",  # Optional, left blank
        "approver_name": "Vikramaditya Roy",
        "approver_func": "Field Programs",
        "approver_sign": "VR",
        "approver_date": "2026-10-02"
    }
    rows = build_table_rows_from_answers("1.1", answers)
    assert len(rows) == 2
    assert rows[0]["Role"] == "Process Owner"
    assert rows[1]["Role"] == "Process Approver"

    # 2. RuleValidator accepts 2-row table with Owner and Approver without requiring Reviewer
    validator = RuleValidator()
    config = {"sections": [{"id": "1.1", "name": "Approval Matrix", "type": "table"}]}
    sec = ProcessSectionSchema(section_id="1.1", content="", structured_data=rows)
    issues = validator.validate(sec, config)
    assert len(issues) == 0

    # 3. AI Auditor does not complain about missing Reviewer
    provider = MockProvider()
    audit_res = provider.audit_guided_input("1.1", {"name": "Approval Matrix", "type": "table"}, answers, "School Onboarding", "Operations")
    assert audit_res["status"] == "COMPLIANT"
    assert len(audit_res["issues"]) == 0

def test_audit_guided_existing_saved_rows_acknowledged_in_section_1_4():
    provider = MockProvider()
    # 3 saved rows in Section 1.4 (Related Documents)
    saved_rows = [
        {"Doc ID": "SOP-OPS-001", "Document Name": "School Onboarding Policy", "Forms / Templates": "FORM-01"},
        {"Doc ID": "SOP-OPS-002", "Document Name": "Infrastructure Verification SOP", "Forms / Templates": "FORM-02"},
        {"Doc ID": "POL-GOV-003", "Document Name": "Code of Conduct & Governance", "Forms / Templates": ""}
    ]
    # Blank inputs for Row 4 (when user clicks Check with AI without typing new row)
    blank_draft_answers = {"sop_id": "", "doc_name": "", "forms": ""}
    
    res = provider.audit_guided_input(
        section_id="1.4",
        section_config={"name": "Related Documents", "type": "table"},
        answers_dict=blank_draft_answers,
        process_name="Partner School Onboarding",
        team_name="School Education",
        existing_sections_data={"1.4": saved_rows},
        current_section_saved=saved_rows
    )
    # Must be COMPLIANT and acknowledge the 3 saved rows, never say completely empty!
    assert res["status"] == "COMPLIANT"
    assert "3 documented reference(s)" in res["summary"]
    assert "sufficient and compliant" in res["summary"]
    assert len(res["issues"]) == 0

def test_audit_guided_completely_empty_section():
    provider = MockProvider()
    blank_answers = {"sop_id": "", "doc_name": "", "forms": ""}
    res = provider.audit_guided_input(
        section_id="1.4",
        section_config={"name": "Related Documents", "type": "table"},
        answers_dict=blank_answers,
        process_name="Partner School Onboarding",
        team_name="School Education",
        existing_sections_data={},
        current_section_saved=[]
    )
    assert res["status"] == "WARNING"
    assert "No content has been added" in res["issues"][0]

