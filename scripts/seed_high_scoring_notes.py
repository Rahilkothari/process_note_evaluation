import os
import sys
from datetime import datetime
import uuid

# Add root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.database import SessionLocal, ProcessNote, ProcessSection, ValidationRun, ValidationFinding
from models.schemas import ProcessNoteSchema, ProcessSectionSchema
from core.validation_engine import ValidationEngine

def get_note_1():
    return {
        "name": "Partner School Onboarding and Infrastructure Verification Workflow",
        "team": "School Education",
        "sme": "Aarav Sharma (Operations Lead)",
        "owner": "Aarav Sharma",
        "status": "APPROVED",
        "sections": [
            {
                "id": "1.1",
                "structured_data": [
                    {"Name": "Aarav Sharma", "Role": "Process Owner", "Function": "Lead - School Operations", "Sign": "AS", "Date": "2026-10-01"},
                    {"Name": "Meera Sen", "Role": "Process Reviewer", "Function": "Lead - Business Excellence & Quality", "Sign": "MS", "Date": "2026-10-02"},
                    {"Name": "Vikramaditya Roy", "Role": "Process Approver", "Function": "Director - Field Programs", "Sign": "VR", "Date": "2026-10-03"}
                ]
            },
            {
                "id": "1.2",
                "structured_data": [
                    {"Version No.": "1.0", "Effective Date": "2026-10-01", "Change Date": "2026-10-01", "Change Request By": "Operations Review Committee", "Change Made By": "Aarav Sharma", "Amendment": "Initial formal baseline release of the comprehensive partner school onboarding, infrastructure inspection, and bilateral agreement execution workflow."}
                ]
            },
            {
                "id": "1.3",
                "structured_data": [
                    {"Effective Date": "2026-10-01", "Next Review Date": "2027-10-01", "Process Owner": "Aarav Sharma", "Name": "Aarav Sharma", "Sign": "AS"}
                ]
            },
            {
                "id": "1.4",
                "structured_data": [
                    {"Process / Policy ID": "POL-SAF-004", "Document Name": "Child Protection, Safeguarding and Safety Guidelines"},
                    {"Process / Policy ID": "SOP-INF-012", "Document Name": "Government School Infrastructure and Lab Facility Standards"},
                    {"Process / Policy ID": "MOU-ORG-001", "Document Name": "State Education Department Bilateral Partnership Agreement"}
                ]
            },
            {
                "id": "1.5",
                "structured_data": [
                    {"Description": "School Onboarding Turnaround Time (TAT from district nomination to final MOU)", "Owner": "Operations Manager", "Target": "Within 14 Business Days", "Maker": "Field Coordinator", "Checker": "Operations Lead", "Data Source": "Operations MIS Tracker", "Report Name": "Monthly Onboarding TAT Dashboard", "Report Frequency": "Monthly", "Review Frequency": "Quarterly"},
                    {"Description": "Infrastructure Readiness and Physical Safety Audit Compliance Rate", "Owner": "Quality Assurance Lead", "Target": ">= 95% Compliance Score", "Maker": "Verification Lead", "Checker": "Quality Assurance Lead", "Data Source": "Mobile Verification Audit App", "Report Name": "Infrastructure Quality & Safety Scorecard", "Report Frequency": "Monthly", "Review Frequency": "Quarterly"}
                ]
            },
            {
                "id": "1.6",
                "content": "This Standard Operating Procedure strictly applies to all government and government-aided secondary schools identified for programmatic adoption across all designated operational districts.\n\n**In-Scope:** Physical site inspection, administrative document verification, headmaster engagement, infrastructure readiness audit, and bilateral partnership MOU execution.\n\n**Explicit Out-of-Scope Exclusions:** This process explicitly excludes private unaided institutions, direct budgetary funding for structural school building renovations, and teacher recruitment or curriculum design governed by state education authorities."
            },
            {
                "id": "1.7",
                "structured_data": [
                    {"Activity": "Receipt of Official District Education Department School Nomination Roster", "Entry Criteria": "Receipt of formal signed nomination letter and authorized list of target schools from District Education Officer (DEO)."}
                ]
            },
            {
                "id": "1.8",
                "structured_data": [
                    {"Activity": "Formal Onboarding Confirmation and MIS Activation", "Exit Criteria": "Bilateral MOU signed by School Headmaster and Director, baseline school profile verified in MIS, and operational welcome kit delivered."}
                ]
            },
            {
                "id": "1.9",
                "content": "Standardizing the partner school onboarding process is critical to establishing robust, transparent, and legally compliant relationships with public educational institutions. Prior to standardization, field teams faced operational inconsistencies in infrastructure assessments, delays in administrative permissions, and variable safety audit standards across districts. This process note establishes institutional rigor by defining verifiable vetting benchmarks, mandatory headmaster engagements, and clear handoffs between field officers and regional management to ensure institutional trust and child safety."
            },
            {
                "id": "1.10",
                "content": "The primary operational objective is to ensure that 100% of newly adopted schools satisfy structural safety, administrative readiness, and legal alignment standards prior to program deployment. Specifically, this process aims to achieve an end-to-end onboarding turnaround time of less than 14 business days, maintain zero safeguarding audit non-conformances, and establish a verified baseline data profile for every participating school in the central MIS."
            },
            {
                "id": "1.11",
                "content": """flowchart TD
    Start([Process Start: District Nomination Received]) --> Step1["1. Administrative Screening & Verification<br/>Owner: Field Coordinator"]
    Step1 --> Step2["2. On-Site Infrastructure & Safety Audit<br/>Owner: Verification Lead"]
    Step2 --> Dec1{"Inspection Criteria Met?"}
    Dec1 -- Yes --> Step3["3. Headmaster Briefing & MOU Drafting<br/>Owner: Operations Manager"]
    Dec1 -- No --> StepRej["Rectification Notice Issued to School Authority"]
    StepRej -.-> Step2
    Step3 --> Step4["4. Bilateral MOU Sign-off & Legal Review<br/>Owner: Operations Manager"]
    Step4 --> Step5["5. MIS Activation & Welcome Kit Dispatch<br/>Owner: MIS Specialist"]
    Step5 --> EndNode([Process End: School Operationalized])
    classDef startEnd fill:#DCFCE7,stroke:#16A34A,stroke-width:2px,color:#14532D,font-weight:bold;
    classDef stepNode fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef decNode fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F,font-weight:bold;
    classDef apprNode fill:#D1FAE5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef rejNode fill:#FEE2E2,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;
    class Start,EndNode startEnd;
    class Dec1 decNode;
    class Step3,Step4,Step5 apprNode;
    class StepRej rejNode;"""
            },
            {
                "id": "1.12",
                "structured_data": [
                    {
                        "Activity": "Administrative Screening & Verification",
                        "Description": "1. Input: District school nomination roster received via official government dispatch. 2. Sub-steps: Verify school registration code (UDISE), student enrollment numbers, and faculty headcount against official state database. 3. Tools: State Education Department Portal and Excel Verification Checklist. 4. Handoff: Submit pre-screening verification dossier to Field Coordinator. 5. Output: Validated candidate school file. 6. Verification: Operations Manager formal review sign-off.",
                        "Owner/Role": "Field Coordinator",
                        "TAT": "2 Business Days"
                    },
                    {
                        "Activity": "On-Site Infrastructure & Safety Audit",
                        "Description": "1. Input: Approved candidate school dossier and inspection scheduling calendar. 2. Sub-steps: Inspect classroom ventilation, power backup, electrical fixtures, student sanitation facilities, and internet connectivity. 3. Tools: Mobile Field Audit Application and Photographic Evidence Upload Tool. 4. Handoff: Transmit geotagged inspection audit scorecard to Quality Assurance Lead. 5. Output: Signed Physical Infrastructure Safety Report. 6. Verification: Quality Assurance Lead evaluates checklist to confirm minimum 95% safety compliance score before issuing formal approval sign-off.",
                        "Owner/Role": "Verification Lead",
                        "TAT": "4 Business Days"
                    },
                    {
                        "Activity": "Headmaster Briefing & MOU Drafting",
                        "Description": "1. Input: Certified Infrastructure Safety Report and standardized institutional MOU template. 2. Sub-steps: Convene formal alignment briefing with School Headmaster and School Management Committee (SMC); populate institutional obligations, resource allocation schedule, and program calendar. 3. Tools: Legal Template Management System. 4. Handoff: Route customized draft agreement to Legal Counsel. 5. Output: Vetted bilateral partnership agreement. 6. Verification: Legal compliance review sign-off.",
                        "Owner/Role": "Operations Manager",
                        "TAT": "3 Business Days"
                    },
                    {
                        "Activity": "Bilateral MOU Sign-off & Execution",
                        "Description": "1. Input: Vetted partnership agreement and institutional authorization documents. 2. Sub-steps: Operations Manager facilitates execution and obtains wet/digital signatures from School Headmaster, SMC President, and Program Director. 3. Tools: Adobe Sign Enterprise Digital Signature Portal. 4. Handoff: Forward fully executed agreement copy to Legal Records Custodian and School Authority. 5. Output: Counter-signed institutional partnership agreement. 6. Verification: Program Director final authorization check.",
                        "Owner/Role": "Operations Manager",
                        "TAT": "3 Business Days"
                    },
                    {
                        "Activity": "MIS Activation & Welcome Kit Dispatch",
                        "Description": "1. Input: Counter-signed bilateral MOU soft copy uploaded to central legal repository and school baseline data. 2. Sub-steps: Verify central repository MOU upload status, activate unique institutional portal profile in central ERP, generate portal login credentials for school staff, and dispatch welcome pedagogical kit. 3. Tools: Central Program MIS Portal and Logistics Tracking System. 4. Handoff: Hand over operational school profile to Regional Program Lead. 5. Output: Active school portal account and delivery confirmation receipt. 6. Verification: MIS Specialist database integrity validation.",
                        "Owner/Role": "MIS Specialist",
                        "TAT": "2 Business Days"
                    }
                ]
            },
            {
                "id": "1.13",
                "structured_data": [
                    {
                        "Sr. No.": 1,
                        "Activity name": "Administrative Screening & Verification",
                        "Activity description": "Verify school registration code (UDISE), student enrollment numbers, and faculty headcount against official state records.",
                        "Timeline": "2 Days",
                        "Responsible": "Field Coordinator",
                        "Accountable": "Operations Manager",
                        "Consulted by": "District Liaison Officer",
                        "Informed to": "Regional Director"
                    },
                    {
                        "Sr. No.": 2,
                        "Activity name": "On-Site Infrastructure & Safety Audit",
                        "Activity description": "Conduct on-ground physical inspection of electrical fixtures, sanitation facilities, classroom safety, and network connectivity.",
                        "Timeline": "4 Days",
                        "Responsible": "Verification Lead",
                        "Accountable": "Quality Assurance Lead",
                        "Consulted by": "Safety Engineer",
                        "Informed to": "Operations Manager"
                    },
                    {
                        "Sr. No.": 3,
                        "Activity name": "Headmaster Briefing & MOU Drafting",
                        "Activity description": "Convene alignment briefing with school authorities and customize bilateral partnership agreement template.",
                        "Timeline": "3 Days",
                        "Responsible": "Operations Manager",
                        "Accountable": "Regional Director",
                        "Consulted by": "Legal Counsel",
                        "Informed to": "District Liaison Officer"
                    },
                    {
                        "Sr. No.": 4,
                        "Activity name": "Bilateral MOU Sign-off & Execution",
                        "Activity description": "Formal execution and counter-signing of bilateral agreement by School Headmaster and Director.",
                        "Timeline": "3 Days",
                        "Responsible": "Operations Manager",
                        "Accountable": "Program Director",
                        "Consulted by": "Legal Counsel",
                        "Informed to": "School Management Committee"
                    },
                    {
                        "Sr. No.": 5,
                        "Activity name": "MIS Activation & Welcome Kit Dispatch",
                        "Activity description": "Provision school portal credentials, activate institutional database profile, and deliver operational toolkit.",
                        "Timeline": "2 Days",
                        "Responsible": "MIS Specialist",
                        "Accountable": "Operations Manager",
                        "Consulted by": "Field Coordinator",
                        "Informed to": "School Headmaster"
                    }
                ]
            },
            {
                "id": "1.14",
                "structured_data": [
                    {"Business Rules": "No school shall be operationalized without an on-site physical infrastructure and child safety audit scoring at least 95% (Enforced by Verification Lead and Quality Assurance Lead in Section 1.12 Step 2)."},
                    {"Business Rules": "Bilateral MOU agreements must receive formal legal counsel vetting before headmaster execution; verbal agreements are strictly prohibited (Enforced by Legal Counsel and Operations Manager in Section 1.12 Step 3)."},
                    {"Business Rules": "School portal login credentials shall only be generated after counter-signed MOU soft copies are uploaded to the central repository (Enforced by MIS Specialist in Section 1.12 Step 5)."}
                ]
            },
            {
                "id": "1.15",
                "structured_data": [
                    {
                        "Area of Exception": "Infrastructure Non-Compliance",
                        "Exception Description": "Target school lacks dedicated functional female sanitation or secure electrical fixtures.",
                        "Exception Mitigation": "Issue conditional 30-day rectification notice to local administration; place onboarding on temporary hold until verified.",
                        "Prop By": "Verification Lead",
                        "Recom By": "Quality Assurance Lead",
                        "Approved By": "Program Director",
                        "Informed to": "School Headmaster",
                        "Remarks": "Zero tolerance on child safety standards; non-negotiable prerequisite."
                    },
                    {
                        "Area of Exception": "Administrative Leadership Transition",
                        "Exception Description": "School Headmaster transferred prior to agreement sign-off.",
                        "Exception Mitigation": "Obtain interim operational endorsement from Assistant Headmaster and secure DEO confirmation within 15 days.",
                        "Prop By": "Field Coordinator",
                        "Recom By": "Operations Manager",
                        "Approved By": "Program Director",
                        "Informed to": "District Education Officer",
                        "Remarks": "Ensures continuity without compromising legal legitimacy."
                    }
                ]
            },
            {
                "id": "1.16",
                "structured_data": [
                    {
                        "Sub Process": "Site Safety Audit",
                        "Risk Description": "Unidentified electrical or structural hazard on school premises during student sessions.",
                        "Root Cause": "Aging infrastructure or incomplete physical inspection.",
                        "Type of Risk": "Operational / Safety",
                        "Risk Impact": "Potential student safety hazard and organizational liability.",
                        "Level of Risk": "High",
                        "Mitigation Control": "Mandatory geotagged photographic audit using calibrated 25-point safety checklist with senior engineer sign-off.",
                        "Owner": "Quality Assurance Lead",
                        "Control Frequency": "Per School Inspection"
                    },
                    {
                        "Sub Process": "Legal Execution",
                        "Risk Description": "Dispute over facility access or intellectual property usage during program execution.",
                        "Root Cause": "Vague clause drafting or unauthorized template modification.",
                        "Type of Risk": "Legal / Compliance",
                        "Risk Impact": "Program suspension or legal grievance.",
                        "Level of Risk": "Medium",
                        "Mitigation Control": "Strict enforcement of locked, immutable legal MOU template with centralized legal review.",
                        "Owner": "Legal Counsel",
                        "Control Frequency": "Per Agreement"
                    }
                ]
            },
            {
                "id": "1.17",
                "structured_data": [
                    {
                        "Compliance Particulars": "Right to Education (RTE) Norms",
                        "Description / Requirement": "Adherence to pupil-teacher ratios and baseline facility norms in adopted schools.",
                        "Authority / Regulation": "Ministry of Education / State RTE Directorate",
                        "Target Date / Frequency": "Annual Verification",
                        "Responsible Role": "Compliance Officer",
                        "Monitoring Mechanism": "Annual statutory compliance review checklist"
                    },
                    {
                        "Compliance Particulars": "POCSO & Child Safeguarding Policy",
                        "Description / Requirement": "Mandatory child protection background verification and code-of-conduct signing for all visiting team members.",
                        "Authority / Regulation": "National Child Protection Policy & Institutional Safeguarding Rubric",
                        "Target Date / Frequency": "Prior to Site Visit",
                        "Responsible Role": "Safeguarding Officer",
                        "Monitoring Mechanism": "HR vetting ledger and signed safeguarding declarations"
                    }
                ]
            },
            {
                "id": "1.18",
                "structured_data": [
                    {
                        "Document / Record Name": "Counter-Signed School Partnership MOUs",
                        "Storage Type": "Hard & Soft Copy",
                        "Storage Location": "Central Legal Fireproof Vault and Cloud DMS",
                        "Retention Period": "7 Years post partnership conclusion",
                        "Cut-off Period": "End of Financial Year",
                        "Archival Custodian": "Legal Records Manager",
                        "Disposal Method": "Secure confidential shredding and certified digital purging"
                    },
                    {
                        "Document / Record Name": "Site Infrastructure Audit Reports & Photographs",
                        "Storage Type": "Soft Copy",
                        "Storage Location": "Secure AWS S3 Encrypted Enterprise Bucket",
                        "Retention Period": "5 Years from audit date",
                        "Cut-off Period": "Quarterly Archival Run",
                        "Archival Custodian": "MIS Lead",
                        "Disposal Method": "Automated cloud lifecycle cold storage archival"
                    }
                ]
            },
            {
                "id": "1.19",
                "structured_data": [
                    {"Abbreviation": "MOU", "Full Form": "Memorandum of Understanding", "Context / Definition": "Formal bilateral agreement defining roles, governance, and resource commitments."},
                    {"Abbreviation": "UDISE", "Full Form": "Unified District Information System for Education", "Context / Definition": "Official school registration database administered by Department of School Education."},
                    {"Abbreviation": "SMC", "Full Form": "School Management Committee", "Context / Definition": "Statutory committee comprising parents, teachers, and local representatives governing school oversight."},
                    {"Abbreviation": "DEO", "Full Form": "District Education Officer", "Context / Definition": "Chief administrative authority for school education within the district jurisdiction."}
                ]
            },
            {
                "id": "1.20",
                "structured_data": [
                    {
                        "Best Practices Followed (suggested list)": "Joint physical inspection alongside School Headmaster and SMC President to ensure collective ownership from Day 1.",
                        "Envisaged/Planned": "Automated geo-fenced mobile check-in for inspection teams with instant audit score computation.",
                        "Tentative Timelines": "Q4 FY 2026-27"
                    },
                    {
                        "Best Practices Followed (suggested list)": "Pre-execution legal vetting workflow to eliminate non-standard contract amendments.",
                        "Envisaged/Planned": "Integration with state education digital repository for real-time UDISE database verification.",
                        "Tentative Timelines": "Q2 FY 2027-28"
                    }
                ]
            },
            {
                "id": "1.21",
                "structured_data": [
                    {
                        "Innovations Implemented": "Digital Mobile Audit Inspection Tool with tamper-proof geotagged photographic upload and automated scoring rubric.",
                        "Envisaged/Planned": "AI-driven optical character recognition (OCR) for automated school registration document verification and background cross-checking.",
                        "TENTATIVE TIMELINES": "Q3 FY 2026-27"
                    },
                    {
                        "Innovations Implemented": "Digital signature integration via enterprise e-sign portal, slashing MOU execution time by 65%.",
                        "Envisaged/Planned": "Predictive school infrastructure readiness score model based on historical district performance datasets.",
                        "TENTATIVE TIMELINES": "Q1 FY 2027-28"
                    }
                ]
            },
            {
                "id": "1.22",
                "structured_data": [
                    {"Supplier (Dept)": "District Education Office", "Input": "Official School Nomination List", "Key Process Step": "Administrative Screening & Verification", "Output": "Validated School Dossier", "Customer (dept)": "Field Operations Team"},
                    {"Supplier (Dept)": "Field Operations Team", "Input": "Candidate School Dossier", "Key Process Step": "On-Site Infrastructure & Safety Audit", "Output": "Certified Safety Audit Scorecard", "Customer (dept)": "Quality Assurance Department"},
                    {"Supplier (Dept)": "Quality Assurance Department", "Input": "Certified Audit Scorecard", "Key Process Step": "Headmaster Briefing & MOU Drafting", "Output": "Vetted Partnership MOU", "Customer (dept)": "School Administration & SMC"},
                    {"Supplier (Dept)": "School Administration & Executive Office", "Input": "Vetted Agreement", "Key Process Step": "Bilateral MOU Sign-off & Execution", "Output": "Counter-Signed Partnership Agreement", "Customer (dept)": "Legal & Records Archive"},
                    {"Supplier (Dept)": "Operations Lead", "Input": "Counter-Signed Agreement", "Key Process Step": "MIS Activation & Welcome Kit Dispatch", "Output": "Active Portal Profile & Deployed Toolkit", "Customer (dept)": "Participating Students & Teachers"}
                ]
            }
        ]
    }

