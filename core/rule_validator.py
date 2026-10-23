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

        elif section_config["type"] in ["file", "flowchart"]:
            if not section.content or not str(section.content).strip():
                issues.append("Flowchart diagram or uploaded file is missing. Please generate or attach a flowchart.")
        
        elif section_config["type"] == "table":
            if not section.structured_data or len(section.structured_data) == 0:
                issues.append("Table is empty. At least one row is required.")
            else:
                # 1.1 Approval matrix
                if section.section_id == "1.1":
                    roles = [str(r.get("Role", "")).lower() for r in section.structured_data]
                    names = [str(r.get("Name", "")).lower() for r in section.structured_data]
                    mandatory_roles = ["process owner", "process reviewer", "process approver"]
                    for m_role in mandatory_roles:
                        if not any(m_role in r_val for r_val in roles) and not any(m_role in n_val for n_val in names):
                            issues.append(f"Missing mandatory role: {m_role.title()}")

                # 1.12 Process Description
                elif section.section_id == "1.12":
                    for idx, row in enumerate(section.structured_data, 1):
                        act = str(row.get("Activity", "")).strip()
                        desc = str(row.get("Description", "")).strip()
                        if not act or act.lower() in ["none", "nan"]:
                            issues.append(f"Row {idx}: Activity title is missing.")
                        if not desc or desc.lower() in ["none", "nan"]:
                            issues.append(f"Row {idx}: Activity description is missing.")

                # 1.13 RACI Matrix
                elif section.section_id == "1.13":
                    boolean_terms = {"yes", "no", "y", "n", "true", "false", "na", "n/a"}
                    for idx, row in enumerate(section.structured_data, 1):
                        # Support both new standard format and legacy format
                        act_name = str(row.get("Activity name", row.get("Activity", row.get("Roles", "")))).strip()
                        resp = str(row.get("Responsible", row.get("Responsible ( R )", row.get("Responsible (R)", "")))).strip()
                        acct = str(row.get("Accountable", row.get("Accountable ( A )", row.get("Accountable (A)", "")))).strip()

                        if not act_name or act_name.lower() in ["none", "nan"]:
                            issues.append(f"Row {idx}: Activity name is missing in RACI Matrix.")
                        
                        if resp.lower() in boolean_terms:
                            issues.append(f"Row {idx} ({act_name}): 'Responsible' specifies '{resp}'. Must specify a job title/designation (e.g. Manager, PH), not Yes/No.")
                        if acct.lower() in boolean_terms:
                            issues.append(f"Row {idx} ({act_name}): 'Accountable' specifies '{acct}'. Must specify a job title/designation (e.g. Manager, Vertical Lead), not Yes/No.")

        return issues
