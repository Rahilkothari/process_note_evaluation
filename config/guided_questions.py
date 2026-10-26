import datetime
from typing import Dict, Any, List

# Comprehensive Guided Questions & Interactive Assistant Specifications for all 22 Sections
# Allows creators to fill structured, intuitive fields (date pickers, dropdowns, text inputs)
# and automatically populate corporate-grade tables or text sections.

def compute_next_review_date(eff_date: datetime.date, freq_str: str) -> datetime.date:
    """Calculates the scheduled next review date based on effective date and review frequency."""
    if not isinstance(eff_date, datetime.date):
        eff_date = datetime.date.today()
    freq_lower = freq_str.lower() if freq_str else ""
    try:
        if "semi-annual" in freq_lower or "6 months" in freq_lower or "half" in freq_lower:
            month = eff_date.month + 6
            year = eff_date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(eff_date.day, 28)
            return datetime.date(year, month, day)
        elif "quarter" in freq_lower or "3 months" in freq_lower:
            month = eff_date.month + 3
            year = eff_date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(eff_date.day, 28)
            return datetime.date(year, month, day)
        elif "monthly" in freq_lower or "1 month" in freq_lower:
            month = eff_date.month + 1
            year = eff_date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(eff_date.day, 28)
            return datetime.date(year, month, day)
        elif "biennial" in freq_lower or "2 years" in freq_lower:
            return datetime.date(eff_date.year + 2, eff_date.month, min(eff_date.day, 28))
        else:
            # Default Annual (12 months)
            return datetime.date(eff_date.year + 1, eff_date.month, min(eff_date.day, 28))
    except Exception:
        return eff_date + datetime.timedelta(days=365)


