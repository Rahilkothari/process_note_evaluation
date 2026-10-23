from typing import List, Dict, Any
from services.llm_service import get_llm_provider

class CrossSectionValidator:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    def validate(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        desc_sec = next((s for s in all_sections if s.get("section_id") == "1.12"), None)
        raci_sec = next((s for s in all_sections if s.get("section_id") == "1.13"), None)
        rules_sec = next((s for s in all_sections if s.get("section_id") == "1.14"), None)
        kpi_sec = next((s for s in all_sections if s.get("section_id") == "1.5"), None)
        flow_sec = next((s for s in all_sections if s.get("section_id") == "1.11"), None)

        desc_data = desc_sec.get("structured_data") if desc_sec else []
        raci_data = raci_sec.get("structured_data") if raci_sec else []
        rules_data = rules_sec.get("structured_data") if rules_sec else []

        # 1. Deterministic Cross Check: RACI Matrix vs Process Description
        if desc_data and raci_data:
            desc_activities = [str(r.get("Activity", "")).strip() for r in desc_data if r.get("Activity")]
            raci_activities = [str(r.get("Activity name", r.get("Activity", ""))).strip() for r in raci_data if r.get("Activity name") or r.get("Activity")]
            
            missing_in_raci = []
            for act in desc_activities:
                if not any(act.lower() in r_act.lower() or r_act.lower() in act.lower() for r_act in raci_activities):
                    missing_in_raci.append(act)

            if missing_in_raci:
                issues.append({
                    "issue": f"Activities from Process Description (1.12) are missing from the RACI Matrix (1.13): {', '.join(missing_in_raci[:3])}.",
                    "severity": "HIGH",
                    "questions": [
                        f"Who is Responsible and Accountable for executing: '{missing_in_raci[0]}'?"
                    ],
                    "related_sections": ["1.12", "1.13"]
                })

        # 2. Deterministic Cross Check: Business Rules vs Process Description
        if rules_data and desc_data:
            desc_corpus = " ".join([
                str(r.get("Activity", "")) + " " + str(r.get("Description", "")) 
                for r in desc_data
            ]).lower()

            for r in rules_data:
                rule_text = str(r.get("Business Rules", r.get("Business Rule", ""))).strip()
                if not rule_text or rule_text.lower() in ["na", "n/a", "none"]:
                    continue

                # Check if rule has explicit verification keywords
                check_keywords = ["check", "verify", "verification", "approval", "approve", "sign-off", "audit", "grammar", "rubric", "inspection"]
                active_keywords = [kw for kw in check_keywords if kw in rule_text.lower()]
                
                if active_keywords:
                    # Look for presence in Process Description
                    matched = any(kw in desc_corpus for kw in active_keywords)
                    if not matched:
                        issues.append({
                            "issue": f"Business Rule '{rule_text}' specifies a mandatory check/rule, but the process for conducting this check is not documented in Section 1.12 (Process Description).",
                            "severity": "HIGH",
                            "questions": [
                                f"For Business Rule '{rule_text}': Who conducts this check, what tools or checklists do they use, and how is completion verified before proceeding?"
                            ],
                            "related_sections": ["1.12", "1.14"]
                        })

        # 3. Deep AI Cross-Section Review (KPIs, Flowchart alignment, nuances)
        try:
            ai_cross_issues = self.llm_provider.validate_cross_sections(all_sections)
            # Deduplicate by issue text prefix
            existing_texts = [iss["issue"].lower()[:40] for iss in issues]
            for ai_iss in ai_cross_issues:
                issue_text = ai_iss.get("issue", "")
                if issue_text and not any(issue_text.lower()[:40] in ex for ex in existing_texts):
                    issues.append(ai_iss)
        except Exception as e:
            print(f"AI cross-section check error: {e}")

        return issues
