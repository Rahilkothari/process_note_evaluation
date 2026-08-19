from typing import List, Dict, Any
from services.llm_service import get_llm_provider

class CrossSectionValidator:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    def validate(self, all_sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        return self.llm_provider.validate_cross_sections(all_sections)
