import pytest
from services.llm_service import MockProvider

def test_audit_guided_approval_matrix_segregation_of_duties():
    provider = MockProvider()
    answers = {
        "owner": "Aarav Sharma",
        "reviewer": "Aarav Sharma",
        "approver": "Aarav Sharma"
    }
    res = provider.audit_guided_input("1.1", {"name": "Approval Matrix", "type": "table"}, answers, "School Onboarding", "Operations")
    assert res["status"] == "CRITICAL"
    assert any("Segregation of Duties" in issue for issue in res["issues"])
    assert any("owner" in k for k in res["autofill_fixes"].keys())

def test_audit_guided_criteria_length():
    provider = MockProvider()
    answers = {"entry_criteria": "start"}
    res = provider.audit_guided_input("1.7", {"name": "Start Point", "type": "table"}, answers, "School Onboarding", "Operations")
    assert res["status"] in ["WARNING", "CRITICAL"]
    assert any("too brief" in issue for issue in res["issues"])

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
