import asyncio
import os
import sys
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.vertex_llm import VertexLLMService
from app.models import PatentAnalysis, OverallAssessment, ElementAnalysis, ClaimElements

# Mock the GenerativeModel to avoid API calls
class MockGenerativeModel:
    def __init__(self, response_text):
        self.response_text = response_text
    
    def generate_content(self, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.text = self.response_text
        return mock_response

def test_offline_quote_verification():
    print("--- Testing Quote Verification (Offline) ---")
    
    service = VertexLLMService()
    
    # Scene: LLM returns a hallucinated quote
    hallucinated_json = json.dumps({
        "prior_art_id": "TEST-001",
        "rationale_bullets": ["Reason 1"],
        "element_analysis": [
            {
                "element": "Element A",
                "matched_paragraph_ids": ["p0"],
                "source_quote": "This text does not exist in the prior art.",
                "support_type": "anticipated",
                "explanation": "Hallucinated."
            },
            {
                "element": "Element B",
                "matched_paragraph_ids": ["p1"],
                "source_quote": "Real text exists here.",
                "support_type": "anticipated",
                "explanation": "Real."
            }
        ],
        "overall_assessment": {
            "novelty_risk": "high",
            "obviousness_risk": "low",
            "summary": "Fake summary"
        }
    })
    
    # Mock the model
    service.model = MockGenerativeModel(hallucinated_json)
    
    prior_art_data = {
        "patent_id": "TEST-001",
        "paragraphs": [
            {"id": "p0", "text": "Something completely different."},
            {"id": "p1", "text": "Real text exists here. Indeed it does."}
        ]
    }
    
    # Run analysis
    analysis = asyncio.run(service.analyze_patent("Claim", ["Element A", "Element B"], prior_art_data))
    
    # Verify Element A (Hallucinated)
    elem_a = next(e for e in analysis.element_analysis if e.element == "Element A")
    print(f"Element A Status: {elem_a.support_type}, Invalid Citation: {elem_a.citation_invalid}")
    
    if elem_a.support_type == "unsupported" and elem_a.citation_invalid == True:
        print("  [PASSED] Hallucination correctly downgraded.")
    else:
        print(f"  [FAILED] Element A should be unsupported/invalid. Got {elem_a.support_type}/{elem_a.citation_invalid}")

    # Verify Element B (Real)
    elem_b = next(e for e in analysis.element_analysis if e.element == "Element B")
    print(f"Element B Status: {elem_b.support_type}, Invalid Citation: {elem_b.citation_invalid}")
    
    if elem_b.support_type == "anticipated" and elem_b.citation_invalid == False:
        print("  [PASSED] Valid quote maintained.")
    else:
        print(f"  [FAILED] Element B should be anticipated/valid. Got {elem_b.support_type}/{elem_b.citation_invalid}")

if __name__ == "__main__":
    test_offline_quote_verification()
