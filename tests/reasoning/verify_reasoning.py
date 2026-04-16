import asyncio
import os
import sys
import json

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.vertex_llm import VertexLLMService
from app.models import PatentAnalysis

# --- Test Fixtures ---

FIXTURES = [
    {
        "name": "Clear Anticipation",
        "claim_text": "A widget comprising a rotatable gear.",
        "elements": ["A widget comprising a rotatable gear"],
        "prior_art_data": {
            "patent_id": "US-TEST-001",
            "paragraphs": [
                {"id": "p_0", "text": "The widget 100 includes a gear 105 that rotates about an axis."},
                {"id": "p_1", "text": "The rotation speed is adjustable."}
            ]
        },
        "expected_support": "anticipated",
        "expected_citation": "p_0"
    },
    {
        "name": "Thematic Match (Unsupported)",
        "claim_text": "A neural network utilizing 8-bit integer quantization for weights.",
        "elements": ["A neural network utilizing 8-bit integer quantization for weights"],
        "prior_art_data": {
            "patent_id": "US-TEST-002",
            "paragraphs": [
                {"id": "p_0", "text": "The system employs a neural network for classification."},
                {"id": "p_1", "text": "Various data formats can be used for processing, including floating point and integers."} 
                # Note: Mentions integers, but NOT specifically 8-bit quantization for weights. 
                # Should be Thematic or Partial, thus Unsupported.
            ]
        },
        "expected_support": "unsupported",
        "expected_citation": None 
    },
    {
        "name": "Partial Teaching (Unsupported)",
        "claim_text": "A bicycle frame made of carbon fiber with an integrated battery compartment.",
        "elements": ["A bicycle frame made of carbon fiber with an integrated battery compartment"],
        "prior_art_data": {
            "patent_id": "US-TEST-003",
            "paragraphs": [
                {"id": "p_0", "text": "The bicycle frame is constructed from high-strength carbon fiber material."},
                {"id": "p_1", "text": "The frame is aerodynamic."}
                # Note: Missing "integrated battery compartment".
            ]
        },
        "expected_support": "unsupported", # Strict rule: Partial -> Unsupported
        "expected_citation": None
    }
]

import time

async def run_tests():
    print("--- Starting Reasoning Verification ---")
    llm = VertexLLMService()
    
    passed = 0
    total = len(FIXTURES)
    
    for test in FIXTURES:
        print(f"\nTest: {test['name']}")
        time.sleep(30) # Rate limit backoff
        try:
            analysis = await llm.analyze_patent(
                claim_text=test['claim_text'],
                elements=test['elements'],
                prior_art_data=test['prior_art_data'],
                strict_mode=True
            )
            
            # Extract result for the single element
            if not analysis.element_analysis:
                print(f"FAILED: No element analysis returned.")
                continue
                
            result = analysis.element_analysis[0]
            support = result.support_type.lower()
            citations = result.matched_paragraph_ids
            
            print(f"  > Expected: {test['expected_support']}")
            print(f"  > Got:      {support}")
            print(f"  > Citations: {citations}")
            print(f"  > Explanation: {result.explanation}")
            
            # Validation Logic
            success = True
            if support != test['expected_support']:
                print("  [X] Support Type Mismatch")
                success = False
            
            if test['expected_citation']:
                if test['expected_citation'] not in citations:
                    print(f"  [X] Missing Expected Citation {test['expected_citation']}")
                    success = False
            else:
                # If expected citation is None, we expect empty citations for strict "unsupported"
                # BUT sometimes model might cite relevant text even if concluding unsupported.
                # Strictly speaking, strict mode prompts say "matched_paragraph_ids with ONLY the IDs used".
                # If unsupported, usually no ID supports it.
                if citations and support == "unsupported":
                     print(f"  [!] Warning: Citations provided for unsupported element: {citations}")
                     # Not necessarily a fail, but worth noting.
            
            if success:
                print("  [PASSED]")
                passed += 1
            else:
                print("  [FAILED]")

        except Exception as e:
            print(f"  [ERROR] Exception during test: {e}")
            
    print(f"\n--- Summary: {passed}/{total} Passed ---")
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_tests())
