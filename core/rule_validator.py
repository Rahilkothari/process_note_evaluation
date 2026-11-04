import re
from typing import Dict, Any, List
from models.schemas import ProcessSectionSchema

PRIMARY_MANDATORY_FIELDS = {
    "1.1": ["Name", "Stakeholder Name", "Employee Name"],
    "1.2": ["Amendment", "Description of Change", "Description"],
    "1.3": ["Name", "Process Owner", "Owner"],
    "1.4": ["Document Name", "Process / Policy ID", "Name"],
    "1.5": ["Description", "Parameters / KPIs", "KPI"],
    "1.7": ["Activity"],
    "1.8": ["Activity"],
    "1.12": ["Activity"],
    "1.13": ["Activity name", "Activity", "Roles"],
    "1.14": ["Business Rules", "Business Rule"],
    "1.15": ["Area of Exception", "Exception Description"],
    "1.16": ["Risk Description", "Control Description", "Mitigation Control", "Control"],
    "1.17": ["Compliance particulars", "Compliance Particulars", "Compliance", "Description / Requirement"],
    "1.18": ["Document Title", "Document / Record Name", "Document Name", "Record Name"],
    "1.19": ["Abbreviation", "Definition", "Context / Definition", "Full Form"],
    "1.20": ["Best Practices Followed (suggested list)", "Best Practices Followed", "Envisaged/Planned"],
    "1.21": ["Innovations Implemented", "Envisaged/Planned"],
    "1.22": ["Key Process Step", "Input", "Output"]
}

def get_field_val(row: Dict[str, Any], candidates: List[str]) -> str:
    """Retrieve field value case-insensitively and through alias names."""
    if not isinstance(row, dict):
        return ""
    # 1. Exact key match
    for c in candidates:
        if c in row and row[c] is not None:
            v = str(row[c]).strip()
            if v and v.lower() not in ["none", "nan", "null"]:
                return v
    # 2. Case-insensitive / normalized key match
    normalized_row = {re.sub(r'[^a-z0-9]', '', str(k).lower()): v for k, v in row.items()}
    for c in candidates:
        c_norm = re.sub(r'[^a-z0-9]', '', c.lower())
        if c_norm in normalized_row and normalized_row[c_norm] is not None:
            v = str(normalized_row[c_norm]).strip()
            if v and v.lower() not in ["none", "nan", "null"]:
                return v
    # 3. Substring key matching (e.g. key contains 'document' or 'retention' or 'control')
    for c in candidates:
        c_norm = re.sub(r'[^a-z0-9]', '', c.lower())
        if len(c_norm) >= 4:
            for k_norm, v in normalized_row.items():
                if (c_norm in k_norm or k_norm in c_norm) and v is not None:
                    v_str = str(v).strip()
                    if v_str and v_str.lower() not in ["none", "nan", "null"]:
                        return v_str
    return ""

