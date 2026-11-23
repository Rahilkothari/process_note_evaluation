import yaml
import os
from typing import Dict, Any, List
from models.schemas import ProcessNoteSchema, ValidationResponse, SectionValidationResult
from core.rule_validator import RuleValidator
from core.ai_validator import AIValidator
from core.cross_section_validator import CrossSectionValidator
from dotenv import load_dotenv
import os

try:
    load_dotenv(dotenv_path='.env')
except Exception:
    pass

class ValidationEngine:
    def __init__(self):
        self.rule_validator = RuleValidator()
        self.ai_validator = AIValidator()
        self.cross_validator = CrossSectionValidator()
        self.sections_config = self._load_yaml("config/sections.yaml")
        self.rules_config = self._load_yaml("config/validation_rules.yaml")

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        full_path = os.path.join(os.getcwd(), path)
        try:
            with open(full_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return {}

    def run_validation(self, note: ProcessNoteSchema) -> ValidationResponse:
        pass_threshold = float(os.getenv("PASS_THRESHOLD", 75))
        warning_threshold = float(os.getenv("WARNING_THRESHOLD", 65))

        section_results: List[SectionValidationResult] = []

        import concurrent.futures

        def validate_single_section(section):
            section_config = next((s for s in self.sections_config.get("sections", []) if s["id"] == section.section_id), {})
            section_name = section_config.get("name", section.section_id)

            # Check for completely empty section
            stype = section_config.get("type", "text")
            is_empty = False
            if stype == "table":
                from core.rule_validator import is_row_meaningfully_filled
                raw_rows = section.structured_data or []
                valid_rows = [r for r in raw_rows if is_row_meaningfully_filled(section.section_id, r)]
                is_empty = (len(valid_rows) == 0)
            elif stype in ["file", "flowchart"]:
                is_empty = not section.content or not str(section.content).strip() or str(section.content).strip().lower() in ["none", "nan", "null"]
            else:
                is_empty = not section.content or not str(section.content).strip() or str(section.content).strip().lower() in ["none", "nan", "null"]

            if is_empty:
                return SectionValidationResult(
                    section=section_name,
                    status="NEEDS_REVISION",
                    score=0.0,
                    issues=["Section content is empty. Required operational details must be provided."],
                    recommendations=["Please populate this section using the guided questions."],
                    severity="HIGH"
                )

            # Layer 1: Deterministic rules
            rule_issues = self.rule_validator.validate(section, self.sections_config)

            # Layer 2: AI evaluation
            ai_result = self.ai_validator.validate(section, self.sections_config, self.rules_config, note.team)
            ai_result.section = section_name # Ensure name is set

            if rule_issues:
                # Merge deterministic rule issues into findings
                existing_issues = list(ai_result.issues or [])
                for r_iss in rule_issues:
                    if r_iss not in existing_issues:
                        existing_issues.append(r_iss)
                ai_result.issues = existing_issues

                # Classify rule issues into major vs minor for 4-tier scale (0, 50, 75, 100)
                has_major_rule_issue = any(
                    any(k in r.lower() for k in ["empty", "missing", "conflict", "required", "invalid", "cannot be blank"])
                    for r in rule_issues
                )
                if has_major_rule_issue:
                    if ai_result.score > 50:
                        ai_result.score = 50.0
                else:
                    if ai_result.score > 75:
                        ai_result.score = 75.0

            # Inculcate standard activity coverage check directly inside Section 1.13 (RACI Matrix)
            if section.section_id == "1.13":
                desc_sec = next((s for s in note.sections if str(s.section_id).strip() == "1.12"), None)
                if desc_sec and desc_sec.structured_data and section.structured_data:
                    desc_activities = [str(r.get("Activity", "")).strip() for r in desc_sec.structured_data if r.get("Activity")]
                    raci_activities = [str(r.get("Activity name", r.get("Activity", ""))).strip() for r in section.structured_data if r.get("Activity name") or r.get("Activity")]

                    missing_major = []
                    for act in desc_activities:
                        if act and not any(act.lower() in r_act.lower() or r_act.lower() in act.lower() for r_act in raci_activities):
                            missing_major.append(act)

                    if missing_major:
                        cov_note = f"Activity Coverage: Operational activities from Section 1.12 ({', '.join(missing_major[:3])}) are not mapped in this RACI table. Ensure primary process workflows have designated Responsible (R) and Accountable (A) roles."
                        existing_issues = list(ai_result.issues or [])
                        if not any("Activity Coverage" in iss or "missing from this RACI" in iss for iss in existing_issues):
                            existing_issues.append(cov_note)
                            ai_result.issues = existing_issues
                        if not ai_result.recommendations:
                            ai_result.recommendations = ["Add missing process activities from Section 1.12 to the RACI matrix to ensure every operational workflow has an assigned owner."]

            if ai_result.score >= 75:
                ai_result.status = "PASS"
                ai_result.severity = "LOW"
            elif ai_result.score >= 50:
                ai_result.status = "WARNING"
                ai_result.severity = "MEDIUM"
            else:
                ai_result.status = "NEEDS_REVISION"
                ai_result.severity = "HIGH"

            return ai_result

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(validate_single_section, note.sections))
            section_results.extend(results)

        # 2. Cross-section validation disabled to strictly adhere to standard format and guidelines
        cross_section_issues = []

        # 3. Aggregate scores strictly based on the 22 standard sections
        total_score = sum([res.score for res in section_results]) if section_results else 0
        raw_score = total_score / len(section_results) if section_results else 0
        overall_score = max(0.0, round(raw_score, 1))

        critical_issues = sum([1 for res in section_results if res.severity == "HIGH"])
        warnings = sum([1 for res in section_results if res.severity == "MEDIUM" or res.status == "WARNING"])

        sections_passed = sum([1 for res in section_results if res.status == "PASS"])
        sections_needing_revision = sum([1 for res in section_results if res.status == "NEEDS_REVISION"])

        # Status follows the overall score percentage bands:
        # Score >= 75.0% -> PASS
        # 65.0% <= Score < 75.0% -> WARNING
        # Score < 65.0% -> NEEDS_REVISION
        if overall_score >= pass_threshold:
            overall_status = "PASS"
        elif overall_score >= warning_threshold:
            overall_status = "WARNING"
        else:
            overall_status = "NEEDS_REVISION"

        return ValidationResponse(
            overall_score=round(overall_score, 1),
            overall_status=overall_status,
            critical_issues=critical_issues,
            warnings=warnings,
            sections_passed=sections_passed,
            sections_needing_revision=sections_needing_revision,
            section_results=section_results,
            cross_section_issues=cross_section_issues
        )
