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
