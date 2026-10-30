import datetime
import re
from typing import Dict, Any, List, Tuple

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
        "title": "Approval Matrix (Sign-off Stakeholders)",
        "intro": "Add sign-off stakeholders one by one. Select the role from the dropdown (Process Owner, Process Reviewer, Process Approver, or custom role), provide person details, and click Add Row to build your Approval Matrix:",
        "type": "table",
        "fields": [
            {
                "id": "role",
                "label": "Sign-off Role *:",
                "type": "select",
                "options": [
                    "Process Owner",
                    "Process Reviewer",
                    "Process Approver",
                    "Other (Specify custom role...)"
                ],
                "default": "Process Owner",
                "help": "💡 Select the sign-off role from the dropdown or choose Other to specify a custom role."
            },
            {
                "id": "name",
                "label": "Stakeholder Full Name *:",
                "type": "text",
                "placeholder": "e.g., Aarav Sharma",
                "help": "💡 [Mandatory] Full name of the designated person."
            },
            {
                "id": "function",
                "label": "Function / Department *:",
                "type": "text",
                "placeholder": "e.g., Lead - School Operations",
                "help": "💡 [Mandatory] Functional department or vertical."
            },
            {
                "id": "sign",
                "label": "Sign / Initials (Optional):",
                "type": "text",
                "placeholder": "e.g., AS",
                "help": "💡 [Optional] Initials or signature code (auto-generated from name if left blank)."
            },
            {
                "id": "date",
                "label": "Sign-off Date *:",
                "type": "date",
                "help": "💡 [Mandatory] Date of sign-off or authorization."
            }
        ]
    },
    "1.2": {
        "title": "Document Change History",
        "intro": "Track the version number and reason for this release. For a new document, Version 1.0 is already selected:",
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
                "label": "Effective Date (When this version goes live):",
                "type": "date"
            },
            {
                "id": "change_date",
                "label": "Date of Change / Release:",
                "type": "date"
            },
            {
                "id": "amendment",
                "label": "Summary of Purpose / Changes:",
                "type": "textarea",
                "placeholder": "e.g., Initial baseline version created to standardize partner school onboarding workflows."
            },
            {
                "id": "req_by",
                "label": "Change Requested By (Optional):",
                "type": "text",
                "placeholder": "e.g., Operations Director / Business Excellence"
            },
            {
                "id": "made_by",
                "label": "Created / Authored By:",
                "type": "text",
                "placeholder": "e.g., Program Head (Creator)"
            }
        ]
    },
    "1.3": {
        "title": "Document Review Cycle",
        "intro": "Set how often this process note should be revisited to ensure it stays current and accurate:",
        "type": "table",
        "fields": [
            {
                "id": "eff_date",
                "label": "1. Effective Date (When this document becomes active):",
                "type": "date",
                "help": "💡 The date from which this version becomes binding."
            },
            {
                "id": "review_frequency",
                "label": "2. How often should this document be reviewed?",
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
                "help": "💡 Corporate standard is Annual or Semi-Annual."
            },
            {
                "id": "next_review_date",
                "label": "3. Scheduled Next Review Date (Auto-calculated):",
                "type": "calculated_date",
                "help": "💡 Auto-calculated based on effective date and cycle. You can adjust if needed."
            },
            {
                "id": "process_owner",
                "label": "4. Designated Review Owner Role:",
                "type": "text",
                "placeholder": "e.g., Program Head (or Operations Manager)",
                "help": "💡 Designation responsible for periodic review."
            },
            {
                "id": "owner_name",
                "label": "5. Review Owner Full Name:",
                "type": "text",
                "placeholder": "e.g., John Doe",
                "help": "💡 Full name of the designated review owner."
            },
            {
                "id": "owner_sign",
                "label": "6. Signature Code / Initials:",
                "type": "text",
                "placeholder": "e.g., JD or PH",
                "help": "💡 Short signature initials."
            }
        ]
    },
    "1.4": {
        "title": "Related Documents & SOPs",
        "intro": "List any connected organizational policies, SOPs, or assessment templates used in this process:",
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
        "title": "Key Performance Indicators (KPIs)",
        "intro": "Define how success and efficiency are measured for this process. AI will standardize the target and Maker-Checker governance structure:",
        "type": "table",
        "fields": [
            {
                "id": "kpi_desc",
                "label": "1. What is being measured? (Metric & Description):",
                "type": "text",
                "placeholder": "e.g., School Onboarding Turnaround Time (TAT) from application to MOU",
                "help": "💡 The operational performance metric or SLA being tracked."
            },
            {
                "id": "target",
                "label": "2. Target Benchmark / Goal:",
                "type": "text",
                "placeholder": "e.g., <= 5 Business Days (Adherence >= 98%)",
                "help": "💡 The measurable threshold or standard to achieve."
            },
            {
                "id": "owner",
                "label": "3. Overall KPI Owner (Role responsible for target):",
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
                "help": "💡 Role accountable for meeting this KPI target."
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
                "help": "💡 Role responsible for entering raw performance data."
            },
            {
                "id": "checker",
                "label": "5. Checker (Who verifies / audits data accuracy):",
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
                "help": "💡 Role verifying and auditing accuracy before reporting."
            },
            {
                "id": "report_freq",
                "label": "6. How often is performance reported?",
                "type": "select",
                "options": ["Monthly", "Weekly", "Daily", "Quarterly"],
                "default": "Monthly"
            },
            {
                "id": "review_freq",
                "label": "7. How often does leadership review it?",
                "type": "select",
                "options": ["Monthly", "Quarterly", "Semi-Annually", "Annually"],
                "default": "Monthly"
            },
            {
                "id": "data_source",
                "label": "8. Data Source & Dashboard Name:",
                "type": "text",
                "placeholder": "e.g., Operations MIS Onboarding Dashboard",
                "help": "💡 System, portal, or spreadsheet where data originates."
            }
        ]
    },
    "1.6": {
        "title": "Process Scope & Coverage",
        "intro": "Define what this process covers and what is excluded. AI will format it into clear operational boundaries:",
        "type": "text",
        "fields": [
            {
                "id": "in_scope",
                "label": "1. In-Scope Activities (What is covered?):",
                "type": "textarea",
                "placeholder": "e.g., Identification, feasibility study, due diligence, MOU signing, and welcome orientation for partner schools across Maharashtra.",
                "help": "💡 Operational stages and workflows included in this note."
            },
            {
                "id": "out_of_scope",
                "label": "2. Out-of-Scope / Exclusions (What is handled separately?):",
                "type": "textarea",
                "placeholder": "e.g., Teacher payroll, infrastructure capital grants, and curriculum design (handled under separate SOPs).",
                "help": "💡 Activities explicitly excluded from this process note."
            },
            {
                "id": "stakeholders",
                "label": "3. Covered Teams / Beneficiaries:",
                "type": "text",
                "placeholder": "e.g., Urban and rural government-aided schools, Field Operations Team, Regional Program Leads."
            }
        ]
    },
    "1.7": {
        "title": "Start Point (Process Trigger & Entry Criteria)",
        "intro": "How does this process kick off? Tell us what event initiates it and what must be ready before starting:",
        "type": "table",
        "fields": [
            {
                "id": "activity",
                "label": "1. What triggers this process to start?",
                "type": "text",
                "placeholder": "e.g., Receipt of approved Annual School Expansion Plan from Program Director",
                "help": "💡 The specific event, schedule, or request that begins this process."
            },
            {
                "id": "entry_criteria",
                "label": "2. What must be ready / verified before starting? (Entry Criteria):",
                "type": "textarea",
                "placeholder": "e.g., Signed budget allocation, verified target school list, and Field Officer assignment.",
                "help": "💡 Quick Tip: Mention at least one prerequisite document, list, or approval needed before work can begin."
            }
        ]
    },
    "1.8": {
        "title": "End Point (Final Output & Exit Criteria)",
        "intro": "How does this process wrap up? What final deliverable or sign-off marks it as 100% complete?",
        "type": "table",
        "fields": [
            {
                "id": "activity",
                "label": "1. What is the final activity or deliverable?",
                "type": "text",
                "placeholder": "e.g., Final signed MOU uploaded to ERP and welcome orientation kit delivered",
                "help": "💡 The concluding milestone or final output of this process."
            },
            {
                "id": "exit_criteria",
                "label": "2. What confirms completion? (Exit Criteria & Sign-off):",
                "type": "textarea",
                "placeholder": "e.g., Verification of onboarding checklist in MIS by Program Head and confirmation email sent.",
                "help": "💡 Quick Tip: Specify the sign-off, system verification, or formal acknowledgment that wraps up the process."
            }
        ]
    },
    "1.9": {
        "title": "Introduction & Organizational Context",
        "intro": "Why does this process exist? Write simple notes or bullet points—AI will elevate it into a polished corporate narrative:",
        "type": "text",
        "fields": [
            {
                "id": "background",
                "label": "1. Background Context (What is this initiative and why was it started?):",
                "type": "textarea",
                "placeholder": "e.g., Kotak Education Foundation partners with municipal and rural schools to enhance foundational learning. This process establishes standard operating protocols.",
                "help": "💡 Share the operational context or history behind this process."
            },
            {
                "id": "importance",
                "label": "2. Strategic Purpose (Why is standardizing this important?):",
                "type": "textarea",
                "placeholder": "e.g., Standardizing ensures uniform partner quality, transparent accountability, regulatory compliance, and seamless stakeholder hand-offs.",
                "help": "💡 What benefits or risks are addressed by standardizing this process?"
            }
        ]
    },
    "1.10": {
        "title": "Process Objectives & Tangible Outcomes",
        "intro": "What are the main goals of this process? AI will organize them into clear, measurable operational objectives:",
        "type": "text",
        "fields": [
            {
                "id": "primary_obj",
                "label": "1. What is the primary business goal of this process?",
                "type": "textarea",
                "placeholder": "e.g., To establish an error-free, timely, and compliant onboarding mechanism for 200+ partner schools within a standard 10-day TAT.",
                "help": "💡 State the main mission or deliverable this process accomplishes."
            },
            {
                "id": "measurable_outcome",
                "label": "2. Key Measurable Outcomes or Success Criteria:",
                "type": "text",
                "placeholder": "e.g., 100% compliant documentation, zero audit findings, and prompt stakeholder communication.",
                "help": "💡 What indicates that the process succeeded?"
            }
        ]
    },
    "1.11": {
        "title": "Process Flowchart (Visual Steps & Decisions)",
        "intro": "List the sequential steps and any key decision points. AI will instantly generate an enterprise BPMN flowchart for you:",
        "type": "flowchart",
        "fields": [
            {
                "id": "steps",
                "label": "1. Step-by-Step Flow (Start to End):",
                "type": "textarea",
                "placeholder": "Step 1: Field Lead submits application\nStep 2: Manager conducts initial screening\nStep 3: Verification Lead performs due diligence\nStep 4: Director reviews & signs MOU",
                "help": "💡 Quick Tip: Number your steps or write one step per line. Include the person or role responsible for each step."
            },
            {
                "id": "decisions",
                "label": "2. Key Decision Points / Conditions (Optional):",
                "type": "textarea",
                "placeholder": "Decision at Step 2: If criteria met -> Proceed to Step 3; If rejected -> Return with remarks.",
                "help": "💡 Optional: Any yes/no decision diamonds (e.g., 'If approved -> Step 3; If rejected -> Revise')."
            },
            {
                "id": "roles",
                "label": "3. Key Roles Involved (Optional):",
                "type": "text",
                "placeholder": "e.g., Field Officer, Manager, Quality Lead, Program Director",
                "help": "💡 Optional: List the primary roles executing these steps."
            }
        ]
    },
    "1.12": {
        "title": "Process Description (Step-by-Step Activities)",
        "intro": "Describe what happens in each key activity. Just enter the main steps or bullets—AI will polish the language and automatically format all required enterprise details (inputs, tools, hand-offs, and validations):",
        "type": "table",
        "fields": [
            {
                "id": "activity_name",
                "label": "Activity Name:",
                "type": "text",
                "placeholder": "e.g., School Selection and Due Diligence",
                "help": "💡 Give this activity a clear, descriptive title."
            },
            {
                "id": "sub_steps",
                "label": "What happens in this activity? (Numbered steps or simple bullets):",
                "type": "textarea",
                "placeholder": "1. Filter applications in Excel based on eligibility criteria.\n2. Field Officer conducts physical on-ground infrastructure audit.\n3. Verify teacher-student ratio and basic sanitation facilities.",
                "help": "💡 Quick Tip: List the main steps in sequence. Don't worry about perfect wording—AI will standardize everything."
            },
            {
                "id": "owner_role",
                "label": "Who executes this activity? (Owner / Role):",
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
                "help": "💡 Select or specify the role responsible for performing this work."
            },
            {
                "id": "tat",
                "label": "Estimated Timeline / TAT:",
                "type": "text",
                "placeholder": "e.g., 2 Business Days (or 5 Days)",
                "help": "💡 How long does this activity usually take to complete?"
            },
            {
                "id": "inputs",
                "label": "Inputs & Records Needed (Optional - leave blank for AI auto-fill):",
                "type": "text",
                "placeholder": "e.g., District school registry, application form, budget allocation (Leave blank for AI auto-fill)",
                "help": "💡 Optional: What documents or records are needed to start? (Leave blank to let AI auto-generate standard inputs)."
            },
            {
                "id": "tools",
                "label": "Tools, Systems & Apps Used (Optional - leave blank for AI auto-fill):",
                "type": "text",
                "placeholder": "e.g., KEF Field App, Google Sheets, State Portal (Leave blank for AI auto-fill)",
                "help": "💡 Optional: Portals, apps, or software used."
            },
            {
                "id": "handoffs",
                "label": "Next Hand-off / Stakeholder (Optional - leave blank for AI auto-fill):",
                "type": "text",
                "placeholder": "e.g., Field Officer hands dossier to Operations Manager (Leave blank for AI auto-fill)",
                "help": "💡 Optional: Who receives the work once completed?"
            },
            {
                "id": "deliverables",
                "label": "Expected Deliverable / Output (Optional - leave blank for AI auto-fill):",
                "type": "text",
                "placeholder": "e.g., Completed Due Diligence Scorecard & Recommendation Report (Leave blank for AI auto-fill)",
                "help": "💡 Optional: The tangible output or document produced."
            },
            {
                "id": "validations",
                "label": "Checks & Approvals (Optional - leave blank for AI auto-fill):",
                "type": "text",
                "placeholder": "e.g., Manager checks scorecard against minimum 80% criteria (Leave blank for AI auto-fill)",
                "help": "💡 Optional: Who reviews or signs off on this step?"
            }
        ]
    },
    "1.13": {
        "title": "RACI Matrix (Roles & Responsibilities)",
        "intro": "Map who is Responsible (R), Accountable (A), Consulted (C), and Informed (I) for each activity. (Tip: You can also auto-sync all activities directly from Section 1.12 below!):",
        "type": "table",
        "fields": [
            {
                "id": "activity_name",
                "label": "Activity Name:",
                "type": "text",
                "placeholder": "e.g., School Onboarding and Due Diligence",
                "help": "💡 Activity title matching your process steps."
            },
            {
                "id": "activity_desc",
                "label": "Activity Description / Key Steps:",
                "type": "textarea",
                "placeholder": "1. Geographical location selection.\n2. Liaison with government authority.\n3. Filter analysis of potential schools.",
                "help": "💡 Brief summary of key sub-steps."
            },
            {
                "id": "timeline",
                "label": "Timeline / TAT:",
                "type": "text",
                "placeholder": "e.g., 5 Business Days (or Given timeline)",
                "help": "💡 Target completion timeframe."
            },
            {
                "id": "responsible",
                "label": "Responsible (R - Who executes the work):",
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
                "help": "💡 Specific job role executing the activity."
            },
            {
                "id": "accountable",
                "label": "Accountable (A - Single sign-off owner):",
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
                "help": "💡 The single person who owns the final approval and outcome."
            },
            {
                "id": "consulted",
                "label": "Consulted by (C - Advisors & Experts):",
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
                "help": "💡 Who provides inputs, legal guidance, or technical advice."
            },
            {
                "id": "informed",
                "label": "Informed to (I - Teams kept updated):",
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
                "help": "💡 Who is kept in the loop on status and completion."
            }
        ]
    },
    "1.14": {
        "title": "Business Rules & Non-Negotiable Policies",
        "intro": "What are the mandatory ground rules or policies team members must follow? AI will format them with clear operational enforcement:",
        "type": "table",
        "fields": [
            {
                "id": "rule_statement",
                "label": "1. Ground Rule or Policy Statement:",
                "type": "textarea",
                "placeholder": "e.g., All translated scripts must pass a peer grammar check before recording.",
                "help": "💡 What is the mandatory standard or boundary that cannot be bypassed?"
            },
            {
                "id": "enforcement",
                "label": "2. Who enforces this and how? (Optional - leave blank for AI auto-fill):",
                "type": "textarea",
                "placeholder": "e.g., Quality Lead verifies against standard translation rubric before releasing to studio (Leave blank for AI auto-fill)",
                "help": "💡 Optional: Who checks compliance? If left blank, AI assigns the Process Owner and designated Reviewer."
            }
        ]
    },
    "1.15": {
        "title": "Exception & Deviation Management",
        "intro": "What deviations or special cases might occur, and who has the authority to approve them?",
        "type": "table",
        "fields": [
            {
                "id": "area",
                "label": "1. Area or Step where exception may occur:",
                "type": "text",
                "placeholder": "e.g., School Eligibility Criteria / TAT Extension",
                "help": "💡 The operational domain or activity where deviations happen."
            },
            {
                "id": "desc",
                "label": "2. What is the exception or deviation?",
                "type": "textarea",
                "placeholder": "e.g., Target school has fewer students than the minimum enrollment threshold.",
                "help": "💡 Describe the unusual situation or criteria variance."
            },
            {
                "id": "mitigation",
                "label": "3. How is it handled or mitigated?",
                "type": "textarea",
                "placeholder": "e.g., Cluster onboarding with adjacent rural school to meet collective threshold.",
                "help": "💡 Compensatory action or conditions required to approve."
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
        "title": "Risk Management & Preventive Controls",
        "intro": "What could go wrong in this process (errors, delays, compliance issues) and how do you prevent or catch it?",
        "type": "table",
        "fields": [
            {
                "id": "sub_process",
                "label": "1. Activity or Stage where risk exists:",
                "type": "text",
                "placeholder": "e.g., School Due Diligence & Data Verification"
            },
            {
                "id": "desc",
                "label": "2. What is the risk? (What could go wrong?):",
                "type": "text",
                "placeholder": "e.g., Inaccurate school student enrollment figures reported",
                "help": "💡 The potential failure or error."
            },
            {
                "id": "root_cause",
                "label": "3. Root Cause (Why might this happen?):",
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
                "label": "5. Risk Severity Level:",
                "type": "select",
                "options": ["High", "Medium", "Low"],
                "default": "Medium"
            },
            {
                "id": "impact",
                "label": "6. Potential Impact:",
                "type": "text",
                "placeholder": "e.g., Misallocation of learning materials and budget"
            },
            {
                "id": "control",
                "label": "7. Preventive Action / Control:",
                "type": "textarea",
                "placeholder": "e.g., Mandatory physical cross-verification against government attendance registers",
                "help": "💡 The specific check, audit, or rule that stops or catches the risk."
            },
            {
                "id": "freq",
                "label": "8. How often is this check done?",
                "type": "select",
                "options": ["Every Transaction", "Daily", "Weekly", "Monthly", "Quarterly", "Annual"],
                "default": "Every Transaction"
            }
        ]
    },
    "1.17": {
        "title": "Compliance & Statutory Obligations",
        "intro": "List statutory, child safety (POCSO), regulatory, or institutional obligations that must be complied with:",
        "type": "table",
        "fields": [
            {
                "id": "sub_process",
                "label": "1. Compliance Area or Obligation:",
                "type": "text",
                "placeholder": "e.g., Child Safety (POCSO) & Personnel Background Checks"
            },
            {
                "id": "compliance",
                "label": "2. Policy Norms & Requirements:",
                "type": "textarea",
                "placeholder": "e.g., Mandatory POCSO guidelines compliance and police verification for all field trainers before school visits.",
                "help": "💡 Exact statutory or organizational compliance standard."
            },
            {
                "id": "target_date",
                "label": "3. Verification Schedule / Due Date:",
                "type": "text",
                "placeholder": "e.g., Prior to on-ground deployment / Annual verification completed by April 30"
            }
        ]
    },
    "1.18": {
        "title": "Data Archival & Document Retention",
        "intro": "Specify where records are stored (cloud repository or physical cabinet) and how long they must be retained:",
        "type": "table",
        "fields": [
            {
                "id": "doc_title",
                "label": "1. Document or Record Title:",
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
                "label": "3. Document Criticality:",
                "type": "select",
                "options": ["High", "Medium", "Low"],
                "default": "High"
            },
            {
                "id": "storage_type",
                "label": "4. Storage Format:",
                "type": "select",
                "options": ["Both Soft & Hard copy", "Soft copy", "Hard copy"],
                "default": "Both Soft & Hard copy"
            },
            {
                "id": "retention",
                "label": "5. Mandatory Retention Period:",
                "type": "select",
                "options": ["7 Years", "5 Years", "3 Years", "10 Years", "Permanent"],
                "default": "7 Years"
            },
            {
                "id": "soft_link",
                "label": "6. Cloud Folder / System Link (Soft Copy):",
                "type": "text",
                "placeholder": "e.g., SharePoint/KEF_MOU_Archive"
            },
            {
                "id": "hard_loc",
                "label": "7. Physical Storage Location (Hard Copy):",
                "type": "text",
                "placeholder": "e.g., Central Operations Cabinet #3"
            }
        ]
    },
    "1.19": {
        "title": "Abbreviations & Acronyms",
        "intro": "List any abbreviations or shorthand used in this document (e.g. MOU, TAT, MIS). You can add one by one or paste multiple at once:",
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
                "label": "2. Full Meaning / Definition:",
                "type": "text",
                "placeholder": "e.g., Program Head"
            },
            {
                "id": "bulk",
                "label": "Or paste multiple acronyms at once (one per line):",
                "type": "textarea",
                "placeholder": "TAT: Turnaround Time\nMOU: Memorandum of Understanding\nMIS: Management Information System\nPOCSO: Protection of Children from Sexual Offences",
                "help": "💡 Paste as many acronyms as you like, formatted as 'ACRONYM: Definition'."
            }
        ]
    },
    "1.20": {
        "title": "Best Practices & Continuous Improvements",
        "intro": "Document proven industry practices followed today, and planned improvements for the future:",
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
                "label": "2. Planned Future Best Practice:",
                "type": "textarea",
                "placeholder": "e.g., Automated geo-tagged photo verification on field mobile app."
            },
            {
                "id": "timeline",
                "label": "3. Target Timeline:",
                "type": "text",
                "placeholder": "e.g., Q3 FY 2026-27"
            }
        ]
    },
    "1.21": {
        "title": "Innovations & Digital Automation",
        "intro": "Capture any new digital tools, automations, or innovative techniques introduced in this process:",
        "type": "table",
        "fields": [
            {
                "id": "implemented",
                "label": "1. Innovation Implemented / Active:",
                "type": "textarea",
                "placeholder": "e.g., QR-code based school profile verification."
            },
            {
                "id": "planned",
                "label": "2. Planned Future Innovation:",
                "type": "textarea",
                "placeholder": "e.g., AI-assisted rubric evaluation for school infrastructure readiness."
            },
            {
                "id": "timeline",
                "label": "3. Target Timeline:",
                "type": "text",
                "placeholder": "e.g., Q4 FY 2026-27"
            }
        ]
    },
    "1.22": {
        "title": "SIPOC Summary (High-Level Snapshot)",
        "intro": "Map the high-level flow: Suppliers, Inputs, Process Steps, Outputs, and Customers:",
        "type": "table",
        "fields": [
            {
                "id": "supplier",
                "label": "1. Suppliers (Who provides the inputs):",
                "type": "text",
                "placeholder": "e.g., State Education Department, Partner School Principals"
            },
            {
                "id": "input",
                "label": "2. Inputs (What records or information are provided):",
                "type": "textarea",
                "placeholder": "e.g., Approved partner school application & infrastructure records"
            },
            {
                "id": "process",
                "label": "3. Key Process Steps in Sequence:",
                "type": "textarea",
                "placeholder": "e.g., Eligibility Check -> Feasibility Audit -> MOU Signing -> Orientation"
            },
            {
                "id": "output",
                "label": "4. Outputs (Deliverables produced):",
                "type": "textarea",
                "placeholder": "e.g., Executed MOUs, verified school dossiers, welcome kits"
            },
            {
                "id": "customer",
                "label": "5. Customers / Beneficiaries (Who receives the outputs):",
                "type": "text",
                "placeholder": "e.g., Partner Schools, Students, Program Implementation Team"
            }
        ]
    }
}


