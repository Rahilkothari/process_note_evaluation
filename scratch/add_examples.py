import yaml

examples = {
    '1.1': 'Example: \nName: John Doe | Role: Process Owner | Function: HR Head | Sign: JD | Date: 2023-10-01',
    '1.2': 'Example: \nVersion No.: 1.0 | Effective Date: 2023-10-01 | Change Date: 2023-10-01 | Change Request By: Jane Smith | Change Made By: John Doe | Amendment: Initial Draft',
    '1.3': 'Example: \nSr. No.: 1 | Effective Date: 2023-10-01 | Next Review Date: 2024-10-01 | Process Owner: John Doe | Name: John Doe | Sign: JD',
    '1.4': 'Example: \nProcess / Policy ID: POL-HR-01 | Document Name: Employee Onboarding Policy',
    '1.5': 'Example: \nSr. No.: 1 | Description: Average Onboarding TAT | Owner: HR Ops | Target: < 5 Days | Maker: Recruiter | Checker: HR Manager | Data Source: HRIS | Report Name: Onboarding Metrics | Report Frequency: Monthly | Review Frequency: Quarterly',
    '1.6': 'Example: "This process covers the end-to-end onboarding of full-time employees in the North America region. It excludes contractors and interns."',
    '1.7': 'Example: \nActivity: Candidate accepts offer | Entry Criteria: Signed offer letter uploaded to HRIS',
    '1.8': 'Example: \nActivity: Employee IT setup complete | Exit Criteria: Employee successfully logs into email and core systems',
    '1.9': 'Example: "Effective onboarding is critical to employee retention and productivity. This process outlines the steps to integrate a new hire into the organization."',
    '1.10': 'Example: "To ensure all new employees are fully equipped (IT, payroll, access) and oriented within their first 5 days of joining."',
    '1.11': 'Example: (Upload a Visio or draw.io flowchart showing the step-by-step onboarding journey)',
    '1.12': 'Example: \nSr. No.: 1 | Activity: Background Check | Description: Initiate background verification with 3rd party vendor | Owner/Role: HR Ops | TAT: 2 days',
    '1.13': 'Example: \nRoles: HR Manager | Responsible (R): Yes | Accountable (A): Yes | Consulted (C): No | Informed (I): No | TAT: 5 days',
    '1.14': 'Example: \nSr. No.: 1 | Business Rule: All IT asset requests must be submitted at least 72 hours before the Date of Joining.',
    '1.15': 'Example: \nSr. No.: 1 | Area: Background Check | Exception Description: Vendor delay > 5 days | Exception Mitigation: Conditional joining approved by VP | ...',
    '1.16': 'Example: \nSub Process: IT Setup | Risk Description: Laptop not delivered on day 1 | Root Cause: Late notification to IT | Type: Operational | Risk Impact: Low productivity | Level: Medium | Control Description: Automated trigger from HRIS to IT | Control Frequency: Per hire',
    '1.17': 'Example: \nSub Process: I-9 Verification | Compliance Particulars: Form I-9 must be completed within 3 days of joining | Target Date: Day 3',
    '1.18': 'Example: \nSub Process: Offer Letter | Financial Year: 2023-24 | Document Title: Signed Offer | Criticality: High | Storage Type: Soft copy | Cut-off Period: 1 yr | Retention Period: 7 yrs | Location: N/A | Folder link: /hr/offers',
    '1.19': 'Example: \nAbbreviation: TAT | Definition: Turn-Around Time',
    '1.20': 'Example: \nBest Practice Followed: Digital signatures for offer letters | Envisaged/Planned: Automated Day 1 welcome email | Tentative Timelines: Q4 2023',
    '1.21': 'Example: \nInnovations Implemented: Replaced manual form with self-service HR portal | Envisaged/Planned: AI chatbot for new hire queries | Tentative Timelines: Q1 2024',
    '1.22': 'Example: \nSupplier (Dept): Recruitment | Input: Candidate Details | Key Process Step: Trigger Onboarding | Output: Welcome Email | Customer (Dept): New Hire'
}

def add_examples():
    with open("config/sections.yaml", "r") as f:
        data = yaml.safe_load(f)
        
    for section in data.get("sections", []):
        sec_id = section.get("id")
        if sec_id in examples:
            section["example"] = examples[sec_id]
            
    with open("config/sections.yaml", "w") as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)

if __name__ == "__main__":
    add_examples()