SECTION_GUIDED_SPECS: Dict[str, Dict[str, Any]] = {
    "1.1": {
        "title": "Approval Matrix Guided Assistant",
        "intro": "Specify the key individuals responsible for reviewing and approving this process note:",
        "type": "table",
        "fields": [
            {
                "id": "owner",
                "label": "Process Owner (Name | Function | Sign):",
                "type": "text",
                "placeholder": "e.g., John Doe | PedTech Operations | JD",
                "help": "Designation/Name, Functional Department, and Initials."
            },
            {
                "id": "reviewer",
                "label": "Process Reviewer (Name | Function | Sign):",
                "type": "text",
                "placeholder": "e.g., Jane Smith | Quality & Excellence | JS",
                "help": "Reviewer responsible for checking quality and accuracy."
            },
            {
                "id": "approver",
                "label": "Process Approver (Name | Function | Sign):",
                "type": "text",
                "placeholder": "e.g., Robert Brown | Director, Operations | RB",
                "help": "Leadership authority providing final sign-off."
            },
            {
                "id": "sign_date",
                "label": "Approval / Sign Date:",
                "type": "date",
                "help": "Date of final review and approval."
            }
        ]
    },
    "1.2": {
        "title": "Document Change History Guided Assistant",
        "intro": "Track the version number, effective date, and scope of changes:",
        "type": "table",
        "fields": [
            {
                "id": "version",
                "label": "Version Number:",
                "type": "select",
                "options": ["1.0 (Initial Draft)", "1.1 (Minor Revision)", "1.2 (Periodic Review)", "2.0 (Major Overhaul)"],
                "default": "1.0 (Initial Draft)"
            },
            {
                "id": "eff_date",
                "label": "Effective Date (when changes take effect):",
                "type": "date"
            },
            {
                "id": "change_date",
                "label": "Change Date:",
                "type": "date"
            },
            {
                "id": "amendment",
                "label": "Summary of Changes / Amendment:",
                "type": "textarea",
                "placeholder": "e.g., Initial baseline version created for standardizing partner school onboarding."
            },
            {
                "id": "req_by",
                "label": "Change Requested By:",
                "type": "text",
                "placeholder": "e.g., Program Director / Business Excellence"
            },
            {
                "id": "made_by",
                "label": "Change Made By:",
                "type": "text",
                "placeholder": "e.g., Program Head (Creator)"
            }
        ]
    },
    "1.3": {
        "title": "Document Review Cycle Guided Assistant",
        "intro": "Set the governance policy for when and how frequently this process note must be audited:",
        "type": "table",
        "fields": [
            {
                "id": "eff_date",
                "label": "1. Effective Date (When this process goes live):",
                "type": "date",
                "help": "The date from which this version of the process becomes binding."
            },
            {
                "id": "review_frequency",
                "label": "2. How often must this document be reviewed?",
                "type": "select",
                "options": [
                    "Annual (Every 12 months)",
                    "Semi-Annual (Every 6 months)",
                    "Quarterly (Every 3 months)",
                    "Monthly",
                    "Biennial (Every 2 years)",
                    "Event-triggered / As needed"
                ],
                "default": "Annual (Every 12 months)",
                "help": "Corporate standard is Annual or Semi-Annual."
            },
            {
                "id": "next_review_date",
                "label": "3. Scheduled Next Review Date:",
                "type": "calculated_date",
                "help": "Auto-calculated based on effective date and cycle. You can adjust if needed."
            },
            {
                "id": "process_owner",
                "label": "4. Designated Process Owner (Role / Designation):",
                "type": "text",
                "placeholder": "e.g., Program Head (or Operations Manager)",
                "help": "Job title or designation responsible for the review."
            },
            {
                "id": "owner_name",
                "label": "5. Process Owner Name:",
                "type": "text",
                "placeholder": "e.g., John Doe",
                "help": "Full name of the designated review owner."
            },
            {
                "id": "owner_sign",
                "label": "6. Signature Code / Initials:",
                "type": "text",
                "placeholder": "e.g., JD or PH",
                "help": "Short signature abbreviation."
            }
        ]
    },
    "1.4": {
        "title": "Related Documents Guided Assistant",
        "intro": "Link connected organizational policies, SOPs, and standard templates:",
        "type": "table",
        "fields": [
            {
                "id": "policy_id",
                "label": "1. Policy or SOP Document ID:",
                "type": "text",
                "placeholder": "e.g., SOP-OPS-012"
            },
            {
                "id": "doc_name",
                "label": "2. Official Document Name:",
                "type": "text",
                "placeholder": "e.g., Partner School Onboarding Policy & Guidelines"
            },
            {
                "id": "template_name",
                "label": "3. Associated Assessment Forms / Templates (Optional):",
                "type": "text",
                "placeholder": "e.g., FORM-04 Due Diligence Assessment Scorecard"
            }
        ]
    },
    "1.5": {
        "title": "Process Performance Parameters / KPIs Guided Assistant",
        "intro": "Define measurable SMART KPIs to track operational performance and governance:",
        "type": "table",
        "fields": [
            {
                "id": "kpi_desc",
                "label": "1. Measurable KPI Metric & Description:",
                "type": "text",
                "placeholder": "e.g., School Onboarding Turnaround Time (TAT) from application to MOU"
            },
            {
                "id": "target",
                "label": "2. Target Benchmark:",
                "type": "text",
                "placeholder": "e.g., <= 5 Business Days (Adherence >= 98%)"
            },
            {
                "id": "owner",
                "label": "3. KPI Owner (Role):",
                "type": "select",
                "options": [
                    "Program Head (PH)",
                    "Operations Manager",
                    "Project Manager",
                    "Vertical Lead",
                    "Quality & Excellence Lead",
                    "Program Director",
                    "Other (Specify custom role...)"
                ],
                "default": "Program Head (PH)",
                "help": "Select standard organizational role responsible for KPI achievement."
            },
            {
                "id": "maker",
                "label": "4. Maker (Who records / inputs performance data):",
                "type": "select",
                "options": [
                    "Field Officer",
                    "Field Executive",
                    "Operations Executive",
                    "Program Associate",
                    "Project Executive",
                    "Trainer / Facilitator",
                    "Program Head (PH)",
                    "Other (Specify custom role...)"
                ],
                "default": "Field Officer",
                "help": "Select designation of person entering/measuring performance data."
            },
            {
                "id": "checker",
                "label": "5. Checker (Who audits / verifies performance data):",
                "type": "select",
                "options": [
                    "Operations Manager",
                    "Program Head (PH)",
                    "Vertical Lead",
                    "Quality & Business Excellence Lead",
                    "Project Manager",
                    "Program Director",
                    "Other (Specify custom role...)"
                ],
                "default": "Operations Manager",
                "help": "Select designation of person verifying and validating KPI accuracy."
            },
            {
                "id": "report_freq",
                "label": "6. Report Generation Frequency:",
                "type": "select",
                "options": ["Monthly", "Weekly", "Daily", "Quarterly"],
                "default": "Monthly"
            },
            {
                "id": "review_freq",
                "label": "7. Leadership Review Frequency:",
                "type": "select",
                "options": ["Monthly", "Quarterly", "Semi-Annually", "Annually"],
                "default": "Monthly"
            },
            {
                "id": "data_source",
                "label": "8. Data Source & Report Name:",
                "type": "text",
                "placeholder": "e.g., MIS Onboarding Portal Dashboard"
            }
        ]
    },
    "1.6": {
        "title": "Process Coverage / Scope Guided Assistant",
        "intro": "Clearly delineate operational boundaries, covered regions, and exclusions:",
        "type": "text",
        "fields": [
            {
                "id": "in_scope",
                "label": "1. In-Scope Activities (What is explicitly INCLUDED?):",
                "type": "textarea",
                "placeholder": "e.g., Identification, feasibility study, due diligence, MOU signing, and orientation for partner schools across Maharashtra."
            },
            {
                "id": "out_of_scope",
                "label": "2. Out-of-Scope / Exclusions (What is explicitly EXCLUDED?):",
                "type": "textarea",
                "placeholder": "e.g., Teacher payroll, infrastructure capital grants, and curriculum design (handled under separate SOPs)."
            },
            {
                "id": "stakeholders",
                "label": "3. Covered Teams / Beneficiaries:",
                "type": "text",
                "placeholder": "e.g., Urban and rural government-aided schools, Field Operations Team, Program Leads."
            }
        ]
    },
    "1.7": {
        "title": "Start Point Guided Assistant",
        "intro": "Specify the precise operational trigger and entry criteria that initiate this process:",
        "type": "table",
        "fields": [
            {
                "id": "activity",
                "label": "1. Initiating Event / Incoming Request:",
                "type": "text",
                "placeholder": "e.g., Receipt of approved Annual School Expansion Plan from Program Director"
            },
            {
                "id": "entry_criteria",
                "label": "2. Mandatory Entry Criteria & Prerequisites:",
                "type": "textarea",
                "placeholder": "e.g., Signed budget allocation, verified target school list, and Field Officer assignment.",
                "help": "Must be descriptive (at least 4 words). Specify prerequisites or authorizations before process starts."
            }
        ]
    },
    "1.8": {
        "title": "End Point Guided Assistant",
        "intro": "Specify the final deliverable and exit criteria that mark process completion:",
        "type": "table",
        "fields": [
            {
                "id": "activity",
                "label": "1. Concluding Activity / Deliverable:",
                "type": "text",
                "placeholder": "e.g., Final signed MOU uploaded to ERP and welcome orientation kit delivered",
                "help": "Specify the concluding operational milestone or final output."
            },
            {
                "id": "exit_criteria",
                "label": "2. Mandatory Exit Criteria & Sign-off:",
                "type": "textarea",
                "placeholder": "e.g., Verification of onboarding checklist in MIS by Program Head, confirmation email sent.",
                "help": "Must be descriptive (at least 4 words). Specify deliverables, sign-offs, or stakeholder acknowledgments required to complete."
            }
        ]
    },
    "1.9": {
        "title": "Introduction Guided Assistant",
        "intro": "Provide the background context and organizational rationale for this process:",
        "type": "text",
        "fields": [
            {
                "id": "background",
                "label": "1. Organizational Background & Context:",
                "type": "textarea",
                "placeholder": "e.g., Kotak Education Foundation partners with municipal and rural schools to enhance foundational learning. This process establishes standard operating protocols."
            },
            {
                "id": "importance",
                "label": "2. Strategic Importance / Rationale:",
                "type": "textarea",
                "placeholder": "e.g., Standardizing ensures uniform partner quality, transparent accountability, regulatory compliance, and seamless stakeholder hand-offs."
            }
        ]
    },
    "1.10": {
        "title": "Objective Guided Assistant",
        "intro": "State the primary business purpose and tangible outcomes of this process:",
        "type": "text",
        "fields": [
            {
                "id": "primary_obj",
                "label": "1. Primary Business Objective:",
                "type": "textarea",
                "placeholder": "e.g., To establish an error-free, timely, and compliant onboarding mechanism for 200+ partner schools within a standard 10-day TAT."
            },
            {
                "id": "measurable_outcome",
                "label": "2. Key Measurable Outcome / Target:",
                "type": "text",
                "placeholder": "e.g., 100% compliant documentation, zero audit findings, and prompt stakeholder communication."
            }
        ]
    },
    "1.11": {
        "title": "Process Flowchart Guided Assistant",
        "intro": "Map sequential steps, decision branches, and hand-offs to auto-generate a Mermaid flowchart:",
        "type": "flowchart",
        "fields": [
            {
                "id": "steps",
                "label": "1. Step-by-Step Flow (Start to End):",
                "type": "textarea",
                "placeholder": "Step 1: Field Lead submits application\nStep 2: Manager conducts initial screening\nStep 3: Verification Lead performs due diligence\nStep 4: Director reviews & signs MOU"
            },
            {
                "id": "decisions",
                "label": "2. Key Decision Points (If Approved / If Rejected):",
                "type": "textarea",
                "placeholder": "Decision at Step 2: If criteria met -> Proceed to Step 3; If rejected -> Return with remarks.\nDecision at Step 4: If budget approved -> Sign MOU; If rejected -> Escalate."
            },
            {
                "id": "roles",
                "label": "3. Hand-off Stakeholders Involved:",
                "type": "text",
                "placeholder": "Field Officer, Manager, Quality Lead, Program Director"
            }
        ]
    },
    "1.12": {
        "title": "Process Description Guided Assistant (BE 6 Enterprise Dimensions)",
        "intro": "Provide detailed operational mechanics covering all 6 mandatory enterprise dimensions:",
        "type": "table",
        "fields": [
            {
                "id": "activity_name",
                "label": "Activity Name:",
                "type": "text",
                "placeholder": "e.g., School Selection and Due Diligence"
            },
            {
                "id": "inputs",
                "label": "1. Inputs & Data Sources (What records/documents are needed to start?):",
                "type": "text",
                "placeholder": "e.g., District school registry, principal application form, budget allocation sheet"
            },
            {
                "id": "sub_steps",
                "label": "2. Step-by-Step Sub-activities (Break down into numbered sub-steps):",
                "type": "textarea",
                "placeholder": "1. Filter applications in Excel based on eligibility criteria.\n2. Field Officer conducts physical on-ground infrastructure audit.\n3. Verify teacher-student ratio and basic sanitation facilities."
            },
            {
                "id": "tools",
                "label": "3. Tools, Systems & Applications (ERP, portals, Excel, field apps):",
                "type": "text",
                "placeholder": "e.g., KEF Field Mobile App, Google Sheets, State Education Portal"
            },
            {
                "id": "handoffs",
                "label": "4. Stakeholders & Hand-offs (Who performs work and to whom is it handed?):",
                "type": "text",
                "placeholder": "e.g., Field Officer executes inspection, hands dossier to Operations Manager"
            },
            {
                "id": "deliverables",
                "label": "5. Expected Deliverables / Outputs (Tangible output produced):",
                "type": "text",
                "placeholder": "e.g., Completed Due Diligence Scorecard & Recommendation Report"
            },
            {
                "id": "validations",
                "label": "6. Checks, Validations & Approvals (Who verifies and against what criteria?):",
                "type": "text",
                "placeholder": "e.g., Manager verifies scorecard; minimum 80% score required for qualification sign-off"
            },
            {
                "id": "owner_role",
                "label": "Owner / Role executing this activity:",
                "type": "select",
                "options": [
                    "Field Officer & Program Head",
                    "Field Officer",
                    "Program Head (PH)",
                    "Operations Manager",
                    "Vertical Lead",
                    "Quality & Excellence Lead",
                    "Trainer / Facilitator",
                    "Other (Specify custom role...)"
                ],
                "default": "Field Officer & Program Head",
                "help": "Select standard organizational role responsible for executing this activity."
            },
            {
                "id": "tat",
                "label": "Timeline / TAT:",
                "type": "text",
                "placeholder": "e.g., 5 Business Days"
            }
        ]
    },
    "1.13": {
        "title": "RACI Matrix Guided Assistant (Standard 8-Column Format)",
        "intro": "Map roles and responsibilities. Ensure exact designations are specified without Yes/No values:",
        "type": "table",
        "fields": [
            {
                "id": "activity_name",
                "label": "Activity Name (matching Section 1.12):",
                "type": "text",
                "placeholder": "e.g., Plan of the Onboarding of the schools"
            },
            {
                "id": "activity_desc",
                "label": "Activity Description / Key Steps:",
                "type": "textarea",
                "placeholder": "1. Geographical location selection.\n2. Liaison with government authority.\n3. Filter analysis of potential schools."
            },
            {
                "id": "timeline",
                "label": "Timeline / TAT:",
                "type": "text",
                "placeholder": "e.g., Given timeline (5 days)"
            },
            {
                "id": "responsible",
                "label": "Responsible (Executes activity - specific designation):",
                "type": "select",
                "options": [
                    "PH",
                    "Field Officer",
                    "Operations Manager",
                    "Vertical Lead",
                    "Project Manager",
                    "Trainer",
                    "Finance Lead",
                    "HR Lead",
                    "Other (Specify custom role...)"
                ],
                "default": "PH",
                "help": "Specific job designation executing the work. Do NOT enter Yes/No."
            },
            {
                "id": "accountable",
                "label": "Accountable (Single final sign-off owner):",
                "type": "select",
                "options": [
                    "Manager",
                    "PH",
                    "Vertical Lead",
                    "Director",
                    "Quality Lead",
                    "Other (Specify custom role...)"
                ],
                "default": "Manager",
                "help": "Single designation owning final sign-off. Do NOT enter Yes/No."
            },
            {
                "id": "consulted",
                "label": "Consulted by (Advising stakeholders):",
                "type": "select",
                "options": [
                    "Director",
                    "Quality Lead",
                    "Vertical Lead",
                    "Legal & Compliance",
                    "Finance Lead",
                    "Other (Specify custom role...)"
                ],
                "default": "Director",
                "help": "Designation providing advice/inputs."
            },
            {
                "id": "informed",
                "label": "Informed to (Teams kept updated):",
                "type": "select",
                "options": [
                    "CEO Project teams",
                    "SCD internal teams",
                    "Operations Team",
                    "Program Director",
                    "Finance Team",
                    "Other (Specify custom role...)"
                ],
                "default": "CEO Project teams",
                "help": "Teams or roles kept updated on progress."
            }
        ]
    },
    "1.14": {
        "title": "Business Rules Guided Assistant",
        "intro": "Formulate strict operational boundaries that must be backed by enforcement in Section 1.12:",
        "type": "table",
        "fields": [
            {
                "id": "rule_statement",
                "label": "1. Mandatory Rule Statement (Policy / Operational boundary):",
                "type": "textarea",
                "placeholder": "e.g., All translated scripts must pass a peer grammar check before recording."
            },
            {
                "id": "enforcement",
                "label": "2. Operational Enforcement (Who verifies, when, and using what tool in 1.12?):",
                "type": "textarea",
                "placeholder": "e.g., Quality Lead verifies against standard translation rubric before releasing to studio."
            }
        ]
    },
    "1.15": {
        "title": "Exception & Change Management Guided Assistant",
        "intro": "Document potential operational deviations, mitigation controls, and approval authorities:",
        "type": "table",
        "fields": [
            {
                "id": "area",
                "label": "1. Area of Exception:",
                "type": "text",
                "placeholder": "e.g., School Eligibility Criteria"
            },
            {
                "id": "desc",
                "label": "2. Exception Description / Deviation:",
                "type": "textarea",
                "placeholder": "e.g., Target school has fewer students than the minimum enrollment threshold."
            },
            {
                "id": "mitigation",
                "label": "3. Exception Mitigation & Compensatory Controls:",
                "type": "textarea",
                "placeholder": "e.g., Cluster onboarding with adjacent rural school to meet collective threshold."
            },
            {
                "id": "prop_by",
                "label": "4. Proposed By:",
                "type": "select",
                "options": [
                    "Field Officer",
                    "Operations Executive",
                    "Program Head (PH)",
                    "Operations Manager",
                    "Other (Specify custom role...)"
                ],
                "default": "Field Officer"
            },
            {
                "id": "recom_by",
                "label": "5. Recommended By:",
                "type": "select",
                "options": [
                    "Program Head (PH)",
                    "Operations Manager",
                    "Vertical Lead",
                    "Other (Specify custom role...)"
                ],
                "default": "Program Head (PH)"
            },
            {
                "id": "approved_by",
                "label": "6. Approved By (Sign-off Authority):",
                "type": "select",
                "options": [
                    "Program Director",
                    "Vertical Lead",
                    "CEO / Leadership",
                    "Other (Specify custom role...)"
                ],
                "default": "Program Director"
            },
            {
                "id": "informed_to",
                "label": "7. Informed To:",
                "type": "select",
                "options": [
                    "Vertical Lead, Finance Team",
                    "CEO Project teams",
                    "Operations Team",
                    "Program Director",
                    "Other (Specify custom role...)"
                ],
                "default": "Vertical Lead, Finance Team"
            }
        ]
    },
    "1.16": {
        "title": "Risk Management Guided Assistant",
        "intro": "Identify operational and compliance risks along with root causes and preventive controls:",
        "type": "table",
        "fields": [
            {
                "id": "sub_process",
                "label": "1. Sub Process & Activity:",
                "type": "text",
                "placeholder": "e.g., School Due Diligence & Data Verification"
            },
            {
                "id": "desc",
                "label": "2. Risk Description:",
                "type": "text",
                "placeholder": "e.g., Inaccurate school student enrollment figures"
            },
            {
                "id": "root_cause",
                "label": "3. Root Cause:",
                "type": "text",
                "placeholder": "e.g., Manual record keeping by partner school without secondary verification"
            },
            {
                "id": "risk_type",
                "label": "4. Type of Risk:",
                "type": "select",
                "options": ["Operational", "Compliance", "Financial", "Reputational"],
                "default": "Operational"
            },
            {
                "id": "level_of_risk",
                "label": "5. Level of Risk:",
                "type": "select",
                "options": ["High", "Medium", "Low"],
                "default": "Medium"
            },
            {
                "id": "impact",
                "label": "6. Risk Impact:",
                "type": "text",
                "placeholder": "e.g., Misallocation of learning materials and budget"
            },
            {
                "id": "control",
                "label": "7. Preventive Control Description:",
                "type": "textarea",
                "placeholder": "e.g., Mandatory physical cross-verification against government attendance registers"
            },
            {
                "id": "freq",
                "label": "8. Control Frequency:",
                "type": "select",
                "options": ["Every Transaction", "Daily", "Weekly", "Monthly", "Quarterly", "Annual"],
                "default": "Every Transaction"
            }
        ]
    },
    "1.17": {
        "title": "Compliance Management Guided Assistant",
        "intro": "List statutory, child safety (POCSO), and institutional compliance obligations:",
        "type": "table",
        "fields": [
            {
                "id": "sub_process",
                "label": "1. Sub Process / Compliance Area:",
                "type": "text",
                "placeholder": "e.g., Child Safety & Personnel Background Checks"
            },
            {
                "id": "compliance",
                "label": "2. Compliance Particulars & Policy Norms:",
                "type": "textarea",
                "placeholder": "e.g., Mandatory POCSO guidelines compliance and police verification for all field trainers."
            },
            {
                "id": "target_date",
                "label": "3. Target Date / Schedule:",
                "type": "text",
                "placeholder": "e.g., Annual verification completed by April 30"
            }
        ]
    },
    "1.18": {
        "title": "Data Archival Guided Assistant",
        "intro": "Define record retention, archival formats, and repository locations:",
        "type": "table",
        "fields": [
            {
                "id": "doc_title",
                "label": "1. Document / Record Title:",
                "type": "text",
                "placeholder": "e.g., Signed Partner School MOUs & Due Diligence Dossiers"
            },
            {
                "id": "fy",
                "label": "2. Financial Year:",
                "type": "text",
                "placeholder": "e.g., FY 2025-26"
            },
            {
                "id": "criticality",
                "label": "3. Criticality:",
                "type": "select",
                "options": ["High", "Medium", "Low"],
                "default": "High"
            },
            {
                "id": "storage_type",
                "label": "4. Storage Type:",
                "type": "select",
                "options": ["Both Soft & Hard copy", "Soft copy", "Hard copy"],
                "default": "Both Soft & Hard copy"
            },
            {
                "id": "retention",
                "label": "5. Retention Period:",
                "type": "select",
                "options": ["7 Years", "5 Years", "3 Years", "10 Years", "Permanent"],
                "default": "7 Years"
            },
            {
                "id": "soft_link",
                "label": "6. Soft Copy Folder Link / System Location:",
                "type": "text",
                "placeholder": "e.g., SharePoint/KEF_MOU_Archive"
            },
            {
                "id": "hard_loc",
                "label": "7. Hard Copy Location:",
                "type": "text",
                "placeholder": "e.g., Central Operations Cabinet #3"
            }
        ]
    },
    "1.19": {
        "title": "Abbreviations & Acronyms Guided Assistant",
        "intro": "List abbreviations and technical terminology used across this document:",
        "type": "table",
        "fields": [
            {
                "id": "abbrev",
                "label": "1. Abbreviation / Acronym:",
                "type": "text",
                "placeholder": "e.g., PH"
            },
            {
                "id": "definition",
                "label": "2. Full Expanded Definition:",
                "type": "text",
                "placeholder": "e.g., Program Head"
            },
            {
                "id": "bulk",
                "label": "Or paste multiple acronyms at once (one per line):",
                "type": "textarea",
                "placeholder": "TAT: Turnaround Time\nMOU: Memorandum of Understanding\nMIS: Management Information System\nPOCSO: Protection of Children from Sexual Offences"
            }
        ]
    },
    "1.20": {
        "title": "Best Practices Summary Guided Assistant",
        "intro": "Document proven industry methodologies and planned procedural improvements:",
        "type": "table",
        "fields": [
            {
                "id": "followed",
                "label": "1. Best Practice Currently Followed:",
                "type": "textarea",
                "placeholder": "e.g., Dual maker-checker verification of school infrastructure prior to MOU execution."
            },
            {
                "id": "envisaged",
                "label": "2. Envisaged / Planned Future Best Practice:",
                "type": "textarea",
                "placeholder": "e.g., Automated geo-tagged photo verification on mobile app."
            },
            {
                "id": "timeline",
                "label": "3. Tentative Timelines:",
                "type": "text",
                "placeholder": "e.g., Q3 FY 2026-27"
            }
        ]
    },
    "1.21": {
        "title": "Innovations Guided Assistant",
        "intro": "Capture digital transformations, automation, and continuous innovation initiatives:",
        "type": "table",
        "fields": [
            {
                "id": "implemented",
                "label": "1. Innovation Implemented:",
                "type": "textarea",
                "placeholder": "e.g., QR-code based school profile verification."
            },
            {
                "id": "planned",
                "label": "2. Envisaged / Planned Innovation:",
                "type": "textarea",
                "placeholder": "e.g., AI-assisted rubric evaluation for school infrastructure readiness."
            },
            {
                "id": "timeline",
                "label": "3. Tentative Timelines:",
                "type": "text",
                "placeholder": "e.g., Q4 FY 2026-27"
            }
        ]
    },
    "1.22": {
        "title": "SIPOC Guided Assistant",
        "intro": "Map Suppliers, Inputs, Process Steps, Outputs, and Customers at a high level:",
        "type": "table",
        "fields": [
            {
                "id": "supplier",
                "label": "1. Supplier (Department / External Source):",
                "type": "text",
                "placeholder": "e.g., State Education Department"
            },
            {
                "id": "input",
                "label": "2. Input (Data / Material received):",
                "type": "textarea",
                "placeholder": "e.g., Approved partner school application & infrastructure records"
            },
            {
                "id": "process",
                "label": "3. Key Process Step (matching Process Description):",
                "type": "textarea",
                "placeholder": "e.g., Eligibility Check, Feasibility Audit, MOU Signing & Orientation"
            },
            {
                "id": "output",
                "label": "4. Output (Deliverables produced):",
                "type": "textarea",
                "placeholder": "e.g., Signed MOU Dossier & Active Onboarded School"
            },
            {
                "id": "customer",
                "label": "5. Customer (Receiving Department / Beneficiaries):",
                "type": "text",
                "placeholder": "e.g., Program Delivery Team & Operations Lead"
            }
        ]
    }
}