def _build_table_rows_raw(sec_id: str, answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    today_str = str(datetime.date.today())

    if sec_id == "1.1":
        def make_sign(name_val: str, explicit_sign: str = ""):
            if explicit_sign.strip():
                return explicit_sign.strip().upper()
            clean_n = name_val.strip()
            parts = [p for p in clean_n.split() if p]
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            elif len(parts) == 1:
                return parts[0][:2].upper()
            return "TBD"

        # 1. Row-by-Row Mode: When adding individual sign-off stakeholder rows one by one
        if "role" in answers or ("name" in answers and "owner_name" not in answers):
            role_val = str(answers.get("role") or "Process Owner").strip()
            name_val = str(answers.get("name") or "").strip()
            func_val = str(answers.get("function") or answers.get("func") or "Operations").strip()
            sign_val = str(answers.get("sign") or "").strip() or make_sign(name_val)
            date_val = str(answers.get("date") or today_str).strip()
            if not name_val and not role_val:
                return []
            return [{
                "Name": name_val,
                "Role": role_val,
                "Function": func_val,
                "Sign": sign_val,
                "Date": date_val
            }]

        def get_val_or_pipe(prefix: str, fallback_func: str, fallback_name: str, is_optional: bool = False):
            # Check if user entered dedicated new fields: name, func, sign, date
            name = str(answers.get(f"{prefix}_name", "")).strip()
            func = str(answers.get(f"{prefix}_func", "")).strip()
            sign = str(answers.get(f"{prefix}_sign", "")).strip()
            date_val = str(answers.get(f"{prefix}_date", ""))

            # Support legacy pipe syntax if typed in old input
            if not name and prefix in answers:
                raw_str = str(answers.get(prefix, "")).strip()
                if "|" in raw_str:
                    parts = [p.strip() for p in raw_str.split("|")]
                    name = parts[0] if len(parts) > 0 and parts[0] else ""
                    func = parts[1] if len(parts) > 1 and parts[1] else ""
                    sign = parts[2] if len(parts) > 2 and parts[2] else ""
                else:
                    name = raw_str

            if is_optional and (not name or name.lower() in ["na", "n/a", "none"]):
                return name, func, sign, date_val

            name = name or fallback_name
            func = func or fallback_func
            sign = sign or (make_sign(name) if name else "TBD")
            date_val = date_val or str(answers.get("sign_date", today_str))
            return name, func, sign, date_val

        o_name, o_func, o_sign, o_date = get_val_or_pipe("owner", "School Operations", "Aarav Sharma")
        r_name, r_func, r_sign, r_date = get_val_or_pipe("reviewer", "Business Excellence & Quality", "", is_optional=True)
        a_name, a_func, a_sign, a_date = get_val_or_pipe("approver", "Field Programs", "Vikramaditya Roy")

        rows = [
            {"Name": o_name, "Role": "Process Owner", "Function": o_func, "Sign": o_sign, "Date": o_date}
        ]
        if r_name:
            is_na = r_name.lower() in ["na", "n/a", "none"]
            rows.append({
                "Name": r_name if not is_na else "N/A",
                "Role": "Process Reviewer",
                "Function": (r_func or "Business Excellence & Quality") if not is_na else "N/A",
                "Sign": (r_sign or make_sign(r_name)) if not is_na else "N/A",
                "Date": (r_date or o_date) if not is_na else "N/A"
            })
        rows.append({"Name": a_name, "Role": "Process Approver", "Function": a_func, "Sign": a_sign, "Date": a_date})
        return rows

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
        if not act:
            act = "Formal Process Trigger & Initiation"
        entry_crit = str(answers.get("entry_criteria") or answers.get("criteria") or answers.get("prerequisites") or "").strip()
        if not entry_crit:
            entry_crit = "Receipt of verified prerequisite documents, operational requirements, and designated stakeholder authorization."
        return [{
            "Activity": act,
            "Entry Criteria": entry_crit
        }]

    elif sec_id == "1.8":
        act = str(answers.get("activity") or answers.get("concluding_activity") or answers.get("deliverable") or "").strip()
        if not act:
            act = "Final Process Milestone Sign-off"
        exit_crit = str(answers.get("exit_criteria") or answers.get("criteria") or answers.get("signoff") or "").strip()
        if not exit_crit:
            exit_crit = "Verification and sign-off of final deliverable dossier by Program Head and stakeholder confirmation."
        return [{
            "Activity": act,
            "Exit Criteria": exit_crit
        }]

    elif sec_id == "1.12":
        # Delineates all 6 mandatory enterprise dimensions in Description with smart auto-fill
        act_name = str(answers.get("activity_name") or "").strip() or "Core Operational Activity"
        sub_steps = str(answers.get("sub_steps") or "").strip()
        if not sub_steps:
            sub_steps = f"1. Review and verify incoming requirements.\n2. Execute operational workflow for {act_name}.\n3. Record completion in tracking system."

        inputs = str(answers.get("inputs") or "").strip()
        if not inputs:
            inputs = f"Requisite initiation records, registry dossiers, and prerequisite authorizations for {act_name}"

        tools = str(answers.get("tools") or "").strip()
        if not tools:
            tools = "Operations MIS Portal, Google Workspace, Excel Tracker"

        handoffs = str(answers.get("handoffs") or "").strip()
        if not handoffs:
            handoffs = "Handed over to next sequential stage owner upon completion"

        deliverables = str(answers.get("deliverables") or "").strip()
        if not deliverables:
            deliverables = f"Completed and verified {act_name} records and deliverable dossier"

        validations = str(answers.get("validations") or "").strip()
        if not validations:
            validations = "Designated Manager reviews and authorizes verification findings against institutional criteria"

        owner = str(answers.get("owner_role") or "Field Officer & Program Head").strip() or "Field Officer & Program Head"
        tat = str(answers.get("tat") or "2 Business Days").strip() or "2 Business Days"

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
            "Activity name": str(answers.get("activity_name") or "Plan of the Onboarding of the schools"),
            "Activity description": str(answers.get("activity_desc") or "1. Location selection. 2. Liaison with authority. 3. Filter analysis."),
            "Timeline": str(answers.get("timeline") or "Given timeline (5 days)"),
            "Responsible": str(answers.get("responsible") or "PH"),
            "Accountable": str(answers.get("accountable") or "Manager"),
            "Consulted by": str(answers.get("consulted") or "Director"),
            "Informed to": str(answers.get("informed") or "CEO Project teams")
        }]

    elif sec_id == "1.14":
        rule = sanitize_rough_text(str(answers.get("rule_statement") or "Mandatory operational compliance rule").strip())
        enforcement = sanitize_rough_text(str(answers.get("enforcement") or "").strip())
        if not enforcement:
            enforcement = "the Process Owner and designated Quality Reviewer through verification sign-off"
        full_rule = f"{rule} (Enforced by {enforcement})" if not (f"Enforced by {enforcement}" in rule or "enforced by" in rule.lower()) else rule
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


