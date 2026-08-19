import yaml
import os
from typing import Dict, Any, List
from models.schemas import ProcessNoteSchema, ValidationResponse, SectionValidationResult
from core.rule_validator import RuleValidator
from core.ai_validator import AIValidator
from core.cross_section_validator import CrossSectionValidator
from dotenv import load_dotenv

load_dotenv()

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
        section_results: List[SectionValidationResult] = []
        
        # 1. Run individual section validations (Rule -> AI)
        for section in note.sections:
            section_config = next((s for s in self.sections_config.get("sections", []) if s["id"] == section.section_id), {})
            section_name = section_config.get("name", section.section_id)
            
            # Layer 1: Deterministic
            rule_issues = self.rule_validator.validate(section, self.sections_config)
            
            if rule_issues:
                # If deterministic fails, don't even send to AI
                section_results.append(SectionValidationResult(
                    section=section_name,
                    status="NEEDS_REVISION",
                    score=0.0,
                    issues=rule_issues,
                    recommendations=["Please fill in the required fields correctly before AI validation."],
                    severity="HIGH"
                ))
            else:
                # Layer 2: AI
                ai_result = self.ai_validator.validate(section, self.sections_config)
                ai_result.section = section_name # Ensure name is set
                section_results.append(ai_result)

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
        pass_threshold = float(os.getenv("PASS_THRESHOLD", 80))
        warning_threshold = float(os.getenv("WARNING_THRESHOLD", 70))
        
        total_score = sum([res.score for res in section_results]) if section_results else 0
        overall_score = total_score / len(section_results) if section_results else 0
        
        critical_issues = sum([1 for res in section_results if res.severity == "HIGH"])
        warnings = sum([1 for res in section_results if res.severity == "MEDIUM" or res.status == "WARNING"])
        
        sections_passed = sum([1 for res in section_results if res.status == "PASS"])
        sections_needing_revision = sum([1 for res in section_results if res.status == "NEEDS_REVISION"])
        
        if critical_issues > 0 or sections_needing_revision > 0 or overall_score < warning_threshold:
            overall_status = "NEEDS_REVISION"
        elif overall_score < pass_threshold or warnings > 0:
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
