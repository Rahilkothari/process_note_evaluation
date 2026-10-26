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
                is_empty = not section.structured_data or len(section.structured_data) == 0
            elif stype in ["file", "flowchart"]:
                is_empty = not section.content or not str(section.content).strip()
            else:
                is_empty = not section.content or not str(section.content).strip()

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

                # If rule issues exist, cap the score at WARNING (50.0) so minor gaps don't falsely pass
                if ai_result.score > 50:
                    ai_result.score = 50.0
                    ai_result.status = "WARNING"
                    ai_result.severity = "MEDIUM"

            if ai_result.score >= 100:
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

        # 2. Run Cross-section validation
        all_sections_dict = []
        for s in note.sections:
            all_sections_dict.append({
                "section_id": s.section_id,
                "content": s.content,
                "structured_data": s.structured_data
            })
            
        cross_section_issues = self.cross_validator.validate(all_sections_dict)

        # 3. Aggregate scores
        total_score = sum([res.score for res in section_results]) if section_results else 0
        overall_score = total_score / len(section_results) if section_results else 0
        
        critical_issues = sum([1 for res in section_results if res.severity == "HIGH"]) + sum([1 for cr in cross_section_issues if cr.get("severity") == "HIGH"])
        warnings = sum([1 for res in section_results if res.severity == "MEDIUM" or res.status == "WARNING"]) + sum([1 for cr in cross_section_issues if cr.get("severity") != "HIGH"])
        
        sections_passed = sum([1 for res in section_results if res.status == "PASS"])
        sections_needing_revision = sum([1 for res in section_results if res.status == "NEEDS_REVISION"])
        
        if critical_issues > 0 or sections_needing_revision > 0 or overall_score < warning_threshold:
            overall_status = "NEEDS_REVISION"
        elif warnings > 0 or overall_score < pass_threshold:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

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