def build_table_rows_from_answers(sec_id: str, answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Converts structured questionnaire answers directly into the exact schema required for table sections, strictly stripping any &amp; into &."""
    cleaned_answers = {}
    for k, v in answers.items():
        if isinstance(v, str):
            while "&amp;" in v:
                v = v.replace("&amp;", "&")
        cleaned_answers[k] = v

    raw_rows = _build_table_rows_raw(sec_id, cleaned_answers)

    cleaned_rows = []
    for row in raw_rows:
        cleaned_row = {}
        for k, v in row.items():
            if isinstance(v, str):
                while "&amp;" in v:
                    v = v.replace("&amp;", "&")
            cleaned_row[k] = v
        cleaned_rows.append(cleaned_row)
    return cleaned_rows


def clean_heading_hashes(text: str, sec_id: str = "", sec_name: str = "") -> str:
    """Removes redundant section title headers, duplicate subheadings, markdown hashes, and asterisks to keep corporate text plain, clean, and well-structured."""
    if not text:
        return ""
    lines = str(text).split("\n")
    cleaned_lines = []

    sec_id_norm = sec_id.strip().lower() if sec_id else ""
    sec_name_norm = sec_name.strip().lower() if sec_name else ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue

        # Omit lines that repeat the section id or title (e.g. '### 1.9 Introduction' or '1.9: Introduction')
        stripped_clean = re.sub(r'^[#*_\-\s]+', '', stripped).lower()
        if sec_id_norm and (sec_id_norm in stripped_clean):
            if sec_name_norm and any(w in stripped_clean for w in sec_name_norm.split()):
                continue
            if stripped_clean.startswith(sec_id_norm):
                continue
        elif sec_name_norm and (stripped_clean == sec_name_norm or stripped_clean == f"{sec_name_norm}:"):
            continue

        # Convert markdown heading line like '### Heading' or '## Heading:'
        m_head = re.match(r'^#{1,6}\s*(.+)$', stripped)
        if m_head:
            head_txt = m_head.group(1).strip()
            head_txt = re.sub(r'\s*#+$', '', head_txt).strip()
            head_txt = head_txt.replace('*', '').strip()
            if head_txt and not head_txt.endswith(':'):
                head_txt += ':'
            cleaned_lines.append(head_txt)
            continue

        # Convert asterisk or circle bullets to clean dash bullets '- '
        if re.match(r'^\s*[*•▪–]\s+', line):
            bullet_body = re.sub(r'^\s*[*•▪–]\s+', '', line).strip()
            bullet_body = bullet_body.replace('*', '')
            cleaned_lines.append(f"- {bullet_body}")
            continue

        # Strip all asterisks/stars (bold, italic, or stray) completely from the line
        line_clean = line.replace('*', '')

        # Strip any leading markdown hashes if any remained
        line_clean = re.sub(r'^#{1,6}\s*', '', line_clean)

        cleaned_lines.append(line_clean)

    # Deduplicate adjacent / consecutive duplicate headings
    # e.g. "Background Context:" followed by "Background & Context:"
    deduped = []
    for line in cleaned_lines:
        stripped = line.strip()
        if not stripped:
            if deduped and deduped[-1] != "":
                deduped.append("")
            continue

        # Check if line is a short section subheading (ends with ':', under 70 chars, not a bullet or url)
        is_subheading = (stripped.endswith(":") and len(stripped) < 70 and not stripped.startswith("-") and not stripped.startswith("http"))

        if is_subheading and deduped:
            last_line = deduped[-1].strip()
            last_is_subheading = (last_line.endswith(":") and len(last_line) < 70 and not last_line.startswith("-"))
            if last_is_subheading:
                # If two consecutive lines are both headings, check if they refer to the same concept
                words1 = set(re.findall(r'[a-z0-9]+', last_line.lower()))
                words2 = set(re.findall(r'[a-z0-9]+', stripped.lower()))
                if words1 and words2 and (words1 == words2 or words1.issubset(words2) or words2.issubset(words1) or len(words1 & words2) >= 1):
                    # Replace previous duplicate heading with this refined heading
                    deduped[-1] = stripped
                    continue

        deduped.append(line)

    result = "\n".join(deduped).strip()
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


def render_section_preview_html(text: str) -> str:
    """Renders plain process section content as beautifully structured, executive HTML with clean typography, styled headers, and indented bullet lists."""
    import html as html_lib
    if not text:
        return '<div style="color: #94A3B8; font-style: italic;">No content available.</div>'

    lines = [line.strip() for line in str(text).split('\n')]
    html_parts = []
    in_bullet_list = False

    for line in lines:
        if not line:
            if in_bullet_list:
                html_parts.append('</ul>')
                in_bullet_list = False
            continue

        # Check if line is a bullet item (- Item)
        m_bullet = re.match(r'^[-*•▪–]\s*(.+)$', line)
        if m_bullet:
            if not in_bullet_list:
                html_parts.append('<ul style="margin: 6px 0 12px 20px; padding: 0; color: #334155;">')
                in_bullet_list = True
            item_text = html_lib.escape(m_bullet.group(1).strip())
            # Format leading label if present (e.g. Label: Description)
            m_label = re.match(r'^([^:]{2,50}:)\s*(.*)$', item_text)
            if m_label:
                item_html = f'<strong style="color: #0F172A;">{m_label.group(1)}</strong> {m_label.group(2)}'
            else:
                item_html = item_text
            html_parts.append(f'<li style="margin-bottom: 6px; line-height: 1.6; font-size: 13.5px;">{item_html}</li>')
            continue

        if in_bullet_list:
            html_parts.append('</ul>')
            in_bullet_list = False

        # Check if line is a section heading
        is_heading = (line.endswith(':') and len(line) < 70 and not any(line.lower().startswith(p) for p in ['note:', 'e.g.:', 'i.e.:', 'for example:']))
        escaped_line = html_lib.escape(line)
        if is_heading:
            html_parts.append(f'<div style="font-weight: 700; color: #0F172A; font-size: 14.5px; margin-top: 14px; margin-bottom: 5px; letter-spacing: -0.01em;">{escaped_line}</div>')
        else:
            html_parts.append(f'<p style="margin: 0 0 10px 0; line-height: 1.65; color: #334155; font-size: 13.5px;">{escaped_line}</p>')

    if in_bullet_list:
        html_parts.append('</ul>')

    return ''.join(html_parts)


def _build_text_summary_raw(sec_id: str, answers: Dict[str, Any]) -> str:
    """Formats structured questionnaire answers into clean, corporate text for text sections without markdown hashes, stars, or redundant label prefixes."""
    if sec_id == "1.6":
        in_scope = answers.get("in_scope", "All operational activities as detailed in this note.")
        out_scope = answers.get("out_of_scope", "Any external activities not explicitly mentioned.")
        stakeholders = answers.get("stakeholders", "All partner stakeholders.")
        in_scope = re.sub(r'^(?:1\.\s*)?(?:in-scope\s*activities(?:\s*&\s*coverage)?:?)\s*', '', str(in_scope), flags=re.IGNORECASE).strip()
        out_scope = re.sub(r'^(?:2\.\s*)?(?:out-of-scope\s*activities(?:\s*&\s*exclusions)?:?)\s*', '', str(out_scope), flags=re.IGNORECASE).strip()
        stakeholders = re.sub(r'^(?:3\.\s*)?(?:target\s*stakeholders(?:\s*&\s*beneficiaries)?:?)\s*', '', str(stakeholders), flags=re.IGNORECASE).strip()
        return (
            "1. In-Scope Activities & Coverage:\n"
            f"{in_scope}\n\n"
            "2. Out-of-Scope Activities & Exclusions:\n"
            f"{out_scope}\n\n"
            "3. Target Stakeholders & Beneficiaries:\n"
            f"{stakeholders}"
        )

    elif sec_id == "1.9":
        bg = answers.get("background", "Standard operating protocol established for operational excellence.")
        imp = answers.get("importance", "Standardization ensures compliance, transparency, and accountability.")
        # Strip redundant heading prefix if the user already typed or pasted it
        bg = re.sub(r'^(?:background\s*(?:&|and)?\s*context:?|\*{0,2}background\s*(?:&|and)?\s*context:?\*{0,2})\s*', '', str(bg), flags=re.IGNORECASE).strip()
        imp = re.sub(r'^(?:strategic\s*(?:&|and)?\s*(?:operational\s*)?(?:purpose|importance):?|\*{0,2}strategic\s*(?:&|and)?\s*(?:operational\s*)?(?:purpose|importance):?\*{0,2})\s*', '', str(imp), flags=re.IGNORECASE).strip()
        return (
            "Background & Context:\n"
            f"{bg}\n\n"
            "Strategic & Operational Purpose:\n"
            f"{imp}"
        )

    elif sec_id == "1.10":
        obj = answers.get("primary_obj", "To execute operational activities in a timely, compliant manner.")
        outcome = answers.get("measurable_outcome", "Zero-defect delivery and 100% adherence to timelines.")
        obj = re.sub(r'^(?:primary\s*(?:business\s*)?objective:?|\*{0,2}primary\s*(?:business\s*)?objective:?\*{0,2})\s*', '', str(obj), flags=re.IGNORECASE).strip()
        outcome = re.sub(r'^(?:expected\s*measurable\s*outcomes:?|measurable\s*outcomes?:?|\*{0,2}measurable\s*outcomes?:?\*{0,2})\s*', '', str(outcome), flags=re.IGNORECASE).strip()
        return (
            "Primary Business Objective:\n"
            f"{obj}\n\n"
            "Expected Measurable Outcomes:\n"
            f"{outcome}"
        )

    # General fallback
    summary_lines = []
    for k, v in answers.items():
        if v:
            summary_lines.append(f"{k.replace('_', ' ').title()}: {v}")
    return "\n".join(summary_lines)


def build_text_summary_from_answers(sec_id: str, answers: Dict[str, Any]) -> str:
    """Formats structured questionnaire answers into clean, corporate text for text sections, strictly ensuring only & and never &amp;."""
    cleaned_answers = {k: v.replace("&amp;", "&") if isinstance(v, str) else v for k, v in answers.items()}
    res = _build_text_summary_raw(sec_id, cleaned_answers)
    while "&amp;" in res:
        res = res.replace("&amp;", "&")
    return res


def sanitize_rough_text(text: str) -> str:
    """Corrects common rough spelling errors, phonetic typos, and informal punctuation in creator input."""
    if not text:
        return ""
    typo_map = {
        r'\bdrsfts\b': 'drafts',
        r'\bdrsft\b': 'draft',
        r'\bdrft\b': 'draft',
        r'\bdrfts\b': 'drafts',
        r'\bcretion\b': 'creation',
        r'\bdeplyment\b': 'deployment',
        r'\bdeply\b': 'deploy',
        r'\btexting\b': 'testing',
        r'\bteat\b': 'test',
        r'\bmou\b': 'MOU',
        r'\btat\b': 'TAT',
        r'\bkpi\b': 'KPI',
        r'\bsop\b': 'SOP',
    }
    cleaned = str(text).replace("&amp;", "&")
    for pattern, repl in typo_map.items():
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    while "&amp;" in cleaned:
        cleaned = cleaned.replace("&amp;", "&")
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def split_conversational_step(item: str) -> List[str]:
    """Splits multi-action conversational sentences (e.g. 'first they need to create a draft, then move ahead with testing') into clean discrete steps."""
    item = str(item).replace("&amp;", "&")
    parts = re.split(r'\s*(?:,\s*then\s+|;\s*then\s+|\s+then\s+|\s+and\s+then\s+|\s+after\s+that\s+|\s+followed\s+by\s+)\s*', item, flags=re.IGNORECASE)
    cleaned = []
    for p in parts:
        p_clean = p.strip().replace("&amp;", "&")
        p_clean = re.sub(r'^(?:first|second|third|finally|next)\s*(?:,\s*|\s+)?', '', p_clean, flags=re.IGNORECASE)
        p_clean = re.sub(r'^(?:they need to|user needs to|we need to|please|must)\s+', '', p_clean, flags=re.IGNORECASE)
        if p_clean:
            p_clean = p_clean[0].upper() + p_clean[1:]
            p_clean = p_clean.rstrip('.')
            cleaned.append(p_clean)
    return cleaned if cleaned else [item.replace("&amp;", "&")]


def parse_flowchart_steps(code: str) -> Tuple[List[str], List[str]]:
    """Extracts step node labels and decision diamond questions from a Mermaid flowchart string."""
    if not code or not str(code).strip():
        return [], []
    code = str(code).replace("&amp;", "&")
    lines = code.split('\n')
    steps = []
    decisions = []
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith('class') or line_clean.startswith('flowchart') or line_clean.startswith('graph'):
            continue
            
        # Match decision diamonds: DecNode{"Label"} or DecNode{{Label}}
        dec_match = re.search(r'([A-Za-z0-9_]+)\s*\{+[\"]?([^\"\{\}]+)[\"]?\}+', line_clean)
        if dec_match:
            d_label = dec_match.group(2).replace("&amp;", "&").strip()
            if d_label not in decisions:
                decisions.append(d_label)
            continue
            
        # Match regular step boxes: StepId["Label"] or StepId[Label]
        step_match = re.search(r'([A-Za-z0-9_]+)\s*\[+[\"]?([^\"\[\]]+)[\"]?\]+', line_clean)
        if step_match:
            node_id = step_match.group(1)
            s_label = step_match.group(2).replace("&amp;", "&").strip()
            # Ignore Start / End / Appr / Rej standard terminals
            if any(term in node_id.lower() for term in ['start', 'end', 'appr', 'rej']):
                continue
            if s_label not in steps:
                steps.append(s_label)
                
    return steps, decisions


def build_mermaid_flowchart_from_answers(answers: Dict[str, Any]) -> str:
    """Generates a clean Mermaid flowchart with proper process boxes, decision diamonds, and terminal pills."""
    steps_raw = str(answers.get("steps", "")).replace("&amp;", "&").strip()
    decisions_raw = str(answers.get("decisions", "")).replace("&amp;", "&").strip()
    roles = str(answers.get("roles", "")).replace("&amp;", "&").strip()

    lines = ["flowchart TD"]
    lines.append("    Start([Process Start]) --> Step1[\"1. Process Initiation\"]")
    
    raw_items = [s.strip().replace("&amp;", "&") for s in steps_raw.split("\n") if s.strip()]
    if not raw_items:
        raw_items = ["Initial Request Submission", "Document Review & Screening", "Operational Execution & Verification", "Final Sign-off & Delivery"]

    # Flatten and split any multi-action conversational sentences into discrete steps
    step_items = []
    for item in raw_items:
        splits = split_conversational_step(item)
        step_items.extend(splits)

    prev_node = "Step1"
    for idx, item in enumerate(step_items, start=2):
        node_id = f"Step{idx}"
        clean_label = item.replace("[", "").replace("]", "").replace('"', "").replace("&amp;", "&").strip()
        lines.append(f"    {prev_node} --> {node_id}[\"{clean_label}\"]")
        prev_node = node_id

    if decisions_raw:
        clean_dec = decisions_raw.replace('"', "").replace("{", "").replace("}", "").replace("&amp;", "&").strip()
        dec_label = clean_dec if clean_dec else "Decision Criteria Met?"
        lines.append(f"    {prev_node} --> Dec1{{\"{dec_label}\"}}")
        lines.append("    Dec1 -- Yes --> StepAppr[\"Approval & Sign-off\"]")
        lines.append("    Dec1 -- No --> StepRej[\"Rejection & Return with Remarks\"]")
        lines.append("    StepRej -.-> Step1")
        lines.append("    StepAppr --> EndNode([Process End])")
    else:
        lines.append(f"    {prev_node} --> EndNode([Process End])")

    # Add custom node styling classes for high-polish enterprise rendering
    lines.append("    classDef startEnd fill:#DCFCE7,stroke:#16A34A,stroke-width:2px,color:#14532D,font-weight:bold;")
    lines.append("    classDef stepNode fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;")
    lines.append("    classDef decNode fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F,font-weight:bold;")
    lines.append("    classDef apprNode fill:#D1FAE5,stroke:#059669,stroke-width:2px,color:#064E3B;")
    lines.append("    classDef rejNode fill:#FEE2E2,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;")
    lines.append("    class Start,EndNode startEnd;")
    step_nodes = ",".join([f"Step{i}" for i in range(1, len(step_items) + 2)])
    lines.append(f"    class {step_nodes} stepNode;")
    if decisions_raw:
        lines.append("    class Dec1 decNode;")
        lines.append("    class StepAppr apprNode;")
        lines.append("    class StepRej rejNode;")

    res = "\n".join(lines)
    while "&amp;" in res:
        res = res.replace("&amp;", "&")
    return res


# Backward compatibility dictionary
SECTION_GUIDED_QUESTIONS = {
    sec_id: {
        "title": spec["title"],
        "questions": [f["label"] for f in spec["fields"]],
        "placeholder": spec["fields"][0].get("placeholder", "") if spec["fields"] else ""
    }
    for sec_id, spec in SECTION_GUIDED_SPECS.items()
}
