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

class GeminiProvider(LLMProvider):
    def __init__(self):
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(os.getenv("LLM_MODEL", "gemini-1.5-pro"))

    def validate_section(self, section_content: str, section_rules: Dict[str, Any], global_rules: Dict[str, Any] = None) -> SectionValidationResult:
        criteria = ""
        if global_rules:
            for rule in global_rules.get("rules", []):
                if rule.get("section_id") == section_rules.get("id"):
                    criteria = "\n".join([f"- {c}" for c in rule.get("criteria", [])])
                    break
                    
        prompt = f"""
You are an expert Process Auditor. Validate the following process section.
Section Name: {section_rules.get('name')}
General Guidelines: {section_rules.get('help_text')}
Strict Evaluation Criteria:
{criteria}

Content to validate:
{section_content}

Evaluate the content strictly against the rules. Be very critical and catch intentional mistakes (e.g. missing approvers, vague metrics, no accountability).

CRITICAL INSTRUCTIONS FOR OUTPUT:
1. If the evaluation results in a "PASS", you MUST leave the "issues" and "recommendations" lists COMPLETELY EMPTY. Do not invent reasons or explain the pass.
2. If the evaluation results in "WARNING" or "NEEDS_REVISION", you must provide issues and recommendations, but keep them CRISP and CONCISE (maximum 1-2 short sentences per point). Do not write long paragraphs.

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
        # Simplified for now
        return []

def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_name == "gemini":
        return GeminiProvider()
    else:
        return MockProvider()
