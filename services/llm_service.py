import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json
from models.schemas import SectionValidationResult

class LLMProvider(ABC):
    @abstractmethod
    def validate_section(self, section_content: str, section_rules: Dict[str, Any], global_rules: Dict[str, Any] = None) -> SectionValidationResult:
        pass

    @abstractmethod
    def validate_cross_sections(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def generate_suggestion(self, section_rules: Dict[str, Any], context_list: List[str], user_draft: str = "") -> str:
        pass

class MockProvider(LLMProvider):
    def validate_section(self, section_content: str, section_rules: Dict[str, Any], global_rules: Dict[str, Any] = None) -> SectionValidationResult:
        content_lower = section_content.lower()
        issues = []
        recommendations = []
        status = "PASS"
        score = 95.0
        severity = "LOW"

        # Simulate detecting generic filler
        if "very important" in content_lower or "operational excellence" in content_lower:
            issues.append("Contains generic or filler language.")
            recommendations.append("Remove generic background and focus on process specifics.")
            status = "WARNING"
            score = 75.0
            severity = "MEDIUM"

        if len(section_content) < 10 and not section_rules.get("allow_short", False):
            issues.append("Response seems too brief to adequately address the section.")
            recommendations.append("Expand the description with more relevant details.")
            status = "NEEDS_REVISION"
            score = 50.0
            severity = "HIGH"

        return SectionValidationResult(
            section=section_rules.get("name", "Unknown Section"),
            status=status,
            score=score,
            issues=issues,
            recommendations=recommendations,
            severity=severity
        )

    def validate_cross_sections(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        cross_issues = []
        # Mock cross-section logic
        has_sipoc = any(s.get("section_id") == "1.22" and s.get("content") for s in all_sections)
        has_desc = any(s.get("section_id") == "1.12" and s.get("content") for s in all_sections)
        
        if has_sipoc and has_desc:
            # Random mock check
            cross_issues.append({
                "issue": "Mock: Step mentioned in SIPOC does not appear in Process Description.",
                "severity": "MEDIUM"
            })
        
        return cross_issues

    def generate_suggestion(self, section_rules: Dict[str, Any], context_list: List[str], user_draft: str = "") -> str:
        return f"This is a mock AI suggestion for {section_rules.get('name')}. Context items found: {len(context_list)}."

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
        if global_rules:
            for rule in global_rules.get("rules", []):
                if rule.get("section_id") == section_rules.get("id"):
                    criteria = "\n".join([f"- {c}" for c in rule.get("criteria", [])])
                    break
                    
        team_context = ""
        team_lower = team_name.lower() if team_name else ""
        if "volunteer" in team_lower:
            team_context = """
TEAM-SPECIFIC GOVERNANCE RULES (VOLUNTEERING):
Ensure the process note adequately covers:
- Types of Volunteering
- Volunteer onboarding, registration and eligibility criteria.
- Volunteer allocation/deployment process across programmes and activities.
- Volunteer engagement, attendance and participation tracking.
- Roles, responsibilities and reporting structure of volunteers.
- Volunteer training, orientation and capacity-building process.
- Volunteer communication, grievance handling and escalation mechanism.
- Background verification, code of conduct and safeguarding requirements, wherever applicable.
- Volunteer exit process.
- Volunteer data management, documentation and records maintained.
- Monitoring, feedback and performance evaluation of volunteers.
- Volunteer certification process, including eligibility criteria, assessment/completion requirements, approval and issuance of certificates.
"""
        elif "comm" in team_lower:
            team_context = """
TEAM-SPECIFIC GOVERNANCE RULES (COMMUNICATIONS):
Ensure the process note adequately covers:
- Branding guidelines, brand identity and usage standards.
- Brand approval process for logos, creatives, collaterals.
- Budget, vendor management, and payment/approval processes.
- Roles, responsibilities, approval matrix and escalation mechanism.
- Records and documentation of approvals and performance/MIS.
"""
        elif "finance" in team_lower:
            team_context = """
TEAM-SPECIFIC GOVERNANCE RULES (FINANCE):
Ensure the process note adequately covers standard finance governance, such as Maker/Checker principles, audit trails, and strict financial approval matrices.
"""
                    
        prompt = f"""
You are an expert Process Auditor. Validate the following process section.
Section Name: {section_rules.get('name')}
General Guidelines: {section_rules.get('help_text')}
Strict Evaluation Criteria:
{criteria}
{team_context}

Content to validate:
{section_content}

Evaluate the content against the rules. Be practical and highly lenient. If the core requirement of the section is met, award a PASS and a high score (75-100). 
Do NOT penalize the content for being brief, concise, or lacking excessive detail as long as the necessary basic information is provided. 
Only give a WARNING (Score 60-74) or NEEDS_REVISION (Score < 60) if critical compliance rules for the team are actively violated, egregiously missing, or if the input is complete gibberish.

CRITICAL INSTRUCTIONS FOR OUTPUT:
1. If the evaluation results in a "PASS", you MUST leave the "issues" and "recommendations" lists COMPLETELY EMPTY. Do not invent reasons or explain the pass.
2. If the evaluation results in "WARNING" or "NEEDS_REVISION", provide very brief issues and recommendations (maximum 1 short sentence per point).

Return your evaluation as a valid JSON object matching this schema exactly:
{{
    "status": "PASS" | "WARNING" | "NEEDS_REVISION",
    "score": float (0-100),
    "severity": "LOW" | "MEDIUM" | "HIGH",
    "issues": [list of specific problems found, empty if none],
    "recommendations": [list of actionable advice, empty if none]
}}
Do NOT wrap the JSON in markdown code blocks. Just return the raw JSON string.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON block even if there is surrounding text
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
                
            data = json.loads(text)

            return SectionValidationResult(
                section=section_rules.get("name", "Unknown Section"),
                status=data.get("status", "PASS"),
                score=float(data.get("score", 100.0)),
                issues=data.get("issues", []),
                recommendations=data.get("recommendations", []),
                severity=data.get("severity", "LOW")
            )
        except Exception as e:
            return SectionValidationResult(
                section=section_rules.get("name", "Unknown Section"),
                status="WARNING",
                score=0.0,
                issues=[f"LLM Error: {str(e)}"],
                recommendations=[],
                severity="HIGH"
            )

    def validate_cross_sections(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        prompt = f"""
You are an expert Process Auditor. Validate the cross-section consistency of the following process note.

All sections and their content:
{json.dumps(all_sections, indent=2)}

Check for logical inconsistencies across sections. For example, a role mentioned in RACI should be defined in Roles & Responsibilities. A step in the SIPOC should be in the detailed process flow.

If everything is consistent, return an empty list: []
If there are inconsistencies, return a JSON array of objects with this exact schema:
[
  {{
    "issue": "Description of the inconsistency",
    "severity": "LOW" | "MEDIUM" | "HIGH"
  }}
]

Output ONLY the raw JSON array. Do NOT wrap in markdown code blocks.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                text = match.group(0)
                
            data = json.loads(text)
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            return [{"issue": f"Cross-section LLM Error: {str(e)}", "severity": "HIGH"}]

    def generate_suggestion(self, section_rules: Dict[str, Any], context_list: List[str], user_draft: str = "") -> str:
        context_str = "\n".join(context_list) if context_list else "No historical context available."
        
        draft_instruction = ""
        if user_draft and user_draft.strip():
            draft_instruction = f"\n\nThe user has provided the following rough draft or notes:\n\"\"\"{user_draft}\"\"\"\nPlease expand, refine, and properly format these notes into a professional section based on the guidelines and historical context. Do not invent completely new concepts not mentioned by the user unless strictly required by the section guidelines."
        else:
            draft_instruction = "\n\nThe user has not provided a draft. Please generate a highly relevant template or complete draft based on the guidelines and historical context."

        prompt = f"""
You are an expert Process Consultant helping a user draft a section of their process note.
Section Name: {section_rules.get('name')}
Guidelines: {section_rules.get('help_text')}

Historical Context (from similar process notes in their team):
{context_str}{draft_instruction}

Please generate a professional, concise, and highly relevant draft for this section. Output ONLY the suggested text, nothing else. Do not use generic corporate filler.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating suggestion: {str(e)}"

def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "mock":
        return MockProvider()
    else:
        raise ValueError(f"LLM_PROVIDER '{provider_name}' is not implemented. Supported providers: 'mock', 'gemini'.")
