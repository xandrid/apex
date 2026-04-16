import asyncio
import json
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.services.hybrid_search import HybridSearchService
from app.services.vertex_llm import VertexLLMService

async def evaluate():
    print("Starting Evaluation...")
    
    # Load Golden Dataset
    with open('golden_dataset.json', 'r') as f:
        dataset = json.load(f)
        
    hybrid_service = HybridSearchService()
    llm_service = VertexLLMService()
    
    total_cases = len(dataset)
    recall_hits = 0
    citation_hits = 0
    total_citations_checked = 0
    
    for case in dataset:
        print(f"\nEvaluating Case: {case['id']}")
        claim_text = case['claim_text']
        expected_pid = case['expected_prior_art_id']
        expected_paras = set(case['expected_paragraph_ids'])
        
        # 1. Test Retrieval (Recall)
        # We search for the whole claim text as a proxy for element search
        results = await hybrid_service.search(claim_text, top_k=5)
        
        found_patent = False
        retrieved_paras = []
        
        for res in results:
            # Check if expected patent is in top 5
            # Mock data might not have 'patent_id' in metadata, using 'id' or default
            meta = res.get('metadata', {})
            pid = meta.get('patent_id', "US20230001MOCK") # Default mock ID
            
            if pid == expected_pid:
                found_patent = True
                retrieved_paras.append({
                    "id": res.get('id', 'unknown'),
                    "text": res.get('text', '')
                })
                print(f"DEBUG: Found chunk ID: {res.get('id', 'unknown')}")
        
        if found_patent:
            recall_hits += 1
            print("  [✓] Recall: Found expected patent in Top 5")
        else:
            print(f"  [✗] Recall: Expected {expected_pid} not found")
            
        # 2. Test Citation Accuracy (LLM)
        # Only run if we found the patent, otherwise we can't test citation
        if found_patent and retrieved_paras:
            # Mock decomposition
            elements = [claim_text] 
            
            # Prepare evidence
            evidence = {
                "patent_id": expected_pid,
                "paragraphs": retrieved_paras
            }
            
            analysis = await llm_service.analyze_patent(claim_text, elements, evidence)
            
            # Check citations
            cited_paras = set()
            for elem_analysis in analysis.element_analysis:
                cited_paras.update(elem_analysis.matched_paragraph_ids)
            
            # Calculate accuracy
            # Did it cite the expected paragraphs?
            # Intersection over Expected (Recall of citations)
            intersection = cited_paras.intersection(expected_paras)
            
            if intersection:
                citation_hits += 1
                print(f"  [✓] Citation: Correctly cited {intersection}")
            else:
                print(f"  [✗] Citation: Failed to cite expected {expected_paras}. Cited: {cited_paras}")
            
            total_citations_checked += 1
            
    # Summary
    print("\n========================================")
    print("EVALUATION RESULTS")
    print("========================================")
    print(f"Recall@5: {recall_hits}/{total_cases} ({recall_hits/total_cases*100:.1f}%)")
    if total_citations_checked > 0:
        print(f"Citation Accuracy: {citation_hits}/{total_citations_checked} ({citation_hits/total_citations_checked*100:.1f}%)")
    else:
        print("Citation Accuracy: N/A (No patents found to check)")

if __name__ == "__main__":
    asyncio.run(evaluate())
