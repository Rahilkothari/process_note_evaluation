import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import re
from models.schemas import SectionValidationResult

class LLMProvider(ABC):
    @abstractmethod
    def validate_section(self, section_content: str, section_rules: Dict[str, Any], global_rules: Dict[str, Any] = None, team_name: str = "") -> SectionValidationResult:
        pass

    @abstractmethod
    def validate_cross_sections(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def generate_suggestion(self, section_rules: Dict[str, Any], context_list: List[str], user_draft: str = "") -> str:
        pass

    @abstractmethod
    def generate_flowchart_mermaid(self, process_description_steps: List[Dict[str, Any]]) -> str:
        pass

    @abstractmethod
    def assist_flowchart(self, draft_steps: str, decisions: str = "", roles: str = "", process_name: str = "", team_name: str = "") -> str:
        pass

    @abstractmethod
    def generate_section_from_qa(self, section_id: str, section_config: Dict[str, Any], user_answers: str, team_name: str = "") -> Any:
        pass

    @abstractmethod
    def refine_table_rows_with_ai(
        self,
        section_id: str,
        section_config: Dict[str, Any],
        raw_rows: List[Dict[str, Any]],
        answers_dict: Dict[str, Any] = None,
        process_name: str = "",
        team_name: str = ""
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def resolve_clarification(self, section_id: str, section_type: str, current_content: Any, question: str, answer: str) -> Any:
        pass


class MockProvider(LLMProvider):
    def validate_section(self, section_content: str, section_rules: Dict[str, Any], global_rules: Dict[str, Any] = None, team_name: str = "") -> SectionValidationResult:
        content_lower = section_content.lower()
        issues = []
        recommendations = []
        questions = []
        status = "PASS"
        score = 100.0
        severity = "LOW"
        sec_id = section_rules.get("id", "")

        # Check generic filler
        if "very important" in content_lower or "operational excellence" in content_lower:
            issues.append("Contains generic or filler language without specific operational procedures.")
            recommendations.append("Remove generic statements and detail the exact activities and tools used.")
            status = "WARNING"
            score = 50.0
            severity = "MEDIUM"

        content_words = len(section_content.split())

        if len(section_content.strip()) < 15 and not section_rules.get("allow_short", False):
            issues.append("Response is too brief to adequately document enterprise operational procedures.")
            recommendations.append("Expand the section with complete operational details.")
            questions.append("Can you provide the step-by-step breakdown and tools used for this section?")
            status = "NEEDS_REVISION"
            score = 0.0
            severity = "HIGH"

        # Specific mock checks for 1.10 Objective: Must have substance & measurable outcomes
        elif sec_id == "1.10":
            if content_words < 20:
                issues.append(f"Objective is too brief ({content_words} words). A professional process note objective must state the operational purpose and measurable business outcomes.")
                recommendations.append("Expand the objective to specify tangible benchmarks (e.g., TAT targets, accuracy thresholds, compliance goals).")
                questions.append("What specific measurable outcome or performance benchmark determines success for this process?")
                status = "WARNING"
                score = 50.0
                severity = "MEDIUM"
            elif not any(term in content_lower for term in ["target", "outcome", "ensure", "achieve", "deliver", "%", "tat", "timeline", "standard", "quality", "compliant"]):
                issues.append("Objective lacks tangible, measurable performance targets or business outcomes.")
                recommendations.append("Include quantitative benchmarks (e.g., TAT <= 5 days, 98% accuracy) to define success.")
                questions.append("What is the exact target turnaround time or quality threshold for this objective?")
                status = "WARNING"
                score = 50.0
                severity = "MEDIUM"

        # Specific mock checks for 1.9 Introduction: Must have background & rationale
        elif sec_id == "1.9":
            if content_words < 25:
                issues.append(f"Introduction is too brief ({content_words} words). Must articulate organizational context and the rationale for standardizing this process.")
                recommendations.append("Provide context on why this process exists and what operational challenges or risks standardization solves.")
                questions.append("What organizational necessity or operational risk led to the standardization of this process?")
                status = "WARNING"
                score = 50.0
                severity = "MEDIUM"

        # Specific mock checks for 1.6 Process Coverage / Scope: Must have boundaries & exclusions
        elif sec_id == "1.6":
            if content_words < 20 or not any(term in content_lower for term in ["exclude", "out-of-scope", "out of scope", "not cover", "boundary"]):
                issues.append("Process Coverage / Scope must explicitly specify operational boundaries, including what is explicitly OUT-OF-SCOPE.")
                recommendations.append("Add a distinct 'Out-of-Scope / Exclusions' section specifying activities not covered.")
                questions.append("What related activities, programs, or stakeholder tasks are explicitly excluded from this process note?")
                status = "WARNING"
                score = 50.0
                severity = "MEDIUM"

        # Specific mock check for 1.12 Process Description
        elif sec_id == "1.12":
            if "input" not in content_lower and "tool" not in content_lower and "check" not in content_lower:
                issues.append("Process Description lacks explicit details on data inputs, tools/systems used, and verification checks.")
                recommendations.append("Document: 1) Data inputs, 2) Tools/systems, 3) Hand-offs, 4) Deliverables, 5) Approval checks.")
                questions.append("What specific applications, systems, or portals are used at each stage of this activity?")
                questions.append("Who performs quality/validation checks on the output before handoff?")
                if status == "PASS":
                    status = "WARNING"
                    score = 50.0
                    severity = "MEDIUM"

        return SectionValidationResult(
            section=section_rules.get("name", "Unknown Section"),
            status=status,
            score=score,
            issues=issues,
            recommendations=recommendations,
            questions=questions,
            severity=severity
        )

    def validate_cross_sections(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cross_issues = []
        desc_sec = next((s for s in all_sections if s.get("section_id") == "1.12"), None)
        raci_sec = next((s for s in all_sections if s.get("section_id") == "1.13"), None)
        rules_sec = next((s for s in all_sections if s.get("section_id") == "1.14"), None)
        kpi_sec = next((s for s in all_sections if s.get("section_id") == "1.5"), None)

        desc_data = desc_sec.get("structured_data") if desc_sec else []
        raci_data = raci_sec.get("structured_data") if raci_sec else []
        rules_data = rules_sec.get("structured_data") if rules_sec else []

        # 1. Check Rules vs Process Description
        if rules_data and desc_data:
            desc_text = " ".join([str(r.get("Description", "")) + " " + str(r.get("Activity", "")) for r in desc_data]).lower()
            for r in rules_data:
                rule_text = str(r.get("Business Rules", r.get("Business Rule", ""))).strip()
                if "check" in rule_text.lower() or "verify" in rule_text.lower() or "approv" in rule_text.lower() or "grammar" in rule_text.lower():
                    # check if mentioned in desc
                    keywords = [w for w in ["check", "grammar", "approv", "inspect", "sign-off", "audit"] if w in rule_text.lower()]
                    if keywords and not any(kw in desc_text for kw in keywords):
                        cross_issues.append({
                            "issue": f"Business Rule '{rule_text}' requires a verification/control step, but no corresponding check is documented in Section 1.12 (Process Description).",
                            "severity": "HIGH",
                            "questions": [f"Who performs the '{rule_text}' check in practice, what tools/rubrics do they use, and how is it documented?"],
                            "related_sections": ["1.12", "1.14"]
                        })

        # 2. Check RACI vs Process Description
        if desc_data and raci_data:
            desc_acts = [str(r.get("Activity", "")).strip().lower() for r in desc_data if r.get("Activity")]
            raci_acts = [str(r.get("Activity name", r.get("Activity", ""))).strip().lower() for r in raci_data if r.get("Activity name") or r.get("Activity")]
            missing = [a for a in desc_acts if not any(a in ra or ra in a for ra in raci_acts)]
            if missing:
                cross_issues.append({
                    "issue": f"Activities from Section 1.12 are missing in the RACI Matrix (1.13): {', '.join(missing[:3])}.",
                    "severity": "MEDIUM",
                    "questions": [f"Please assign Responsible, Accountable, Consulted, and Informed designations for: {', '.join(missing[:3])}."],
                    "related_sections": ["1.12", "1.13"]
                })

        return cross_issues

    def generate_suggestion(self, section_rules: Dict[str, Any], context_list: List[str], user_draft: str = "") -> str:
        return f"Enterprise suggestion for {section_rules.get('name')}: Standard procedure with clear inputs, owner designations, and verification steps."

    def generate_flowchart_mermaid(self, process_description_steps: List[Dict[str, Any]]) -> str:
        if not process_description_steps:
            return "graph TD\n    A[Start Process] --> B[Execute Activity] --> C[End Process]"
        lines = ["graph TD"]
        for idx, step in enumerate(process_description_steps, start=1):
            act = str(step.get("Activity", f"Activity {idx}")).replace('"', '').replace('[', '(').replace(']', ')')
            owner = str(step.get("Owner/Role", "")).replace('"', '')
            label = f"{act} ({owner})" if owner else act
            lines.append(f"    S{idx}[\"{label}\"]")
            if idx > 1:
                lines.append(f"    S{idx-1} --> S{idx}")
        return "\n".join(lines)

    def assist_flowchart(self, draft_steps: str, decisions: str = "", roles: str = "", process_name: str = "", team_name: str = "") -> str:
        from config.guided_questions import split_conversational_step
        lines = ["flowchart TD"]
        lines.append("    Start([Process Start]) --> Step1[\"1. Process Initiation\"]")
        raw_items = [s.strip() for s in draft_steps.split("\n") if s.strip()]
        if not raw_items:
            raw_items = ["Initial Request Submission", "Document Review & Screening", "Operational Execution & Verification", "Final Sign-off & Delivery"]
        
        step_items = []
        for it in raw_items:
            step_items.extend(split_conversational_step(it))

        prev = "Step1"
        for i, s in enumerate(step_items, start=2):
            node_id = f"Step{i}"
            clean = s.replace('"', '').replace('[', '').replace(']', '')
            lines.append(f"    {prev} --> {node_id}[\"{clean}\"]")
            prev = node_id
        dec = decisions.strip() if decisions.strip() else "Verification Criteria Met?"
        lines.append(f"    {prev} --> Dec1{{\"{dec}\"}}")
        lines.append("    Dec1 -- Yes --> StepAppr[\"Approval & Sign-off\"]")
        lines.append("    Dec1 -- No --> StepRej[\"Rejection & Return with Remarks\"]")
        lines.append("    StepRej -.-> Step1")
        lines.append("    StepAppr --> EndNode([Process End])")
        lines.append("    classDef startEnd fill:#DCFCE7,stroke:#16A34A,stroke-width:2px,color:#14532D,font-weight:bold;")
        lines.append("    classDef stepNode fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;")
        lines.append("    classDef decNode fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F,font-weight:bold;")
        lines.append("    classDef apprNode fill:#D1FAE5,stroke:#059669,stroke-width:2px,color:#064E3B;")
        lines.append("    classDef rejNode fill:#FEE2E2,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;")
        lines.append("    class Start,EndNode startEnd;")
        lines.append("    class Dec1 decNode;")
        lines.append("    class StepAppr apprNode;")
        lines.append("    class StepRej rejNode;")
        return "\n".join(lines)

    def generate_section_from_qa(self, section_id: str, section_config: Dict[str, Any], user_answers: str, team_name: str = "") -> Any:
        sec_type = section_config.get("type", "text")
        if sec_type == "table":
            fields = section_config.get("fields", [])
            row = {f: f"Sample {f} based on: {user_answers[:30]}" for f in fields}
            return [row]
        return f"Professional process note content synthesized from responses:\n\n{user_answers}"

    def resolve_clarification(self, section_id: str, section_type: str, current_content: Any, question: str, answer: str) -> Any:
        if section_type == "table" and isinstance(current_content, list):
            if current_content:
                current_content[0]["Description"] = current_content[0].get("Description", "") + f" [Clarification incorporated: {answer}]"
            return current_content
        return f"{current_content}\n\n**Clarification Note ({question}):** {answer}"

    def refine_table_rows_with_ai(
        self,
        section_id: str,
        section_config: Dict[str, Any],
        raw_rows: List[Dict[str, Any]],
        answers_dict: Dict[str, Any] = None,
        process_name: str = "",
        team_name: str = ""
    ) -> List[Dict[str, Any]]:
        from config.guided_questions import sanitize_rough_text
        refined = []
        for r in raw_rows:
            cleaned_row = {}
            for k, v in r.items():
                val_str = sanitize_rough_text(str(v or ""))
                if k == "Business Rules":
                    if "all" in val_str.lower() and "evaluation" in val_str.lower():
                        val_str = "All operational and testing drafts must undergo formal evaluation and verification prior to deployment (Enforced by the Process Owner end-to-end)."
                    elif not val_str.endswith("."):
                        val_str = val_str + "."
                cleaned_row[k] = val_str
            refined.append(cleaned_row)
        return refined


class GeminiProvider(LLMProvider):
    def __init__(self):
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(os.getenv("LLM_MODEL", "gemini-1.5-pro"))

    def validate_section(self, section_content: str, section_rules: Dict[str, Any], global_rules: Dict[str, Any] = None, team_name: str = "") -> SectionValidationResult:
        criteria = ""
        sec_id = section_rules.get("id", "")
        if global_rules:
            for rule in global_rules.get("rules", []):
                if rule.get("section_id") == sec_id:
                    criteria = "\n".join([f"- {c}" for c in rule.get("criteria", [])])
                    break
                    
        team_context = ""
        team_lower = team_name.lower() if team_name else ""
        if "volunteer" in team_lower:
            team_context = """
TEAM GOVERNANCE (VOLUNTEERING): Ensure coverage of onboarding criteria, background checks, safeguard requirements, allocation, training, grievance escalation, and certification.
"""
        elif "comm" in team_lower:
            team_context = """
TEAM GOVERNANCE (COMMUNICATIONS): Ensure coverage of branding guidelines, brand approvals, marketing calendar, PR approvals, consent forms, and vendor payments.
"""
        elif "finance" in team_lower:
            team_context = """
TEAM GOVERNANCE (FINANCE): Ensure Maker/Checker principles, delegation of authority (DOA), audit trail, and financial sign-offs.
"""

        section_specific_prompt = ""
        if sec_id == "1.10":
            section_specific_prompt = """
MANDATORY AUDIT FOR SECTION 1.10 (OBJECTIVE):
- Must articulate a substantive, comprehensive business objective.
- MUST state:
  1) The primary operational purpose of the process.
  2) The tangible, measurable business outcomes and targets (e.g., turnaround time thresholds, accuracy rates, compliance adherence, error reduction).
  3) Organizational value and alignment.
- STRICT DEPTH ENFORCEMENT: If the objective is brief (fewer than 20-25 words), superficial, or merely states a generic intent without concrete measurable targets or deliverables:
  DO NOT ASSIGN PASS (Score: 100).
  You MUST assign WARNING (Score: 50) or NEEDS_REVISION (Score: 0).
  Specifically state in 'issues' that the objective is too brief and lacks measurable targets, and formulate clarification questions asking for specific success benchmarks.
"""
        elif sec_id == "1.9":
            section_specific_prompt = """
MANDATORY AUDIT FOR SECTION 1.9 (INTRODUCTION):
- Must provide substantive organizational context and background rationale.
- MUST cover:
  1) Operational context and background within the organization.
  2) Why standardizing this specific process is critical (e.g. risk mitigation, consistency, auditability).
- STRICT DEPTH ENFORCEMENT: If the introduction is merely 1-2 generic sentences (fewer than 25-30 words):
  DO NOT ASSIGN PASS (Score: 100).
  You MUST assign WARNING (Score: 50) or NEEDS_REVISION (Score: 0).
  Request the Process Owner to detail the organizational necessity.
"""
        elif sec_id == "1.6":
            section_specific_prompt = """
MANDATORY AUDIT FOR SECTION 1.6 (PROCESS COVERAGE / SCOPE):
- Must clearly define operational boundaries.
- MUST explicitly specify BOTH:
  1) IN-SCOPE: Specific activities, programs, locations, and teams covered.
  2) OUT-OF-SCOPE: Related activities, handoffs, or teams explicitly excluded.
- STRICT DEPTH ENFORCEMENT: If the scope is only a brief generic phrase or fails to explicitly state out-of-scope exclusions:
  DO NOT ASSIGN PASS (Score: 100).
  Assign WARNING (Score: 50). Ask what related activities are explicitly excluded.
"""
        elif sec_id == "1.12":
            section_specific_prompt = """
MANDATORY 6-DIMENSION AUDIT FOR SECTION 1.12 (PROCESS DESCRIPTION):
Evaluate whether the steps provide clear, actionable details across these 6 enterprise dimensions:
1. Source of data / inputs required for each activity.
2. Step-by-step breakdown (major activities broken into specific sub-activities).
3. Tools, applications, and systems used at each stage (e.g., ERP, portals, Excel, field apps).
4. Teams or stakeholders involved and the hand-offs between them.
5. Expected outcome or deliverable of each activity and the overall process.
6. Checks, validations, and approvals (who verifies, against what criteria).

If ANY of these 6 dimensions are missing, vague, or if descriptions are brief 1-liners:
- Assign status WARNING (score 50) or NEEDS_REVISION (score 0).
- Specifically state the missing dimension in 'issues'.
- Formulate 1 to 3 direct, probing CLARIFICATION QUESTIONS for the Process Owner to ask for the exact missing information.
"""
        elif sec_id == "1.13":
            section_specific_prompt = """
MANDATORY AUDIT FOR SECTION 1.13 (RACI MATRIX):
- Must follow the standard 8-column format: Sr. No., Activity name, Activity description, Timeline, Responsible, Accountable, Consulted by, Informed to.
- Activities must align with Section 1.12.
- Responsible, Accountable, Consulted by, and Informed to must specify EXACT job designations/roles (e.g., PH, Manager, Vertical Lead, Director).
- Flag an issue if cells contain 'Yes', 'No', boolean values, or blanks. Single Accountable ownership is required per activity.
"""
        elif sec_id == "1.14":
            section_specific_prompt = """
MANDATORY AUDIT FOR SECTION 1.14 (BUSINESS RULES):
- Entries must be actual operational rules and boundaries, not generic process descriptions or suggestions.
- Rules must be concrete and enforceable.
"""

        prompt = f"""
You are an expert Senior Process Auditor and Business Excellence Lead reviewing an Enterprise Process Note.
Section ID: {sec_id}
Section Name: {section_rules.get('name')}
General Guidelines: {section_rules.get('help_text')}
Evaluation Criteria:
{criteria}
{team_context}
{section_specific_prompt}

Content to validate:
{section_content}

CRITICAL INSTRUCTIONS FOR SCORING AND OUTPUT:
Assess whether the content is complete, logical, and clearly documented from an organizational audit perspective.
STRICT AUDIT RULE ON SUBSTANCE & DEPTH:
- NEVER assign PASS (Score: 100) to brief, superficial, or shallow descriptions.
- Sections requiring narrative explanation (e.g., Objective 1.10, Introduction 1.9, Scope 1.6, Process Description 1.12) must have comprehensive operational depth, clarity, and specific details.
- If a section contains only 1-2 brief generic sentences (e.g. fewer than 20-25 words) or lacks concrete metrics, targets, or boundaries, you MUST assign WARNING (Score: 50) or NEEDS_REVISION (Score: 0).

You MUST output exactly one of the following fixed scores and statuses:

1. PASS (Score: 100):
   - The content fully addresses the requirements and meets all evaluation criteria with proper depth.
   - The logic is sound, end-to-end steps are documented, and no critical elements are missing.
   - Leave "issues", "recommendations", and "questions" COMPLETELY EMPTY.

2. WARNING (Score: 50):
   - Content partially addresses requirements but lacks operational detail (e.g. missing tools, inputs, or handoffs).
   - Provide specific issues, actionable recommendations, and targeted clarification questions for the Process Owner.

3. NEEDS_REVISION (Score: 0):
   - Content is missing, illogical, severely incomplete, or uses generic corporate filler.
   - Provide specific issues, actionable recommendations, and targeted clarification questions for the Process Owner.

Return your evaluation as a valid JSON object matching this schema exactly:
{{
    "status": "PASS" | "WARNING" | "NEEDS_REVISION",
    "score": 100 | 50 | 0,
    "severity": "LOW" | "MEDIUM" | "HIGH",
    "issues": [list of specific problems found, empty if none],
    "recommendations": [list of actionable advice, empty if none],
    "questions": [list of specific clarification questions for the Process Owner, empty if none]
}}
Do NOT wrap the JSON in markdown code blocks. Return only the raw JSON string.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
                
            data = json.loads(text)
            status = data.get("status", "PASS")
            score = 100.0 if status == "PASS" else (50.0 if status == "WARNING" else 0.0)

            return SectionValidationResult(
                section=section_rules.get("name", "Unknown Section"),
                status=status,
                score=score,
                issues=data.get("issues", []),
                recommendations=data.get("recommendations", []),
                questions=data.get("questions", []),
                severity=data.get("severity", "LOW")
            )
        except Exception as e:
            return SectionValidationResult(
                section=section_rules.get("name", "Unknown Section"),
                status="WARNING",
                score=50.0,
                issues=[f"AI Validation Exception: {str(e)}"],
                recommendations=["Please review the section content against organizational guidelines."],
                questions=["Could you please confirm the complete steps and responsible roles for this section?"],
                severity="MEDIUM"
            )

    def validate_cross_sections(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        prompt = f"""
You are an expert Senior Process Auditor and Business Excellence Lead conducting a cross-sectional consistency review of an enterprise Process Note.

All sections and their documented contents:
{json.dumps(all_sections, indent=2)}

You MUST rigorously audit the 4 core inter-relationships defined by the Business Excellence team:

1. KPI (Section 1.5) and Process Description (Section 1.12):
   - The activities performed in 1.12 must clearly contribute to intended process outcomes and produce the data sources required for the defined KPIs in 1.5.
   - If a KPI measures turnaround time or quality, is there an activity in 1.12 capturing that measurement?

2. Process Description (Section 1.12) and RACI Matrix (Section 1.13):
   - Every major activity in 1.12 must be reflected as an activity in the RACI Matrix (1.13).
   - Roles in the RACI matrix must be specific job designations (e.g., PH, Manager, Vertical Lead, Director), NEVER Yes/No or checkmarks.
   - Every activity must have a clear Accountable (A) designation.

3. Process Description (Section 1.12) and Business Rules (Section 1.14):
   - EVERY Business Rule listed in 1.14 must be adequately supported and implemented by operational steps in 1.12.
   - CRITICAL EXAMPLE: If a rule states "All translated scripts must pass a peer grammar check before recording", the Process Description (1.12) MUST document the step for conducting the peer grammar check, who performs it, tools used, and sign-off criteria.
   - If a Business Rule exists without documented implementation steps in 1.12, FLAG THE GAP and formulate a targeted clarification question for the Process Owner asking for the missing procedure and responsible role!

4. Process Description (Section 1.12) and Process Flowchart (Section 1.11):
   - The flowchart steps, decision diamonds, and hand-offs must visually and logically match the operational steps described in 1.12.

OUTPUT FORMAT:
If there are gaps or inconsistencies, return a JSON array of objects with this schema:
[
  {{
    "issue": "Clear, professional explanation of the inconsistency or gap across sections",
    "severity": "HIGH" | "MEDIUM",
    "questions": [
      "Specific clarification question for the Process Owner to explain and resolve the gap"
    ],
    "related_sections": ["1.12", "1.14"]
  }}
]

If everything is completely consistent and all business rules, KPIs, and RACI roles are supported, return an empty array: []

Return ONLY raw JSON. No markdown code blocks.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                text = match.group(0)
            data = json.loads(text)
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            return [{
                "issue": f"Cross-section validation check error: {str(e)}",
                "severity": "MEDIUM",
                "questions": ["Please verify consistency between Process Description, RACI Matrix, and Business Rules."],
                "related_sections": ["1.12", "1.13", "1.14"]
            }]

    def generate_suggestion(self, section_rules: Dict[str, Any], context_list: List[str], user_draft: str = "") -> str:
        context_str = "\n".join(context_list) if context_list else "No historical context available."
        
        draft_instruction = ""
        if user_draft and user_draft.strip():
            draft_instruction = f"\n\nThe creator provided these rough notes:\n\"\"\"{user_draft}\"\"\"\nPlease refine, polish, and structure these notes into a high-standard corporate process section."
        else:
            draft_instruction = "\n\nPlease generate a professional, fully compliant template/draft based on the section criteria."

        prompt = f"""
You are an expert Process Management Consultant assisting a team in drafting an enterprise Process Note.
Section: {section_rules.get('id')} - {section_rules.get('name')}
Guidelines: {section_rules.get('help_text')}
Example: {section_rules.get('example', 'N/A')}
Historical Context:
{context_str}
{draft_instruction}

Generate a polished, professional, and audit-ready draft. Do not use generic filler. Output only the suggested draft.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating suggestion: {str(e)}"

    def generate_flowchart_mermaid(self, process_description_steps: List[Dict[str, Any]]) -> str:
        steps_summary = json.dumps(process_description_steps, indent=2)
        prompt = f"""
You are an expert BPMN process modeler.
Convert the following process activities from Section 1.12 (Process Description) into a clean, professional Mermaid.js flowchart (starting with 'graph TD'):

Activities:
{steps_summary}

RULES:
1. Start with 'graph TD'.
2. Represent sequential process steps in clear rectangular boxes: S1["1. Activity Name<br/>Owner: Role"].
3. Represent key verification, checks, or approval points as decision diamonds: D1{{"Criteria Met?"}} -->|Yes| S2[...] / D1 -->|No| S_Fix[...].
4. Capture hand-offs between roles clearly.
5. Keep labels concise, clean, and escape any characters that would break Mermaid syntax (do not use raw quotes or parentheses inside node labels without quotes).
6. Return ONLY the valid Mermaid code without markdown code fences (no ```mermaid).
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            text = re.sub(r'^```mermaid\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'```$', '', text).strip()
            return text
        except Exception:
            # Fallback generator
            lines = ["graph TD"]
            for idx, s in enumerate(process_description_steps, start=1):
                act = str(s.get("Activity", f"Activity {idx}")).replace('"', '')
                owner = str(s.get("Owner/Role", "")).replace('"', '')
                lines.append(f"    S{idx}[\"{act} ({owner})\"]")
                if idx > 1:
                    lines.append(f"    S{idx-1} --> S{idx}")
            return "\n".join(lines)

    def assist_flowchart(self, draft_steps: str, decisions: str = "", roles: str = "", process_name: str = "", team_name: str = "") -> str:
        prompt = f"""
You are an expert BPMN process modeler and Business Excellence consultant.
Create an enterprise-grade Mermaid.js flowchart (starting with 'flowchart TD') for the following operational process:
Process Name: {process_name}
Team / Department: {team_name}

Creator's Rough Draft / Steps:
\"\"\"{draft_steps}\"\"\"

Decision Points / Rejection criteria:
\"\"\"{decisions}\"\"\"

Key Roles / Stakeholders:
\"\"\"{roles}\"\"\"

CRITICAL RULES:
1. Start with 'flowchart TD'.
2. Standard BPMN node shapes:
   - Start and End boundaries MUST be rounded stadium/pill shapes: Start([Process Start]) and EndNode([Process End])
   - Sequential process activities MUST be crisp rectangular boxes: Step1["1. Step Description<br/>Owner: Role"]
   - Decision/verification points MUST be diamond shapes: Dec1{{"Criteria Met?"}}
   - Branches MUST have labeled arrows: Dec1 -- Yes --> StepAppr["Approval & Sign-off"] and Dec1 -- No --> StepRej["Rejection & Return"]
   - Include a dotted return loopback for rework/resubmission: StepRej -.-> Step1
3. BREAK DOWN LONG / CONVERSATIONAL SENTENCES:
   - If the user provides a conversational sentence, multi-action clause, or run-on phrase (e.g., 'first they need to create a draft, then move ahead with testing'), NEVER leave it as one giant box.
   - You MUST split it into sequential, discrete action steps (e.g., Step1["1. Create Process Note Draft"] --> Step2["2. Conduct Operational Testing"]).
   - Use crisp, imperative professional business action phrases (3 to 8 words per box).
4. Strictly escape any quotes or special characters inside node labels so the Mermaid syntax never breaks.
5. Apply styling classes at the end:
   classDef startEnd fill:#DCFCE7,stroke:#16A34A,stroke-width:2px,color:#14532D,font-weight:bold;
   classDef stepNode fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
   classDef decNode fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F,font-weight:bold;
   classDef apprNode fill:#D1FAE5,stroke:#059669,stroke-width:2px,color:#064E3B;
   classDef rejNode fill:#FEE2E2,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;
   class Start,EndNode startEnd;
6. Return ONLY the valid Mermaid code without markdown code blocks (no ```mermaid).
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            text = re.sub(r'^```mermaid\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'```$', '', text).strip()
            return text
        except Exception:
            from config.guided_questions import build_mermaid_flowchart_from_answers
            return build_mermaid_flowchart_from_answers({"steps": draft_steps, "decisions": decisions, "roles": roles})

    def generate_section_from_qa(self, section_id: str, section_config: Dict[str, Any], user_answers: str, team_name: str = "") -> Any:
        sec_type = section_config.get("type", "text")
        fields = section_config.get("fields", [])
        prompt = f"""
You are an expert Process Management Consultant assisting a Process Owner in creating an enterprise-grade Process Note.
Section ID: {section_id}
Section Name: {section_config.get('name')}
Section Type: {sec_type}
Table Fields: {fields if sec_type == 'table' else 'N/A'}
Guidelines: {section_config.get('help_text')}

The creator has answered the guided assistant questions with the following rough notes:
\"\"\"{user_answers}\"\"\"

TASK:
Convert these rough answers into a complete, professional, corporate-grade section conforming strictly to organizational standards.

OUTPUT FORMAT:
- If Section Type is 'table':
  Return a valid JSON array of objects where each object has keys exactly matching the Table Fields:
  [
    {{ {', '.join([f'"{f}": "..."' for f in fields])} }}
  ]
  Return ONLY the raw JSON array. No markdown code blocks.

- If Section Type is 'text':
  Return polished, professional, well-structured text with proper paragraphs or bullet points. Do not use generic filler.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if sec_type == "table":
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    text = match.group(0)
                data = json.loads(text)
                if isinstance(data, list):
                    return data
            return text
        except Exception as e:
            if sec_type == "table":
                return [{f: user_answers[:40] for f in fields}]
            return f"Processed draft based on answers:\n\n{user_answers}"

    def resolve_clarification(self, section_id: str, section_type: str, current_content: Any, question: str, answer: str) -> Any:
        prompt = f"""
You are an enterprise Process Management Editor.
A Process Owner has answered an audit clarification question raised by the Business Excellence review team.

Section ID: {section_id}
Section Type: {section_type}

Current Section Content:
{json.dumps(current_content, indent=2) if section_type == 'table' else str(current_content)}

Audit Clarification Question:
\"{question}\"

Process Owner's Clarification Response:
\"{answer}\"

TASK:
Seamlessly integrate the Process Owner's response into the existing section content so that the audit gap is completely addressed and documented with organizational rigor.
- If Section Type is 'table':
  Return the updated JSON array of row objects.
- If Section Type is 'text':
  Return the updated complete section text incorporating the clarification.

Return ONLY the updated content. If JSON, do not wrap in markdown fences.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if section_type == "table":
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    text = match.group(0)
                data = json.loads(text)
                if isinstance(data, list):
                    return data
            return text
        except Exception:
            if section_type == "table" and isinstance(current_content, list):
                if current_content:
                    current_content[0]["Description"] = current_content[0].get("Description", "") + f" [Clarification: {answer}]"
                return current_content
            return f"{current_content}\n\n**Clarification ({question}):** {answer}"

    def refine_table_rows_with_ai(
        self,
        section_id: str,
        section_config: Dict[str, Any],
        raw_rows: List[Dict[str, Any]],
        answers_dict: Dict[str, Any] = None,
        process_name: str = "",
        team_name: str = ""
    ) -> List[Dict[str, Any]]:
        fields = section_config.get("fields", [])
        sec_name = section_config.get("name", f"Section {section_id}")
        help_text = section_config.get("help_text", "")

        prompt = f"""
You are a Principal Business Excellence Consultant and Senior Technical Writer for enterprise Standard Operating Procedures (SOPs) and Process Notes.
A Process Creator has submitted rough draft answers for Section {section_id}: "{sec_name}".

Process Name: {process_name}
Team: {team_name}
Section Guidelines: {help_text}
Expected Table Columns: {fields}

Creator's Rough Draft Rows:
{json.dumps(raw_rows, indent=2)}

Original Creator Questionnaire Responses:
{json.dumps(answers_dict or {}, indent=2)}

YOUR MANDATORY OBJECTIVES:
1. SPELLING & GRAMMAR RECTIFICATION:
   - Fix all spelling errors, phonetic typos, and informal shorthand (e.g., 'drsfts' -> 'drafts', 'cretion' -> 'creation', 'deplyment' -> 'deployment', 'texting' -> 'testing').
2. ELEVATE TO EXECUTIVE CORPORATE SOP PHRASING:
   - Rewrite casual, colloquial, or fragmented notes into crisp, authoritative, standardized corporate language.
   - Example: Instead of "all texting drsfts should go via final evaluation (Enforced by project owner verifies everything end to end)", rewrite to:
     "All operational testing drafts and deliverables must undergo mandatory formal review and sign-off prior to deployment (Enforced by the Process Owner via end-to-end audit verification)."
3. AUDIT RIGOR & BE STANDARDS:
   - Ensure the refined content is specific, unambiguous, and compliant with Business Excellence quality benchmarks.
   - Retain the exact business intent, numbers, thresholds, and role designations provided by the user.
4. STRICT JSON OUTPUT FORMAT:
   - Return a valid JSON array of objects with EXACTLY the keys matching the Expected Table Columns: {fields}.
   - Return ONLY the JSON array. Do not include markdown code fences or explanatory text.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                text = match.group(0)
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0:
                cleaned_rows = []
                for row in data:
                    if isinstance(row, dict):
                        cleaned_row = {f: str(row.get(f, "")).strip() for f in fields}
                        cleaned_rows.append(cleaned_row)
                if cleaned_rows:
                    return cleaned_rows
        except Exception as e:
            print(f"Error in refine_table_rows_with_ai: {e}")

        # Safe fallback
        from config.guided_questions import sanitize_rough_text
        sanitized = []
        for r in raw_rows:
            sanitized.append({k: sanitize_rough_text(str(v or "")) for k, v in r.items()})
        return sanitized


def get_llm_provider() -> LLMProvider:
    from dotenv import load_dotenv
    try:
        load_dotenv(dotenv_path='.env')
    except Exception:
        pass
    
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "mock":
        return MockProvider()
    else:
        raise ValueError(f"LLM_PROVIDER '{provider_name}' is not implemented. Supported providers: 'mock', 'gemini'.")