def get_note_2():
    return {
        "name": "Digital Pedagogical Learning Module Creation and Quality Review Workflow",
        "team": "School Education",
        "sme": "Sneha Patil (Lead - Pedagogical Content)",
        "owner": "Sneha Patil",
        "status": "APPROVED",
        "sections": [
            {
                "id": "1.1",
                "structured_data": [
                    {"Name": "Sneha Patil", "Role": "Process Owner", "Function": "Lead - Pedagogical Content & Curriculum", "Sign": "SP", "Date": "2026-10-01"},
                    {"Name": "Arjun Nair", "Role": "Process Reviewer", "Function": "Head - Quality Assurance & Standards", "Sign": "AN", "Date": "2026-10-02"},
                    {"Name": "Dr. Sunita Kulkarni", "Role": "Process Approver", "Function": "Director - Academic Programs", "Sign": "SK", "Date": "2026-10-03"}
                ]
            },
            {
                "id": "1.2",
                "structured_data": [
                    {"Version No.": "1.0", "Effective Date": "2026-10-01", "Change Date": "2026-10-01", "Change Request By": "Academic Advisory Board", "Change Made By": "Sneha Patil", "Amendment": "Initial formal baseline standard operating procedure governing curriculum research, digital learning script drafting, peer review, audio-visual production, and LMS deployment."}
                ]
            },
            {
                "id": "1.3",
                "structured_data": [
                    {"Effective Date": "2026-10-01", "Next Review Date": "2027-10-01", "Process Owner": "Sneha Patil", "Name": "Sneha Patil", "Sign": "SP"}
                ]
            },
            {
                "id": "1.4",
                "structured_data": [
                    {"Process / Policy ID": "POL-PED-001", "Document Name": "National Curriculum Framework (NCF) Alignment Standard"},
                    {"Process / Policy ID": "POL-ACC-003", "Document Name": "Universal Digital Accessibility and Inclusive Learning Guidelines"},
                    {"Process / Policy ID": "SOP-AVP-008", "Document Name": "Audio-Visual Production and Brand Identity Rubric"}
                ]
            },
            {
                "id": "1.5",
                "structured_data": [
                    {"Description": "Digital Module Development Turnaround Time (TAT from curriculum blueprint to LMS release)", "Owner": "Content Operations Lead", "Target": "Within 21 Business Days", "Maker": "Curriculum Specialist", "Checker": "Pedagogy Reviewer", "Data Source": "Content CMS Tracker", "Report Name": "Monthly Digital Production TAT Dashboard", "Report Frequency": "Monthly", "Review Frequency": "Quarterly"},
                    {"Description": "First-Pass Peer Quality & Fact-Check Approval Rate", "Owner": "Quality Review Lead", "Target": ">= 92% Compliance Threshold", "Maker": "Senior Subject Reviewer", "Checker": "Quality Assurance Head", "Data Source": "Content Rubric Scoring System", "Report Name": "Curriculum Quality Audit Scorecard", "Report Frequency": "Monthly", "Review Frequency": "Quarterly"}
                ]
            },
            {
                "id": "1.6",
                "content": "This Standard Operating Procedure strictly applies to all digital learning modules, interactive video scripts, and student practice rubrics developed for secondary grades across regional languages.\n\n**In-Scope:** Curriculum blueprinting, multilingual script translation, instructional design review, studio audio-visual recording, subtitle sync, and final LMS catalog publishing.\n\n**Explicit Out-of-Scope Exclusions:** This process explicitly excludes physical textbook printing, hardware procurement for smart classrooms, and commercial third-party content licensing."
            },
            {
                "id": "1.7",
                "structured_data": [
                    {"Activity": "Receipt of Approved Academic Term Blueprint and Learning Outcomes Matrix", "Entry Criteria": "Formal approval of syllabus learning objectives and competence targets signed by the Director of Academic Programs."}
                ]
            },
            {
                "id": "1.8",
                "structured_data": [
                    {"Activity": "Live LMS Module Publishing and Student Access Verification", "Exit Criteria": "Module uploaded to central LMS catalog, audio-visual quality certified, closed-captioning verified, and formal sign-off issued by Academic Approver."}
                ]
            },
            {
                "id": "1.9",
                "content": "Digital pedagogical modules form the instructional core of blended learning classrooms, reaching over 250,000 students across regional school networks. In the absence of a standardized creation workflow, content developers experienced inconsistent tone, formatting deviations, delayed subject-matter reviews, and accessibility gaps in multimedia assets. Establishing this end-to-end SOP ensures strict pedagogical rigor, factual accuracy, inclusive accessibility standards, and streamlined multi-tier sign-offs prior to public release."
            },
            {
                "id": "1.10",
                "content": "The operational objective is to deliver 100% curriculum-compliant, inclusive, and high-engagement digital learning assets within an established 21-day production cycle. Specifically, the workflow enforces a minimum 92% first-pass quality rating, achieves full adherence to WCAG 2.1 digital accessibility standards (subtitles and screen-reader compatibility), and maintains zero factual non-conformances in deployed modules."
            },
            {
                "id": "1.11",
                "content": """flowchart TD
    Start([Process Start: Curriculum Blueprint Approved]) --> Step1["1. Instructional Scripting & Localization<br/>Owner: Curriculum Specialist"]
    Step1 --> Step2["2. Pedagogical & Fact-Check Review<br/>Owner: Senior Subject Reviewer"]
    Step2 --> Dec1{"Quality Rubric Criteria Met?"}
    Dec1 -- Yes --> Step3["3. Multimedia Recording & Production<br/>Owner: Media Production Lead"]
    Dec1 -- No --> StepRej["Script Returned for Pedagogical Revision"]
    StepRej -.-> Step1
    Step3 --> Step4["4. Quality Assurance & Accessibility Audit<br/>Owner: Quality Assurance Specialist"]
    Step4 --> Step5["5. LMS Catalog Upload & Release Sign-off<br/>Owner: LMS Operations Specialist"]
    Step5 --> EndNode([Process End: Module Live on LMS])
    classDef startEnd fill:#DCFCE7,stroke:#16A34A,stroke-width:2px,color:#14532D,font-weight:bold;
    classDef stepNode fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef decNode fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F,font-weight:bold;
    classDef apprNode fill:#D1FAE5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef rejNode fill:#FEE2E2,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;
    class Start,EndNode startEnd;
    class Dec1 decNode;
    class Step3,Step4,Step5 apprNode;
    class StepRej rejNode;"""
            },
            {
                "id": "1.12",
                "structured_data": [
                    {
                        "Activity": "Instructional Scripting & Localization",
                        "Description": "1. Input: Approved curriculum syllabus blueprint and pedagogical rubric standards. 2. Sub-steps: Draft concept explanations, create narrative analogies, incorporate formative quiz prompts, and translate into regional languages. 3. Tools: Content Management System (CMS) and Multilingual Lexicon Dictionary. 4. Handoff: Submit drafted instructional script to Senior Subject Reviewer. 5. Output: Complete lesson script and storyboard draft. 6. Verification: Curriculum Specialist self-review checklist.",
                        "Owner/Role": "Curriculum Specialist",
                        "TAT": "5 Business Days"
                    },
                    {
                        "Activity": "Pedagogical & Fact-Check Review",
                        "Description": "1. Input: Drafted lesson script and syllabus learning outcomes matrix. 2. Sub-steps: Audit factual accuracy, verify scientific notation, review age-appropriate language, and evaluate rubrics against NCF standards. 3. Tools: Peer Review Assessment Rubric Portal. 4. Handoff: Route approved script to Media Production Lead. 5. Output: Certified and vetted production-ready script. 6. Verification: Senior Subject Reviewer formal sign-off.",
                        "Owner/Role": "Senior Subject Reviewer",
                        "TAT": "4 Business Days"
                    },
                    {
                        "Activity": "Multimedia Recording & Production",
                        "Description": "1. Input: Certified lesson script, graphic assets, and voiceover guidelines. 2. Sub-steps: Record studio audio narration, animate pedagogical diagrams, edit video timeline, and synchronize closed captions. 3. Tools: DaVinci Resolve Studio and Adobe Creative Cloud Suite. 4. Handoff: Transmit raw compiled MP4 media files to Quality Assurance Specialist. 5. Output: High-definition interactive video module. 6. Verification: Media Production Lead technical check.",
                        "Owner/Role": "Media Production Lead",
                        "TAT": "6 Business Days"
                    },
                    {
                        "Activity": "Quality Assurance & Accessibility Audit",
                        "Description": "1. Input: Compiled video module and WCAG 2.1 digital accessibility criteria. 2. Sub-steps: Verify audio loudness levels (-14 LUFS), validate subtitle synchronization, test screen-reader metadata, and conduct student comprehension beta test. 3. Tools: Automated Accessibility Scanner and Audio Metering Software. 4. Handoff: Forward verified asset package to LMS Operations Specialist. 5. Output: Certified Quality and Accessibility Audit Report. 6. Verification: Quality Assurance Specialist compliance endorsement.",
                        "Owner/Role": "Quality Assurance Specialist",
                        "TAT": "3 Business Days"
                    },
                    {
                        "Activity": "LMS Catalog Upload & Release Sign-off",
                        "Description": "1. Input: Certified Quality and Accessibility Audit Report and master video module file. 2. Sub-steps: Verify that the signed Quality Audit Report is cataloged in the repository, upload SCORM/MP4 package to LMS, configure grade tags, conduct sandbox playback verification, and publish live to students. 3. Tools: Enterprise Learning Management System (Moodle/Open edX). 4. Handoff: Notify Regional Academic Coordinators of live release. 5. Output: Active public module URL and LMS enrollment index. 6. Verification: LMS Operations Specialist formal publishing confirmation.",
                        "Owner/Role": "LMS Operations Specialist",
                        "TAT": "3 Business Days"
                    }
                ]
            },
            {
                "id": "1.13",
                "structured_data": [
                    {
                        "Sr. No.": 1,
                        "Activity name": "Instructional Scripting & Localization",
                        "Activity description": "Draft lesson scripts, formative assessment questions, and storyboards aligned with curriculum objectives.",
                        "Timeline": "5 Days",
                        "Responsible": "Curriculum Specialist",
                        "Accountable": "Pedagogy Content Lead",
                        "Consulted by": "Language Linguist",
                        "Informed to": "Media Production Lead"
                    },
                    {
                        "Sr. No.": 2,
                        "Activity name": "Pedagogical & Fact-Check Review",
                        "Activity description": "Review factual accuracy, age appropriateness, and curriculum benchmark adherence.",
                        "Timeline": "4 Days",
                        "Responsible": "Senior Subject Reviewer",
                        "Accountable": "Pedagogy Content Lead",
                        "Consulted by": "Subject Matter Expert",
                        "Informed to": "Curriculum Specialist"
                    },
                    {
                        "Sr. No.": 3,
                        "Activity name": "Multimedia Recording & Production",
                        "Activity description": "Record audio narration, produce motion graphics, and assemble video cuts.",
                        "Timeline": "6 Days",
                        "Responsible": "Media Production Lead",
                        "Accountable": "Media Production Lead",
                        "Consulted by": "Instructional Designer",
                        "Informed to": "Quality Assurance Specialist"
                    },
                    {
                        "Sr. No.": 4,
                        "Activity name": "Quality Assurance & Accessibility Audit",
                        "Activity description": "Perform audio-visual quality inspection, subtitle sync checks, and accessibility compliance verification.",
                        "Timeline": "3 Days",
                        "Responsible": "Quality Assurance Specialist",
                        "Accountable": "Quality Assurance Head",
                        "Consulted by": "Accessibility Expert",
                        "Informed to": "LMS Operations Specialist"
                    },
                    {
                        "Sr. No.": 5,
                        "Activity name": "LMS Catalog Upload & Release Sign-off",
                        "Activity description": "Deploy SCORM package on LMS, conduct playback smoke testing, and publish live to school cohorts.",
                        "Timeline": "3 Days",
                        "Responsible": "LMS Operations Specialist",
                        "Accountable": "Academic Programs Director",
                        "Consulted by": "Curriculum Specialist",
                        "Informed to": "School Teachers"
                    }
                ]
            },
            {
                "id": "1.14",
                "structured_data": [
                    {"Business Rules": "All scripts must pass double-blind peer fact-checking scoring >= 90% before studio recording is scheduled (Enforced by Senior Subject Reviewer in Section 1.12 Step 2)."},
                    {"Business Rules": "Closed caption subtitles in the primary delivery language are mandatory for 100% of video content to ensure universal accessibility (Enforced by Quality Assurance Specialist in Section 1.12 Step 4)."},
                    {"Business Rules": "No module shall be published live to students without a verified Quality and Accessibility Audit Report signed by the QA Head on file (Enforced by LMS Operations Specialist in Section 1.12 Step 5)."}
                ]
            },
            {
                "id": "1.15",
                "structured_data": [
                    {
                        "Area of Exception": "Curriculum Discrepancy",
                        "Exception Description": "Fact-checking reveals an ambiguity or state board curriculum conflict in syllabus source material.",
                        "Exception Mitigation": "Convene rapid Academic Advisory Review Panel within 48 hours to issue an authoritative clarification memorandum.",
                        "Prop By": "Senior Subject Reviewer",
                        "Recom By": "Pedagogy Content Lead",
                        "Approved By": "Director of Academic Programs",
                        "Informed to": "Curriculum Specialist",
                        "Remarks": "All changes logged in syllabus version repository."
                    },
                    {
                        "Area of Exception": "Audio Narration Studio Failure",
                        "Exception Description": "Voice recording equipment failure or talent unavailability exceeding 48 hours.",
                        "Exception Mitigation": "Switch to pre-cleared backup studio roster and utilize certified professional freelance narrators.",
                        "Prop By": "Media Production Lead",
                        "Recom By": "Content Operations Lead",
                        "Approved By": "Director of Academic Programs",
                        "Informed to": "Curriculum Specialist",
                        "Remarks": "Maintains 21-day delivery SLA without compromising sound fidelity."
                    }
                ]
            },
            {
                "id": "1.16",
                "structured_data": [
                    {
                        "Sub Process": "Curriculum Scripting",
                        "Risk Description": "Factual error or outdated conceptual formula published in student video lessons.",
                        "Root Cause": "Insufficient source validation or unverified third-party references.",
                        "Type of Risk": "Academic / Reputational",
                        "Risk Impact": "Loss of educational credibility, negative student feedback, and regulatory censure.",
                        "Level of Risk": "High",
                        "Mitigation Control": "Mandatory 3-step fact-verification protocol cross-referenced with NCERT standard reference volumes.",
                        "Owner": "Senior Subject Reviewer",
                        "Control Frequency": "Every Module Script"
                    },
                    {
                        "Sub Process": "Multimedia Production",
                        "Risk Description": "Copyright infringement or unlicensed intellectual property usage in graphic illustrations.",
                        "Root Cause": "Use of unauthorized internet image assets without commercial release licenses.",
                        "Type of Risk": "Legal / Financial",
                        "Risk Impact": "Copyright infringement lawsuits and required withdrawal of published content.",
                        "Level of Risk": "High",
                        "Mitigation Control": "Strict policy mandating custom vector art created in-house or purchased from licensed enterprise asset banks with clearance IDs.",
                        "Owner": "Media Production Lead",
                        "Control Frequency": "Per Media Asset"
                    }
                ]
            },
            {
                "id": "1.17",
                "structured_data": [
                    {
                        "Compliance Particulars": "National Education Policy (NEP 2020) Standards",
                        "Description / Requirement": "Incorporation of competency-based learning and experiential pedagogical rubrics.",
                        "Authority / Regulation": "Ministry of Education / NCERT",
                        "Target Date / Frequency": "Per Curriculum Cycle",
                        "Responsible Role": "Academic Compliance Lead",
                        "Monitoring Mechanism": "Curriculum standards review matrix"
                    },
                    {
                        "Compliance Particulars": "Rights of Persons with Disabilities (RPwD) Act & WCAG 2.1",
                        "Description / Requirement": "Mandatory provision of subtitles, high-contrast visual assets, and accessible digital text formats.",
                        "Authority / Regulation": "Department of Empowerment of Persons with Disabilities",
                        "Target Date / Frequency": "Every Release",
                        "Responsible Role": "Accessibility Specialist",
                        "Monitoring Mechanism": "Automated WCAG accessibility audit checklists"
                    }
                ]
            },
            {
                "id": "1.18",
                "structured_data": [
                    {
                        "Document / Record Name": "Approved Lesson Scripts, Storyboards, and QA Checklists",
                        "Storage Type": "Soft Copy (Cloud DMS)",
                        "Storage Location": "Enterprise Content Repository with Version Control",
                        "Retention Period": "10 Years from publishing date",
                        "Cut-off Period": "End of Academic Year",
                        "Archival Custodian": "Content Operations Lead",
                        "Disposal Method": "Automated cloud archival to cold tier storage"
                    },
                    {
                        "Document / Record Name": "Master Audio-Visual Production Project Files (.prproj, .aep, WAV)",
                        "Storage Type": "Soft Copy (Nearline Cloud)",
                        "Storage Location": "Dedicated AWS Glacier Archive Bucket",
                        "Retention Period": "5 Years from release",
                        "Cut-off Period": "Quarterly Archival Run",
                        "Archival Custodian": "Media Production Lead",
                        "Disposal Method": "Cryptographic digital purging upon policy review"
                    }
                ]
            },
            {
                "id": "1.19",
                "structured_data": [
                    {"Abbreviation": "NCF", "Full Form": "National Curriculum Framework", "Context / Definition": "Apex guidelines for school curriculum design issued by NCERT."},
                    {"Abbreviation": "LMS", "Full Form": "Learning Management System", "Context / Definition": "Digital delivery platform hosting interactive learning courses and quizzes."},
                    {"Abbreviation": "SCORM", "Full Form": "Sharable Content Object Reference Model", "Context / Definition": "Standardized technical specification for e-learning software products."},
                    {"Abbreviation": "WCAG", "Full Form": "Web Content Accessibility Guidelines", "Context / Definition": "International technical benchmarks for digital accessibility."}
                ]
            },
            {
                "id": "1.20",
                "structured_data": [
                    {
                        "Best Practices Followed (suggested list)": "Interactive micro-learning segments (3 to 5 minutes duration) with embedded checkpoint quizzes to maximize student retention.",
                        "Envisaged/Planned": "AI-assisted automated subtitle translation and voice dubbing into additional regional dialects.",
                        "Tentative Timelines": "Q4 FY 2026-27"
                    },
                    {
                        "Best Practices Followed (suggested list)": "Collaborative script co-creation between academic teachers and professional media animators.",
                        "Envisaged/Planned": "Real-time student video drop-off heatmap analytics integrated directly into teacher dashboard.",
                        "Tentative Timelines": "Q2 FY 2027-28"
                    }
                ]
            },
            {
                "id": "1.21",
                "structured_data": [
                    {
                        "Innovations Implemented": "Automated WCAG 2.1 digital accessibility testing scanner integrated into the pre-release CI/CD content pipeline.",
                        "Envisaged/Planned": "Generative AI synthetic voice cloning for regional language vernacular adaptations with native pronunciation.",
                        "TENTATIVE TIMELINES": "Q3 FY 2026-27"
                    },
                    {
                        "Innovations Implemented": "Cloud-based collaborative video review player with frame-accurate timestamp commenting for pedagogical reviewers.",
                        "Envisaged/Planned": "Adaptive student assessment engine adjusting quiz difficulty based on video engagement telemetry.",
                        "TENTATIVE TIMELINES": "Q1 FY 2027-28"
                    }
                ]
            },
            {
                "id": "1.22",
                "structured_data": [
                    {"Supplier (Dept)": "Academic Advisory Board", "Input": "Curriculum Syllabus Blueprint", "Key Process Step": "Instructional Scripting & Localization", "Output": "Draft Storyboards and Scripts", "Customer (dept)": "Pedagogy Review Team"},
                    {"Supplier (Dept)": "Pedagogy Content Team", "Input": "Draft Scripts", "Key Process Step": "Pedagogical & Fact-Check Review", "Output": "Certified Production Script", "Customer (dept)": "Media Production Department"},
                    {"Supplier (Dept)": "Media Production Team", "Input": "Certified Script", "Key Process Step": "Multimedia Recording & Production", "Output": "High-Definition Video Module", "Customer (dept)": "Quality Assurance Team"},
                    {"Supplier (Dept)": "Quality Assurance Department", "Input": "Compiled Video Module", "Key Process Step": "Quality Assurance & Accessibility Audit", "Output": "Certified Quality Audit Report", "Customer (dept)": "LMS Operations Team"},
                    {"Supplier (Dept)": "LMS Operations Team", "Input": "Certified Video Package", "Key Process Step": "LMS Catalog Upload & Release Sign-off", "Output": "Live Module on LMS Catalog", "Customer (dept)": "School Students and Teachers"}
                ]
            }
        ]
    }

