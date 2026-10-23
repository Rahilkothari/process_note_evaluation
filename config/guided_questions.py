# Guided questions registry for all 22 Process Note sections
# Designed for creators to easily answer questions and auto-generate corporate-grade sections

SECTION_GUIDED_QUESTIONS = {
    "1.1": {
        "title": "Approval Matrix Guided Assistant",
        "questions": [
            "Who is the Process Owner ultimately responsible for this process (Name, Designation, Function)?",
            "Who is the Process Reviewer responsible for verifying the accuracy of this note?",
            "Who is the Process Approver providing final leadership sign-off?"
        ],
        "placeholder": "e.g., Owner: John Doe (Manager, PedTech), Reviewer: Jane Smith (Quality Lead), Approver: Robert Brown (Director, Operations)"
    },
    "1.2": {
        "title": "Document Change History Guided Assistant",
        "questions": [
            "Is this the initial draft (v1.0), or are you revising an existing process note?",
            "If revising, what specific changes or amendments were made and who requested them?"
        ],
        "placeholder": "e.g., Initial version 1.0 created for standardizing school onboarding process."
    },
    "1.3": {
        "title": "Document Review Cycle Guided Assistant",
        "questions": [
            "What is the effective date when this process goes live?",
            "How often must this document be reviewed (e.g. Annually, Every 6 months)?",
            "Who is the designated Process Owner responsible for the review?"
        ],
        "placeholder": "e.g., Effective: 2026-04-01, Review Cycle: Annual (Next Review: 2027-03-31), Owner: Program Head"
    },
    "1.4": {
        "title": "Related Documents Guided Assistant",
        "questions": [
            "What organizational policies, SOPs, templates, or system manuals are linked to this process?",
            "What are their document IDs and official names?"
        ],
        "placeholder": "e.g., SOP-OPS-012: School Partnership Policy, FORM-04: Onboarding Assessment Form"
    },
    "1.5": {
        "title": "Process Performance Parameters / KPIs Guided Assistant",
        "questions": [
            "What measurable KPIs determine whether this process is successful (e.g., Turnaround Time < 48 hrs, Onboarding Accuracy > 95%)?",
            "Who is the Maker and Checker for measuring each KPI?",
            "What is the data source or report used, and how frequently is it reviewed?"
        ],
        "placeholder": "e.g., KPI 1: Onboarding TAT under 5 days, Owner: Manager, Target: 98%, Maker: Field Lead, Checker: Manager, Source: MIS Dashboard, Review: Monthly"
    },
    "1.6": {
        "title": "Process Coverage / Scope Guided Assistant",
        "questions": [
            "What specific activities, programs, teams, or locations are INCLUDED in this process?",
            "What related activities or teams are explicitly EXCLUDED from this process note?"
        ],
        "placeholder": "e.g., INCLUDES: Identification, due diligence, and registration of partner schools across Maharashtra. EXCLUDES: Teacher payroll and curriculum delivery."
    },
    "1.7": {
        "title": "Start Point Guided Assistant",
        "questions": [
            "What specific trigger, event, or incoming request initiates this process?",
            "What entry criteria or prerequisite documents must be available before work begins?"
        ],
        "placeholder": "e.g., Trigger: Receipt of approved School Expansion Plan from Program Director. Entry Criteria: Signed budget authorization and target school list."
    },
    "1.8": {
        "title": "End Point Guided Assistant",
        "questions": [
            "What specific final deliverable or event marks the official conclusion of this process?",
            "What exit criteria must be met before the process is considered complete?"
        ],
        "placeholder": "e.g., Deliverable: Final signed MOU uploaded to ERP. Exit Criteria: Welcome orientation kit delivered and verified by Program Head."
    },
    "1.9": {
        "title": "Introduction Guided Assistant",
        "questions": [
            "What is the background context and organizational necessity for this process?",
            "Why is standardizing this process essential for the organization?"
        ],
        "placeholder": "e.g., Kotak Education Foundation partners with municipal and rural schools. Standardizing onboarding ensures uniform quality, regulatory compliance, and seamless stakeholder alignment."
    },
    "1.10": {
        "title": "Objective Guided Assistant",
        "questions": [
            "What is the single primary objective and measurable business outcome this process aims to achieve?"
        ],
        "placeholder": "e.g., To establish an error-free, timely, and compliant onboarding mechanism for 200+ partner schools within a standard 10-day TAT."
    },
    "1.11": {
        "title": "Process Flowchart Guided Assistant",
        "questions": [
            "What is the sequential journey from start to finish?",
            "What are the major decision points (e.g., If approved -> step X; If rejected -> step Y)?",
            "Which team does each hand-off go to?"
        ],
        "placeholder": "e.g., Step 1: Field Lead submits form -> Step 2: Manager reviews -> Decision: If criteria met, proceed to MOU drafting; If rejected, send back with remarks -> Step 3: MOU signed."
    },
    "1.12": {
        "title": "Process Description Guided Assistant (BE Enterprise Standard)",
        "questions": [
            "1. Major Activities & Sub-steps: What are the main activities from start to finish? Break each major activity down into specific numbered sub-steps.",
            "2. Inputs & Data Sources: What documents, lists, or records are required to start each activity?",
            "3. Tools & Systems: What specific applications, ERP modules, portals, or spreadsheets are used?",
            "4. Stakeholders & Hand-offs: Who does the work, and to which team/role is the outcome handed over?",
            "5. Expected Deliverables: What is the tangible output produced by each activity?",
            "6. Checks & Validations: What approvals, verifications, or quality checks are performed and by whom?"
        ],
        "placeholder": "e.g., Activity: School Due Diligence\n1. Inputs: Gov school registry, application form.\n2. Sub-steps: Verify infrastructure, check teacher ratio, inspect sanitation.\n3. Tools: KEF Field App, Google Sheets.\n4. Stakeholders: Field Officer conducts check, hands report to Program Manager.\n5. Output: Due Diligence Scorecard.\n6. Check: Manager reviews scorecard; must score >80% to qualify."
    },
    "1.13": {
        "title": "RACI Matrix Guided Assistant (Standard Format)",
        "questions": [
            "For each key activity described in Section 1.12:",
            "- What is the Activity Name and brief Description?",
            "- What is the Timeline / TAT?",
            "- Responsible: Which specific job title/designation executes this (e.g. PH, Field Officer)?",
            "- Accountable: Which single designation owns the final sign-off (e.g. Manager, Vertical Lead)?",
            "- Consulted by: Who provides inputs/advice (e.g. Director, Legal)?",
            "- Informed to: Who is kept updated on progress (e.g. CEO Project teams, SCD internal teams)?"
        ],
        "placeholder": "e.g., Activity: School Onboarding Plan | Desc: Location selection and liaison | Timeline: 5 days | R: PH | A: Manager | C: Director | I: CEO Project teams"
    },
    "1.14": {
        "title": "Business Rules Guided Assistant",
        "questions": [
            "What strict operational, financial, or policy rules must NEVER be bypassed?",
            "How is each rule practically enforced in the process (who checks it, when, and using what tool)?"
        ],
        "placeholder": "e.g., Rule 1: No school can be onboarded without an on-ground physical inspection verified by Manager. Rule 2: All translated scripts must pass a peer grammar check before recording."
    },
    "1.15": {
        "title": "Exception & Change Management Guided Assistant",
        "questions": [
            "What potential exceptions or deviations can occur during this process?",
            "How is each exception mitigated, who proposes the deviation, and who has approval authority?"
        ],
        "placeholder": "e.g., Exception: School does not meet standard teacher-student ratio. Mitigation: Special waiver recommendation by PH with justification, approved by Program Director."
    },
    "1.16": {
        "title": "Risk Management Guided Assistant",
        "questions": [
            "What operational, reputational, or compliance risks exist for this process?",
            "What is the root cause, risk impact, risk level (High/Med/Low), and what specific control prevents it?"
        ],
        "placeholder": "e.g., Risk: Inaccurate school student data. Root Cause: Manual entry by school staff. Level: Medium. Control: Mandatory cross-verification against government attendance records every quarter."
    },
    "1.17": {
        "title": "Compliance Management Guided Assistant",
        "questions": [
            "What statutory regulations, child safety/POCSO guidelines, or internal foundation policies apply?",
            "What is the compliance target date or review schedule?"
        ],
        "placeholder": "e.g., POCSO Compliance: Annual background check verification of all on-ground personnel by April 30."
    },
    "1.18": {
        "title": "Data Archival Guided Assistant",
        "questions": [
            "What documents/records must be archived (e.g. MOUs, Inspection reports, Approvals)?",
            "What is the storage type (hard/soft copy folder link), cut-off period, and retention period?"
        ],
        "placeholder": "e.g., Document: Signed School MOUs | Criticality: High | Storage: Soft copy (SharePoint/KEF_MOU_Archive) & Hard copy (Central Operations Cabinet) | Retention: 7 Years"
    },
    "1.19": {
        "title": "Abbreviations & Acronyms Guided Assistant",
        "questions": [
            "What acronyms or technical abbreviations are used in this process note?"
        ],
        "placeholder": "e.g., TAT: Turnaround Time, PH: Program Head, MOU: Memorandum of Understanding, MIS: Management Information System, POCSO: Protection of Children from Sexual Offences"
    },
    "1.20": {
        "title": "Best Practices Summary Guided Assistant",
        "questions": [
            "What industry or internal best practices are currently followed in this process?",
            "What planned best practices are envisaged for future implementation, and by when?"
        ],
        "placeholder": "e.g., Followed: Dual verification of school credentials before agreement. Planned: Automated geo-tagged photo verification on mobile app by Q3 2026."
    },
    "1.21": {
        "title": "Innovations Guided Assistant",
        "questions": [
            "What innovations, digital tools, automation, or process re-engineering have been implemented?",
            "What innovations are planned for the future?"
        ],
        "placeholder": "e.g., Implemented: QR-code based school profile verification. Planned: AI-assisted rubric evaluation for school infrastructure readiness."
    },
    "1.22": {
        "title": "SIPOC Guided Assistant",
        "questions": [
            "Supplier: Who provides the inputs (which internal/external departments)?",
            "Input: What data/materials are received?",
            "Key Process Step: What are the 4-6 primary stages (matching Process Description)?",
            "Output: What products/deliverables are produced?",
            "Customer: Who receives the outputs?"
        ],
        "placeholder": "e.g., Supplier: Education Dept | Input: Approved School List | Process: Eligibility Check, Due Diligence, MOU Signing, Orientation | Output: Active Onboarded School | Customer: Program Delivery Team"
    }
}
