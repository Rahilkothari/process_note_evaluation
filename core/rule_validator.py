from typing import Dict, Any, List
from models.schemas import ProcessSectionSchema

class RuleValidator:
    def validate(self, section: ProcessSectionSchema, config: Dict[str, Any]) -> List[str]:
        issues = []
        
        section_config = next((s for s in config.get("sections", []) if s["id"] == section.section_id), None)
        if not section_config:
            return issues

        # Check for text sections depth and substance
        if section_config["type"] == "text":
            content_str = str(section.content or "").strip()
            if not content_str:
                issues.append("Section content is empty.")
            else:
                words = content_str.split()
                word_count = len(words)
                content_lower = content_str.lower()

                # 1.10 Objective: Must not be superficial; must state purpose & measurable outcome
                if section.section_id == "1.10":
                    if word_count < 20:
                        issues.append(f"Objective is too brief ({word_count} words). A professional process note objective must state the clear operational purpose, scope of impact, and measurable business outcomes (e.g., TAT targets, accuracy thresholds, compliance goals).")
                    elif not any(term in content_lower for term in ["target", "outcome", "ensure", "achieve", "deliver", "%", "tat", "timeline", "standard", "quality", "compliant", "timely", "error"]):
                        issues.append("Objective lacks tangible business outcomes or measurable performance targets. Specify what measurable success looks like.")

                # 1.9 Introduction: Must articulate background context and rationale
                elif section.section_id == "1.9":
                    if word_count < 25:
                        issues.append(f"Introduction is too brief ({word_count} words). Must articulate the organizational background, operational setting, and the rationale for standardizing this process.")

                # 1.6 Process Coverage / Scope: Must define both in-scope and out-of-scope boundaries
                elif section.section_id == "1.6":
                    if word_count < 20:
                        issues.append(f"Process Coverage / Scope is too brief ({word_count} words). Must define in-scope activities, covered locations/teams, and explicit exclusions.")
                    if not any(term in content_lower for term in ["exclude", "out-of-scope", "out of scope", "not cover", "boundary", "limitation", "inclusion", "in-scope"]):
                        issues.append("Process Coverage / Scope must explicitly specify operational boundaries (both what is INCLUDED and what is EXCLUDED).")

                # General text section minimum
                elif word_count < 15:
                    issues.append(f"Section content is too brief ({word_count} words). Please provide adequate operational detail as required by organizational standards.")

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

                # 1.7 Start Point
                elif section.section_id == "1.7":
                    for idx, row in enumerate(section.structured_data, 1):
                        act = str(row.get("Activity", "")).strip()
                        crit = str(row.get("Entry Criteria", "")).strip()
                        if not act:
                            issues.append(f"Row {idx}: Initiating Activity is missing.")
                        if not crit or len(crit.split()) < 4:
                            issues.append(f"Row {idx}: Entry Criteria is too brief or missing. Specify prerequisites before process starts.")

                # 1.8 End Point
                elif section.section_id == "1.8":
                    for idx, row in enumerate(section.structured_data, 1):
                        act = str(row.get("Activity", "")).strip()
                        crit = str(row.get("Exit Criteria", "")).strip()
                        if not act:
                            issues.append(f"Row {idx}: Concluding Activity is missing.")
                        if not crit or len(crit.split()) < 4:
                            issues.append(f"Row {idx}: Exit Criteria is too brief or missing. Specify deliverables/sign-offs required to complete.")

                # 1.12 Process Description
                elif section.section_id == "1.12":
                    for idx, row in enumerate(section.structured_data, 1):
                        act = str(row.get("Activity", "")).strip()
                        desc = str(row.get("Description", "")).strip()
                        if not act or act.lower() in ["none", "nan"]:
                            issues.append(f"Row {idx}: Activity title is missing.")
                        if not desc or desc.lower() in ["none", "nan"]:
                            issues.append(f"Row {idx}: Activity description is missing.")
                        else:
                            desc_words = len(desc.split())
                            if desc_words < 15:
                                issues.append(f"Row {idx} ('{act}'): Activity description is too brief ({desc_words} words). Sub-steps, tools, hand-offs, and verification checks must be clearly articulated.")

                # 1.13 RACI Matrix
                elif section.section_id == "1.13":
                    boolean_terms = {"yes", "no", "y", "n", "true", "false", "na", "n/a"}
                    for idx, row in enumerate(section.structured_data, 1):
                        act_name = str(row.get("Activity name", row.get("Activity", row.get("Roles", "")))).strip()
                        resp = str(row.get("Responsible", row.get("Responsible ( R )", row.get("Responsible (R)", "")))).strip()
                        acct = str(row.get("Accountable", row.get("Accountable ( A )", row.get("Accountable (A)", "")))).strip()

                        if not act_name or act_name.lower() in ["none", "nan"]:
                            issues.append(f"Row {idx}: Activity name is missing in RACI Matrix.")
                        
                        if resp.lower() in boolean_terms:
                            issues.append(f"Row {idx} ({act_name}): 'Responsible' specifies '{resp}'. Must specify a job title/designation (e.g. Manager, PH), not Yes/No.")
                        if acct.lower() in boolean_terms:
                            issues.append(f"Row {idx} ({act_name}): 'Accountable' specifies '{acct}'. Must specify a job title/designation (e.g. Manager, Vertical Lead), not Yes/No.")

                # 1.14 Business Rules
                elif section.section_id == "1.14":
                    for idx, row in enumerate(section.structured_data, 1):
                        rule_text = str(row.get("Business Rules", row.get("Business Rule", ""))).strip()
                        if not rule_text or rule_text.lower() in ["none", "nan"]:
                            issues.append(f"Row {idx}: Business Rule entry is empty.")
                        elif len(rule_text.split()) < 8:
                            issues.append(f"Row {idx}: Business Rule is too brief ('{rule_text}'). State the complete operational condition and enforcement boundary.")

                # 1.2 Document Change History
                elif section.section_id == "1.2":
                    for idx, row in enumerate(section.structured_data, 1):
                        desc = str(row.get("Description of Change", row.get("Description", ""))).strip()
                        if not desc:
                            issues.append(f"Row {idx}: Description of Change is missing.")
                        elif desc.lower() in ["minor issues updated", "updated", "test", "testing", "changed", "na", "none"]:
                            issues.append(f"Row {idx}: Description of Change is too generic ('{desc}'). Specify exactly what operational steps or policies were updated.")

                # 1.4 Related Documents
                elif section.section_id == "1.4":
                    placeholder_terms = ["testing doc", "test", "testing", "dummy", "na", "none", "nan", "doc"]
                    for idx, row in enumerate(section.structured_data, 1):
                        doc_name = str(row.get("Document Name", row.get("Name", ""))).strip()
                        if not doc_name:
                            issues.append(f"Row {idx}: Document Name is missing.")
                        elif doc_name.lower() in placeholder_terms:
                            issues.append(f"Row {idx}: Document Name contains placeholder data ('{doc_name}'). Specify an actual policy, SOP, or statutory standard.")

                # 1.5 Process Performance Parameters / KPIs
                elif section.section_id == "1.5":
                    for idx, row in enumerate(section.structured_data, 1):
                        kpi_name = str(row.get("Parameters / KPIs", row.get("KPI", ""))).strip()
                        kpi_desc = str(row.get("Description", "")).strip()
                        if not kpi_name:
                            issues.append(f"Row {idx}: Parameter / KPI name is missing.")
                        if not kpi_desc or kpi_desc.lower() in ["na", "none", "nan"]:
                            issues.append(f"Row {idx} ('{kpi_name}'): KPI Description is missing. Define the measurement formula and operational target.")

                # 1.21 Innovations
                elif section.section_id == "1.21":
                    for idx, row in enumerate(section.structured_data, 1):
                        imp = str(row.get("Innovations Implemented", "")).strip().lower()
                        plan = str(row.get("Envisaged/Planned", row.get("Envisaged / Planned", ""))).strip().lower()
                        na_terms = ["na", "n/a", "none", "nil", "not applicable", ""]
                        if imp in na_terms and plan in na_terms:
                            issues.append(f"Row {idx}: Innovations cannot be plain 'NA'. If no innovation is currently deployed, document baseline status and future tech roadmap (e.g., 'Baseline SOP; automated MIS alerts planned for FY27').")

        return issues