def seed_both():
    db = SessionLocal()
    engine = ValidationEngine()
    
    notes_data = [get_note_1(), get_note_2()]
    
    for ndata in notes_data:
        print(f"\n=======================================================")
        print(f"Processing '{ndata['name']}'...")
        print(f"=======================================================")
        
        existing = db.query(ProcessNote).filter(ProcessNote.process_name == ndata['name']).first()
        if existing:
            db.query(ValidationFinding).filter(ValidationFinding.process_name == ndata['name']).delete()
            db.query(ValidationRun).filter(ValidationRun.process_note_id == existing.id).delete()
            db.query(ProcessSection).filter(ProcessSection.process_note_id == existing.id).delete()
            note = existing
            note.team = ndata['team']
            note.subject_matter_expert = ndata['sme']
            note.process_owner = ndata['owner']
            note.status = ndata['status']
            db.commit()
        else:
            note = ProcessNote(
                document_id=f"PN-{uuid.uuid4().hex[:6].upper()}",
                process_name=ndata['name'],
                team=ndata['team'],
                version=1.0,
                subject_matter_expert=ndata['sme'],
                process_owner=ndata['owner'],
                status=ndata['status'],
                created_at=datetime.utcnow()
            )
            db.add(note)
            db.commit()
            db.refresh(note)

        sec_schemas = []
        for s in ndata['sections']:
            ps = ProcessSection(
                process_note_id=note.id,
                process_name=note.process_name,
                section_id=s['id'],
                content=s.get('content', ''),
                structured_data=s.get('structured_data', [])
            )
            db.add(ps)
            sec_schemas.append(ProcessSectionSchema(
                section_id=s['id'],
                content=s.get('content', ''),
                structured_data=s.get('structured_data', [])
            ))
        db.commit()

        print(f"Running validation on '{note.process_name}'...")
        payload = ProcessNoteSchema(
            process_name=note.process_name,
            team=note.team,
            version=note.version,
            sections=sec_schemas
        )
        result = engine.run_validation(payload)
        print(f"\n>>> FINAL RESULT FOR '{note.process_name}':")
        print(f"    SCORE = {result.overall_score}%")
        print(f"    STATUS = {result.overall_status}")
        print(f"    PASSED SECTIONS = {result.sections_passed} / {len(result.section_results)}")
        print(f"    CRITICAL ISSUES = {result.critical_issues}")
        print(f"    WARNINGS = {result.warnings}")

        vrun = ValidationRun(
            process_note_id=note.id,
            process_name=note.process_name,
            overall_score=result.overall_score,
            status=result.overall_status,
            model_used="gemini-1.5-pro",
            timestamp=datetime.utcnow()
        )
        db.add(vrun)
        db.commit()
        db.refresh(vrun)

        for res in result.section_results:
            finding = ValidationFinding(
                validation_id=vrun.id,
                process_name=note.process_name,
                section_id=res.section,
                severity=res.severity,
                status=res.status,
                score=res.score,
                issue="; ".join(res.issues) if res.issues else None,
                recommendation="; ".join(res.recommendations) if res.recommendations else None,
                is_cross_section=0
            )
            db.add(finding)

        for cr in result.cross_section_issues:
            finding = ValidationFinding(
                validation_id=vrun.id,
                process_name=note.process_name,
                section_id=f"Cross-Section ({' & '.join(cr.get('related_sections', []))})",
                severity=cr.get("severity", "MEDIUM"),
                status="NEEDS_REVISION" if cr.get("severity") == "HIGH" else "WARNING",
                score=0.0 if cr.get("severity") == "HIGH" else 50.0,
                issue=cr.get("issue"),
                recommendation="Ensure operational alignment across sections.",
                is_cross_section=1
            )
            db.add(finding)

        note.status = result.overall_status
        db.commit()

    print("\nAll process notes successfully generated, validated, and persisted in database!")
    db.close()

if __name__ == "__main__":
    seed_both()