def build_table_rows_from_answers(sec_id: str, answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Converts structured questionnaire answers directly into the exact schema required for table sections."""
    today_str = str(datetime.date.today())

    if sec_id == "1.1":
        sign_date = str(answers.get("sign_date", today_str))
        def parse_role_entry(text: str, default_role: str):
            parts = [p.strip() for p in text.split("|")]
            name = parts[0] if len(parts) > 0 and parts[0] else "TBD"
            func = parts[1] if len(parts) > 1 and parts[1] else "Operations"
            sign = parts[2] if len(parts) > 2 and parts[2] else name[:2].upper()
            return {"Name": name, "Role": default_role, "Function": func, "Sign": sign, "Date": sign_date}
        return [
            parse_role_entry(str(answers.get("owner", "Process Owner | Operations | PO")), "Process Owner"),
            parse_role_entry(str(answers.get("reviewer", "Quality Lead | Business Excellence | QL")), "Process Reviewer"),
            parse_role_entry(str(answers.get("approver", "Program Director | Leadership | DIR")), "Process Approver")
        ]

    elif sec_id == "1.2":
        return [{
            "Version No.": str(answers.get("version", "1.0")).split()[0],
            "Effective Date": str(answers.get("eff_date", today_str)),
            "Change Date": str(answers.get("change_date", today_str)),
            "Change Request By": str(answers.get("req_by", "Process Owner")),
            "Change Made By": str(answers.get("made_by", "Process Creator")),
            "Amendment": str(answers.get("amendment", "Initial baseline version"))
        }]

    elif sec_id == "1.3":
        eff_date = answers.get("eff_date", datetime.date.today())
        freq = str(answers.get("review_frequency", "Annual (Every 12 months)"))
        next_date = answers.get("next_review_date") or compute_next_review_date(eff_date, freq)
        owner_role = str(answers.get("process_owner", "Program Head")).strip() or "Program Head"
        owner_name = str(answers.get("owner_name", "")).strip() or "Process Owner"
        sign = str(answers.get("owner_sign", "")).strip()
        if not sign:
            sign = "".join([p[0].upper() for p in owner_name.split()[:2]]) or "PO"

        return [{
            "Effective Date": str(eff_date),
            "Next Review Date": str(next_date),
            "Process Owner": owner_role,
            "Name": owner_name,
            "Sign": sign
        }]

    elif sec_id == "1.4":
        rows = [{
            "Process / Policy ID": str(answers.get("policy_id", "SOP-OPS-012")),
            "Document Name": str(answers.get("doc_name", "Partner School Onboarding Policy"))
        }]
        template = str(answers.get("template_name", "")).strip()
        if template:
            rows.append({
                "Process / Policy ID": "FORM-01",
                "Document Name": template
            })
        return rows

    elif sec_id == "1.5":
        return [{
            "Description": str(answers.get("kpi_desc", "Turnaround Time (TAT)")),
            "Owner": str(answers.get("owner", "Program Head")),
            "Target": str(answers.get("target", "<= 5 Business Days")),
            "Maker": str(answers.get("maker", "Field Officer")),
            "Checker": str(answers.get("checker", "Operations Manager")),
            "Data Source": str(answers.get("data_source", "MIS Dashboard")),
            "Report Name": str(answers.get("data_source", "Onboarding Performance MIS")),
            "Report Frequency": str(answers.get("report_freq", "Monthly")),
            "Review Frequency": str(answers.get("review_freq", "Monthly"))
        }]

    elif sec_id == "1.7":
        act = str(answers.get("activity") or answers.get("incoming_trigger") or answers.get("trigger") or "").strip()
        entry_crit = str(answers.get("entry_criteria") or answers.get("criteria") or answers.get("prerequisites") or "").strip()
        return [{
            "Activity": act,
            "Entry Criteria": entry_crit
        }]

    elif sec_id == "1.8":
        act = str(answers.get("activity") or answers.get("concluding_activity") or answers.get("deliverable") or "").strip()
        exit_crit = str(answers.get("exit_criteria") or answers.get("criteria") or answers.get("signoff") or "").strip()
        return [{
            "Activity": act,
            "Exit Criteria": exit_crit
        }]

    elif sec_id == "1.12":
        # Delineates all 6 mandatory BE dimensions in Description
        act_name = str(answers.get("activity_name", "Core Operational Activity")).strip()
        inputs = str(answers.get("inputs", "Standard input documents")).strip()
        sub_steps = str(answers.get("sub_steps", "1. Execute operational steps.")).strip()
        tools = str(answers.get("tools", "MIS Portal, Google Workspace")).strip()
        handoffs = str(answers.get("handoffs", "Handed off to Next Stage Lead")).strip()
        deliverables = str(answers.get("deliverables", "Completed Operational Deliverable")).strip()
        validations = str(answers.get("validations", "Checker verification & approval sign-off")).strip()
        owner = str(answers.get("owner_role", "Field Officer & Program Head")).strip()
        tat = str(answers.get("tat", "5 Business Days")).strip()

        desc_formatted = (
            f"1. Inputs: {inputs}\n"
            f"2. Sub-steps:\n{sub_steps}\n"
            f"3. Tools & Systems: {tools}\n"
            f"4. Stakeholders & Hand-offs: {handoffs}\n"
            f"5. Expected Deliverable: {deliverables}\n"
            f"6. Checks & Validations: {validations}"
        )
        return [{
            "Activity": act_name,
            "Description": desc_formatted,
            "Owner/Role": owner,
            "TAT": tat
        }]

    elif sec_id == "1.13":
        return [{
            "Sr. No.": 1,
            "Activity name": str(answers.get("activity_name", "Plan of the Onboarding of the schools")),
            "Activity description": str(answers.get("activity_desc", "1. Location selection. 2. Liaison. 3. Filter analysis.")),
            "Timeline": str(answers.get("timeline", "Given timeline")),
            "Responsible": str(answers.get("responsible", "PH")),
            "Accountable": str(answers.get("accountable", "Manager")),
            "Consulted by": str(answers.get("consulted", "Director")),
            "Informed to": str(answers.get("informed", "CEO Project teams"))
        }]

    elif sec_id == "1.14":
        rule = str(answers.get("rule_statement", "Mandatory operational rule")).strip()
        enforcement = str(answers.get("enforcement", "")).strip()
        full_rule = f"{rule} (Enforced by {enforcement})" if enforcement else rule
        return [{"Business Rules": full_rule}]

    elif sec_id == "1.15":
        return [{
            "Area of Exception": str(answers.get("area", "Eligibility Criteria")),
            "Exception Description": str(answers.get("desc", "Standard criteria deviation")),
            "Exception Mitigation": str(answers.get("mitigation", "Special compensatory approval")),
            "Prop By": str(answers.get("prop_by", "Field Officer")),
            "Recom By": str(answers.get("recom_by", "Program Head")),
            "Approved By": str(answers.get("approved_by", "Program Director")),
            "Informed to": str(answers.get("informed_to", "Vertical Lead")),
            "Remarks": "Documented in exception register"
        }]

    elif sec_id == "1.16":
        return [{
            "Sub Process": str(answers.get("sub_process", "Core Field Operations")),
            "Risk Description": str(answers.get("desc", "Data discrepancy during field execution")),
            "Root Cause": str(answers.get("root_cause", "Manual record keeping")),
            "Type of Risk": str(answers.get("risk_type", "Operational")),
            "Risk Impact": str(answers.get("impact", "Operational delay")),
            "Level of Risk": str(answers.get("level_of_risk", "Medium")),
            "Control Description": str(answers.get("control", "Mandatory Maker-Checker cross verification")),
            "Control frequency": str(answers.get("freq", "Every Transaction"))
        }]

    elif sec_id == "1.17":
        return [{
            "Sub Process": str(answers.get("sub_process", "Operational Governance")),
            "Compliance particulars": str(answers.get("compliance", "Adherence to statutory policy and child safety regulations")),
            "Target date": str(answers.get("target_date", "Annual Audit / April 30"))
        }]

    elif sec_id == "1.18":
        return [{
            "Sub Process": "Documentation & Records",
            "Financial Year": str(answers.get("fy", "FY 2025-26")),
            "Document Title": str(answers.get("doc_title", "Signed MOUs & Verification Reports")),
            "Criticality": str(answers.get("criticality", "High")),
            "Storage Type": str(answers.get("storage_type", "Both Soft & Hard copy")),
            "Cut off Period": "Financial Year End",
            "Retention period": str(answers.get("retention", "7 Years")),
            "Location - hard copy": str(answers.get("hard_loc", "Central Operations Cabinet")),
            "Folder link - soft copy": str(answers.get("soft_link", "SharePoint/Operations_Archive"))
        }]

    elif sec_id == "1.19":
        rows = []
        bulk = str(answers.get("bulk", "")).strip()
        if bulk:
            for line in bulk.split("\n"):
                line = line.strip()
                if ":" in line:
                    abbr, defn = line.split(":", 1)
                    rows.append({"Abbreviation": abbr.strip(), "Definition": defn.strip()})
                elif "-" in line:
                    abbr, defn = line.split("-", 1)
                    rows.append({"Abbreviation": abbr.strip(), "Definition": defn.strip()})
        abbr = str(answers.get("abbrev", "")).strip()
        defn = str(answers.get("definition", "")).strip()
        if abbr and defn:
            rows.insert(0, {"Abbreviation": abbr, "Definition": defn})
        if not rows:
            rows = [{"Abbreviation": "PH", "Definition": "Program Head"}]
        return rows

    elif sec_id == "1.20":
        return [{
            "Best Practices Followed (suggested list)": str(answers.get("followed", "Dual maker-checker verification")),
            "Envisaged/Planned": str(answers.get("envisaged", "Automated geo-tagged mobile verification")),
            "Tentative Timelines": str(answers.get("timeline", "Q3 FY 2026-27"))
        }]

    elif sec_id == "1.21":
        return [{
            "Innovations Implemented": str(answers.get("implemented", "QR-code based digital verification")),
            "Envisaged/Planned": str(answers.get("planned", "AI-assisted rubric evaluation")),
            "TENTATIVE TIMELINES": str(answers.get("timeline", "Q4 FY 2026-27"))
        }]

    elif sec_id == "1.22":
        return [{
            "Supplier (Dept)": str(answers.get("supplier", "Education Department")),
            "Input": str(answers.get("input", "Approved application and school records")),
            "Key Process Step": str(answers.get("process", "Feasibility Audit, MOU Signing & Orientation")),
            "Output": str(answers.get("output", "Active Onboarded School")),
            "Customer (dept)": str(answers.get("customer", "Program Delivery Team"))
        }]

    return []


def build_text_summary_from_answers(sec_id: str, answers: Dict[str, Any]) -> str:
    """Formats structured questionnaire answers into clean, corporate markdown text for text sections."""
    if sec_id == "1.6":
        in_scope = answers.get("in_scope", "All operational activities as detailed in this note.")
        out_scope = answers.get("out_of_scope", "Any external activities not explicitly mentioned.")
        stakeholders = answers.get("stakeholders", "All partner stakeholders.")
        return (
            "### 1. In-Scope Activities & Coverage\n"
            f"{in_scope}\n\n"
            "### 2. Out-of-Scope Activities & Exclusions\n"
            f"{out_scope}\n\n"
            "### 3. Target Stakeholders & Beneficiaries\n"
            f"{stakeholders}"
        )

    elif sec_id == "1.9":
        bg = answers.get("background", "Standard operating protocol established for operational excellence.")
        imp = answers.get("importance", "Standardization ensures compliance, transparency, and accountability.")
        return (
            "### Background Context\n"
            f"{bg}\n\n"
            "### Strategic Organizational Importance\n"
            f"{imp}"
        )

    elif sec_id == "1.10":
        obj = answers.get("primary_obj", "To execute operational activities in a timely, compliant manner.")
        outcome = answers.get("measurable_outcome", "Zero-defect delivery and 100% adherence to timelines.")
        return (
            "### Primary Business Objective\n"
            f"{obj}\n\n"
            "### Expected Measurable Outcomes\n"
            f"{outcome}"
        )

    # General fallback
    summary_lines = []
    for k, v in answers.items():
        if v:
            summary_lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
    return "\n".join(summary_lines)


def build_mermaid_flowchart_from_answers(answers: Dict[str, Any]) -> str:
    """Generates a clean Mermaid flowchart from structured wizard answers."""
    steps_raw = str(answers.get("steps", "")).strip()
    decisions_raw = str(answers.get("decisions", "")).strip()
    roles = str(answers.get("roles", "")).strip()

    lines = ["flowchart TD"]
    lines.append("    Start([Process Start]) --> Step1[1. Process Initiation]")
    
    step_items = [s.strip() for s in steps_raw.split("\n") if s.strip()]
    if not step_items:
        step_items = ["Initial Request Submission", "Document Review & Screening", "Operational Execution & Verification", "Final Sign-off & Delivery"]

    prev_node = "Step1"
    for idx, item in enumerate(step_items, start=2):
        node_id = f"Step{idx}"
        # clean label
        clean_label = item.replace("[", "").replace("]", "").replace('"', "")
        lines.append(f"    {prev_node} --> {node_id}[\"{clean_label}\"]")
        prev_node = node_id

    if decisions_raw:
        lines.append(f"    {prev_node} --> Dec1{{\"Decision Criteria Met?\"}}")
        lines.append("    Dec1 -- Yes --> StepAppr[\"Approval & Sign-off\"]")
        lines.append("    Dec1 -- No --> StepRej[\"Rejection & Return with Remarks\"]")
        lines.append("    StepRej -.-> Step1")
        lines.append("    StepAppr --> EndNode([Process End])")
    else:
        lines.append(f"    {prev_node} --> EndNode([Process End])")

    return "\n".join(lines)


# Backward compatibility dictionary
SECTION_GUIDED_QUESTIONS = {
    sec_id: {
        "title": spec["title"],
        "questions": [f["label"] for f in spec["fields"]],
        "placeholder": spec["fields"][0].get("placeholder", "") if spec["fields"] else ""
    }
    for sec_id, spec in SECTION_GUIDED_SPECS.items()
}
