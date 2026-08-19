from typing import Dict, Any, List
from models.schemas import ProcessSectionSchema

class RuleValidator:
    def validate(self, section: ProcessSectionSchema, config: Dict[str, Any]) -> List[str]:
        issues = []
        
        section_config = next((s for s in config.get("sections", []) if s["id"] == section.section_id), None)
        if not section_config:
            return issues

        # Check for missing content
        if section_config["type"] == "text":
            if not section.content or not str(section.content).strip():
                issues.append("Section content is empty.")
        
        elif section_config["type"] == "table":
            if not section.structured_data or len(section.structured_data) == 0:
                issues.append("Table is empty. At least one row is required.")
            else:
                # Check for empty mandatory fields in the table
                fields = section_config.get("fields", [])
                for idx, row in enumerate(section.structured_data):
                    for field in fields:
                        if field not in row or not str(row[field]).strip():
                            issues.append(f"Row {idx+1}: Missing required field '{field}'.")

                # specific deterministic checks
                if section.section_id == "1.1": # Approval matrix
                    roles = [str(r.get("Role", "")).lower() for r in section.structured_data]
                    mandatory_roles = ["process owner", "process reviewer", "process approver"]
                    for m_role in mandatory_roles:
                        if not any(m_role in role for role in roles):
                            issues.append(f"Missing mandatory role: {m_role.title()}")

        return issues
