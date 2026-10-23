from typing import Dict, Any
from models.schemas import ProcessSectionSchema, SectionValidationResult
from services.llm_service import get_llm_provider
import json

class AIValidator:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    def validate(self, section: ProcessSectionSchema, config: Dict[str, Any], rules_config: Dict[str, Any] = None, team_name: str = "") -> SectionValidationResult:
        section_config = next((s for s in config.get("sections", []) if s["id"] == section.section_id), None)
        if not section_config:
             return SectionValidationResult(
                section=section.section_id,
                status="PASS",
                score=100.0,
                severity="LOW"
            )

        # Prepare content for LLM
        content_to_validate = ""
        if section_config["type"] in ["text", "file", "flowchart"]:
            content_to_validate = section.content or ""
        elif section_config["type"] == "table":
            content_to_validate = json.dumps(section.structured_data) if section.structured_data else ""
        
        if not content_to_validate or not str(content_to_validate).strip():
             return SectionValidationResult(
                section=section_config.get("name", section.section_id),
                status="NEEDS_REVISION",
                score=0.0,
                severity="HIGH",
                issues=["Section content is empty. Operational details must be provided."],
                recommendations=["Use the AI Process Co-pilot above to draft this section with guided questions."],
                questions=["What are the primary operational details for this section?"]
            )

        return self.llm_provider.validate_section(content_to_validate, section_config, rules_config, team_name)
