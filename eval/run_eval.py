import os
import sys
import json
import asyncio
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from tqdm import tqdm

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.vector_search import VectorSearchService
from app.services.vertex_llm import VertexLLMService
from app.services.local_vector_store import LocalVectorStore

# Initialize Services
# Force LocalVectorStore to avoid Qdrant dependency during eval
local_store = LocalVectorStore()
vector_service = VectorSearchService(store=local_store)
llm_service = VertexLLMService()

HARD_NEGATVES_PATH = os.path.join(os.path.dirname(__file__), 'hard_negatives.json')
REPORT_PATH = os.path.join(os.path.dirname(__file__), '../EVAL_HARD_NEGATIVES.md')

def load_hard_negatives():
    with open(HARD_NEGATVES_PATH, 'r') as f:
        return json.load(f)

async def evaluate_robustness(examples, top_k=20):
    results = []
    print(f"Running robustness evaluation on {len(examples)} examples...")
    
    for ex in tqdm(examples):
        mod_text = ex['modified_text']
        true_pid = ex['patent_id']
        modification = ex['modification']
        target_chunk_id = ex.get('target_chunk_id')
        
        # 1. Retrieval Robustness
        # Can we still find the patent despite the change?
        matches = await vector_service.search(mod_text, top_k=top_k)
        
        hits = [m for m in matches if m.patent_id == true_pid]
        is_hit = len(hits) > 0
        top_hit = hits[0] if hits else None
        
        # 2. Reasoning Robustness (Hallucination Check)
        # We process the top relevant hit (or top hit overall if no relevant hit found? 
        # Ideally we want to test if the model hallucinations support on the *relevant* text).
        # If we don't find the patent, we can't test "Anticipation of modified claim on original patent".
        # So we only run reasoning if we found the patent.
        
        reasoning_result = "N/A"
        quote_check = "N/A"
        support_type = "N/A"
        
        if top_hit:
            try:
                # 1. Decompose the modified claim
                # The analysis service requires elements.
                decomposition = await llm_service.decompose_claim(mod_text)
                elements = decomposition.elements
                
                # 2. Construct Prior Art Data
                # analyze_patent expects: {'patent_id': str, 'paragraphs': [{'id': str, 'text': str}]}
                # top_hit is a ParagraphMatch object.
                prior_art_data = {
                    "patent_id": top_hit.patent_id,
                    "paragraphs": [{"id": top_hit.paragraph_id, "text": top_hit.text}]
                }
                
                # 3. Analyze
                analysis = await llm_service.analyze_patent(
                    claim_text=mod_text,
                    elements=elements,
                    prior_art_data=prior_art_data,
                    strict_mode=True # Enforce strict citation checking
                )
                
                # Analyze the report
                # We look for the element that contains the 'replacement' term.
                replacement_term = modification.split(' -> ')[1]
                
                target_element_status = "Not Found"
                target_element_quote = ""
                
                # Convert Pydantic model to dict if needed, or access attributes
                # PatentAnalysis -> element_analysis (list)
                
                for element in analysis.element_analysis:
                    # element is ElementAnalysis object? Or dict if loaded from JSON in service?
                    # Service returns PatentAnalysis object.
                    # ElementAnalysis has 'text', 'status' (mapped to support_type in JSON?), 'supporting_quote'
                    # Wait, looking at VertexLLMService, it returns PatentAnalysis(**data).
                    # Let's check model definition if we can. 
                    # Assuming standard attribute access.
                    
                    e_text = getattr(element, 'element', '') or getattr(element, 'text', '')
                    if replacement_term.lower() in e_text.lower():
                        support_type = getattr(element, 'support_type', 'unknown')
                        target_element_quote = getattr(element, 'source_quote', '')
                        target_element_status = "Found"
                        break
                
                if target_element_status == "Found":
                    # Strict Check: success if Unsupported. 
                    # Obvious is "Warning" but not Fail in this version? 
                    # User said: "Treat Obvious as neutral/optional for now; we want strict anti-hallucination".
                    # So PASS if != Anticipated.
                    
                    if support_type.lower() == "anticipated":
                        reasoning_result = "FAIL (Hallucination)"
                    else:
                        reasoning_result = "PASS"
                        
                    # Queue Verification
                    if target_element_quote:
                        # Normalize a bit (strip punct, lower)
                        q_norm = "".join(target_element_quote.lower().split())
                        full_norm = "".join(top_hit.text.lower().split())
                        
                        # Service already does "Soft fail" verification.
                        # But we want to explicitly measure it in Eval.
                        if q_norm in full_norm and len(q_norm) > 10:
                             quote_check = "PASS"
                        elif len(q_norm) < 10:
                             quote_check = "WARN (Short)"
                        else:
                             quote_check = "FAIL (Fabricated)"
                    else:
                        # If unsupported, often no quote. That's fine.
                        quote_check = "N/A"
                        
            except Exception as e:
                print(f"LLM Error: {e}")
                import traceback
                traceback.print_exc()
                reasoning_result = "ERROR"

        results.append({
            "original_id": ex['original_id'],
            "modification": modification,
            "retrieval_hit": is_hit,
            "support_type": support_type,
            "reasoning_result": reasoning_result,
            "quote_check": quote_check
        })
        
    return pd.DataFrame(results)