def is_row_meaningfully_filled(sec_id: str, row: Dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    for k, val in row.items():
        if k in ["Reviewer Comment", "Sr. No."]:
            continue
        if val is not None and str(val).strip() != "" and str(val).strip().lower() not in ["none", "nan", "null"]:
            return True
    return False

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
            raw_rows = section.structured_data or []
            valid_rows = [r for r in raw_rows if is_row_meaningfully_filled(section.section_id, r)]

            if not valid_rows:
                issues.append("Table is empty or contains no valid operational records. Required fields cannot be blank.")
                return issues

            # 1.1 Approval matrix
            if section.section_id == "1.1":
                for idx, r in enumerate(valid_rows, 1):
                    r_name = get_field_val(r, ["Name", "Stakeholder Name", "Employee Name", "Process Owner"])
                    r_role = get_field_val(r, ["Role", "Designation", "Stakeholder Role"])
                    if not r_name:
                        issues.append(f"Row {idx}: Stakeholder Name cannot be blank.")
                    if not r_role:
                        issues.append(f"Row {idx}: Stakeholder Role must be selected.")

                # Check Segregation of Duties if both Process Owner and Process Approver exist
                owner_names = [str(r.get("Name", "")).strip().lower() for r in valid_rows if "owner" in str(r.get("Role", "")).lower() and str(r.get("Name", "")).strip()]
                approver_names = [str(r.get("Name", "")).strip().lower() for r in valid_rows if "approver" in str(r.get("Role", "")).lower() and str(r.get("Name", "")).strip()]
                for ow in owner_names:
                    if ow in approver_names:
                        issues.append(f"Governance Conflict: Process Owner '{ow.title()}' cannot also be the Process Approver (self-approval).")
                        break

            # 1.3 Document Review Cycle
            elif section.section_id == "1.3":
                for idx, row in enumerate(valid_rows, 1):
                    owner = get_field_val(row, ["Process Owner", "Owner", "Name", "Stakeholder Name"])
                    eff_d = get_field_val(row, ["Effective Date", "Date", "Review Date"])
                    if not owner:
                        issues.append(f"Row {idx}: Process Owner / Stakeholder Name cannot be blank.")
                    if not eff_d:
                        issues.append(f"Row {idx}: Effective Date is required.")

            # 1.7 Start Point
            elif section.section_id == "1.7":
                for idx, row in enumerate(valid_rows, 1):
                    act = get_field_val(row, ["Activity", "Activity Name", "Process Step", "Initiating Activity"])
                    crit = get_field_val(row, ["Entry Criteria", "Prerequisites", "Criteria"])
                    if not act:
                        issues.append(f"Row {idx}: Initiating Activity is missing.")
                    if not crit or len(crit.split()) < 4:
                        issues.append(f"Row {idx}: Entry Criteria is too brief or missing. Specify prerequisites before process starts.")

            # 1.8 End Point
            elif section.section_id == "1.8":
                for idx, row in enumerate(valid_rows, 1):
                    act = get_field_val(row, ["Activity", "Activity Name", "Process Step", "Concluding Activity"])
                    crit = get_field_val(row, ["Exit Criteria", "Deliverables", "Criteria"])
                    if not act:
                        issues.append(f"Row {idx}: Concluding Activity is missing.")
                    if not crit or len(crit.split()) < 4:
                        issues.append(f"Row {idx}: Exit Criteria is too brief or missing. Specify deliverables/sign-offs required to complete.")

            # 1.12 Process Description
            elif section.section_id == "1.12":
                for idx, row in enumerate(valid_rows, 1):
                    act = get_field_val(row, ["Activity", "Activity title", "Step", "Step Name", "Process Step"])
                    desc = get_field_val(row, ["Description", "Process Description", "Detailed Description", "Sub-steps"])
                    if not act:
                        issues.append(f"Row {idx}: Activity title is missing.")
                    if not desc:
                        issues.append(f"Row {idx}: Activity description is missing.")
                    else:
                        desc_words = len(desc.split())
                        if desc_words < 15:
                            issues.append(f"Row {idx} ('{act}'): Activity description is too brief ({desc_words} words). Sub-steps, tools, hand-offs, and verification checks must be clearly articulated.")

            # 1.13 RACI Matrix
            elif section.section_id == "1.13":
                boolean_terms = {"yes", "no", "y", "n", "true", "false", "na", "n/a"}
                for idx, row in enumerate(valid_rows, 1):
                    act_name = get_field_val(row, ["Activity name", "Activity", "Roles", "Step"])
                    resp = get_field_val(row, ["Responsible", "Responsible ( R )", "Responsible (R)", "R"])
                    acct = get_field_val(row, ["Accountable", "Accountable ( A )", "Accountable (A)", "A"])

                    if not act_name:
                        issues.append(f"Row {idx}: Activity name is missing in RACI Matrix.")
                    
                    if resp.lower() in boolean_terms:
                        issues.append(f"Row {idx} ({act_name}): 'Responsible' specifies '{resp}'. Must specify a job title/designation (e.g. Manager, PH), not Yes/No.")
                    if acct.lower() in boolean_terms:
                        issues.append(f"Row {idx} ({act_name}): 'Accountable' specifies '{acct}'. Must specify a job title/designation (e.g. Manager, Vertical Lead), not Yes/No.")

            # 1.14 Business Rules
            elif section.section_id == "1.14":
                for idx, row in enumerate(valid_rows, 1):
                    rule_text = get_field_val(row, ["Business Rules", "Business Rule", "Rule", "Rule Description"])
                    if not rule_text:
                        issues.append(f"Row {idx}: Business Rule entry is empty.")
                    elif len(rule_text.split()) < 8:
                        issues.append(f"Row {idx}: Business Rule is too brief ('{rule_text}'). State the complete operational condition and enforcement boundary.")

            # 1.15 Exception & Deviation Management
            elif section.section_id == "1.15":
                for idx, row in enumerate(valid_rows, 1):
                    area = get_field_val(row, ["Area of Exception", "Exception Area", "Area", "Process Area"])
                    desc = get_field_val(row, ["Exception Description", "Description", "Exception", "Deviation Description", "Exception Mitigation"])
                    if not area:
                        issues.append(f"Row {idx}: Area of Exception is missing.")
                    if not desc:
                        issues.append(f"Row {idx}: Exception Description is missing.")

            # 1.16 Risk Management
            elif section.section_id == "1.16":
                for idx, row in enumerate(valid_rows, 1):
                    risk_desc = get_field_val(row, ["Risk Description", "Risk", "Identified Risk", "Description"])
                    control = get_field_val(row, ["Control Description", "Mitigation Control", "Control", "Mitigation", "Preventive / Detective Control", "Control / Mitigation"])
                    if not risk_desc:
                        issues.append(f"Row {idx}: Risk Description is missing.")
                    if not control:
                        issues.append(f"Row {idx}: Control Description is missing.")

            # 1.17 Compliance Management
            elif section.section_id == "1.17":
                for idx, row in enumerate(valid_rows, 1):
                    comp = get_field_val(row, ["Compliance particulars", "Compliance Particulars", "Compliance", "Description / Requirement", "Statutory Requirements", "Particulars"])
                    if not comp:
                        issues.append(f"Row {idx}: Compliance particulars / statutory requirements cannot be blank.")

            # 1.18 Data Archival
            elif section.section_id == "1.18":
                for idx, row in enumerate(valid_rows, 1):
                    doc_title = get_field_val(row, ["Document Title", "Document / Record Name", "Document Name", "Record Name", "Document", "Title"])
                    ret = get_field_val(row, ["Retention period", "Retention Period", "Retention", "Retention Period (Years)", "Retention Timeline"])
                    if not doc_title:
                        issues.append(f"Row {idx}: Document Title is missing in Data Archival.")
                    if not ret:
                        issues.append(f"Row {idx}: Retention period is missing.")

            # 1.19 Abbreviations & Acronyms
            elif section.section_id == "1.19":
                for idx, row in enumerate(valid_rows, 1):
                    abbr = get_field_val(row, ["Abbreviation", "Acronym", "Term", "Abbreviation / Acronym"])
                    defn = get_field_val(row, ["Definition", "Context / Definition", "Full Form", "Meaning", "Description"])
                    if not abbr:
                        issues.append(f"Row {idx}: Abbreviation acronym is missing.")
                    if not defn:
                        issues.append(f"Row {idx}: Abbreviation Definition is missing.")

            # 1.20 Best Practices Summary
            elif section.section_id == "1.20":
                for idx, row in enumerate(valid_rows, 1):
                    bp = get_field_val(row, ["Best Practices Followed (suggested list)", "Best Practices Followed", "Best Practice", "Best Practices", "Envisaged/Planned", "Description"])
                    if not bp:
                        issues.append(f"Row {idx}: Best Practice description cannot be blank.")

            # 1.22 SIPOC
            elif section.section_id == "1.22":
                for idx, row in enumerate(valid_rows, 1):
                    step = get_field_val(row, ["Key Process Step", "Process Step", "Step", "Activity"])
                    inp = get_field_val(row, ["Input", "Inputs", "Supplier (Dept)"])
                    out = get_field_val(row, ["Output", "Outputs", "Customer (dept)"])
                    if not step:
                        issues.append(f"Row {idx}: Key Process Step in SIPOC is missing.")
                    if not inp:
                        issues.append(f"Row {idx}: Input in SIPOC is missing.")
                    if not out:
                        issues.append(f"Row {idx}: Output in SIPOC is missing.")

            # 1.2 Document Change History
            elif section.section_id == "1.2":
                for idx, row in enumerate(valid_rows, 1):
                    desc = get_field_val(row, ["Amendment", "Description of Change", "Description"])
                    if not desc:
                        issues.append(f"Row {idx}: Description of Change / Amendment is missing.")
                    elif desc.lower() in ["minor issues updated", "updated", "test", "testing", "changed", "na", "none"]:
                        issues.append(f"Row {idx}: Description of Change is too generic ('{desc}'). Specify exactly what operational steps or policies were updated.")

            # 1.4 Related Documents
            elif section.section_id == "1.4":
                placeholder_terms = ["testing doc", "test", "testing", "dummy", "na", "none", "nan", "doc"]
                for idx, row in enumerate(valid_rows, 1):
                    doc_name = get_field_val(row, ["Document Name", "Process / Policy ID", "Name", "Document"])
                    if not doc_name:
                        issues.append(f"Row {idx}: Document Name is missing.")
                    elif doc_name.lower() in placeholder_terms:
                        issues.append(f"Row {idx}: Document Name contains placeholder data ('{doc_name}'). Specify an actual policy, SOP, or statutory standard.")

            # 1.5 Process Performance Parameters / KPIs
            elif section.section_id == "1.5":
                for idx, row in enumerate(valid_rows, 1):
                    kpi_desc = get_field_val(row, ["Description", "Parameters / KPIs", "KPI", "Parameter"])
                    if not kpi_desc or kpi_desc.lower() in ["na", "none", "nan"]:
                        issues.append(f"Row {idx}: KPI Description / Parameter is missing.")

            # 1.21 Innovations
            elif section.section_id == "1.21":
                for idx, row in enumerate(valid_rows, 1):
                    imp = get_field_val(row, ["Innovations Implemented", "Innovation", "Innovations"]).lower()
                    plan = get_field_val(row, ["Envisaged/Planned", "Envisaged / Planned", "Planned"]).lower()
                    na_terms = ["na", "n/a", "none", "nil", "not applicable", ""]
                    if imp in na_terms and plan in na_terms:
                        issues.append(f"Row {idx}: Innovations cannot be plain 'NA'. If no innovation is currently deployed, document baseline status and future tech roadmap (e.g., 'Baseline SOP; automated MIS alerts planned for FY27').")

        return issues