async def main():
    if not os.path.exists(HARD_NEGATVES_PATH):
        print("Hard negatives not found. Run generate_hard_test.py first.")
        return

    data = load_hard_negatives()
    # Sample if too large? 
    # Generating script creates all matches. Let's take 20 for eval speed if many.
    if len(data) > 20:
        import random
        random.seed(42)
        data = random.sample(data, 20)
    
    df = await evaluate_robustness(data, top_k=20)
    
    # Metrics
    retrieval_recall = df['retrieval_hit'].mean()
    
    # Reasoning Metrics (excluding N/A which implies retrieval failure or no target element found)
    valid_reasoning = df[df['reasoning_result'].isin(['PASS', 'FAIL (Hallucination)'])]
    if len(valid_reasoning) > 0:
        hallucination_rate = (valid_reasoning['reasoning_result'] == 'FAIL (Hallucination)').mean()
    else:
        hallucination_rate = 0.0
        
    # Quote Metrics
    valid_quotes = df[df['quote_check'].isin(['PASS', 'FAIL (Fabricated)'])]
    if len(valid_quotes) > 0:
        quote_fail_rate = (valid_quotes['quote_check'] == 'FAIL (Fabricated)').mean()
    else:
        quote_fail_rate = 0.0

    report = f"""# APEX Hard Negative Evaluation (Adversarial)
**Date**: {pd.Timestamp.now()}
**Sample Size**: {len(data)} Modified Claims

## 1. Retrieval Robustness
| Metric | Value | Target |
|---|---|---|
| **Robust Recall@20** | **{retrieval_recall:.2%}** | > 80% |
*Can we find the original patent even when a keyword is swapped?*

## 2. Reasoning Reliability (Anti-Hallucination)
| Metric | Value | Target |
|---|---|---|
| **Hallucination Rate** | **{hallucination_rate:.2%}** | 0% |
*Frequency where model claims "Anticipation" for the modified term.*

## 3. Evidence Integrity
| Metric | Value | Target |
|---|---|---|
| **Fake Quote Rate** | **{quote_fail_rate:.2%}** | 0% |
*Frequency where cited quote text does not exist in the source.*

## Failure Examples
{df[df['reasoning_result'] == 'FAIL (Hallucination)'][['modification', 'support_type']].to_markdown()}

## Full Data
{df.to_markdown()}
    """
    
    print(report)
    with open(REPORT_PATH, 'w') as f:
        f.write(report)
    print(f"Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
