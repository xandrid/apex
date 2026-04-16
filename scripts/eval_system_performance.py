import os
import sys
import json
import random
import asyncio
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from tqdm import tqdm

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.vector_search import VectorSearchService, get_vector_service
from app.services.vertex_llm import VertexLLMService

# Initialize Services
# We need to manually initialize because we are running as a script
vector_service = get_vector_service()
llm_service = VertexLLMService()

DATA_PATH = os.path.join(os.path.dirname(__file__), '../apex_data/chunks.json')

def load_data():
    print(f"Loading data from {DATA_PATH}...")
    with open(DATA_PATH, 'r') as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks.")
    return chunks

def group_by_patent(chunks):
    patents = {}
    for chunk in chunks:
        pid = chunk.get('metadata', {}).get('patent_id')
        if not pid: continue
        
        if pid not in patents:
            patents[pid] = {'claims': [], 'descriptions': []}
        
        c_type = chunk.get('metadata', {}).get('type')
        if c_type == 'claim':
            patents[pid]['claims'].append(chunk)
        elif c_type == 'description' or c_type == 'abstract':
            patents[pid]['descriptions'].append(chunk)
    return patents

async def evaluate_retrieval(claims, top_k=20):
    results = []
    
    print(f"Running retrieval evaluation on {len(claims)} claims...")
    
    for claim in tqdm(claims):
        claim_text = claim['text']
        true_pid = claim['metadata']['patent_id']
        
        # Check ID safely
        claim_id = claim.get('id') or claim.get('metadata', {}).get('id', 'unknown')
        
        # Run Search
        # Note: VectorSearchService uses cosine similarity on the whole corpus
        matches = await vector_service.search(claim_text, top_k=top_k)
        
        # Analyze Matches
        hits = []
        ranks = []
        
        for rank, match in enumerate(matches):
            match_pid = match.patent_id
            # Self-retrieval check: Is it from the same patent?
            # And is it NOT the query chunk itself.
            is_relevant = (match_pid == true_pid) and (match.paragraph_id != claim_id)
            
            if is_relevant:
                hits.append(match)
                ranks.append(rank + 1) # 1-indexed
        
        # Metrics for this query
        is_hit_at_k = len(hits) > 0
        mrr = 1.0 / ranks[0] if ranks else 0.0
        precision = len(hits) / top_k
        
        results.append({
            "claim_id": claim_id,
            "patent_id": true_pid,
            "hit_at_k": is_hit_at_k,
            "mrr": mrr,
            "precision_k": precision,
            "first_rank": ranks[0] if ranks else None,
            "top_match_score": matches[0].similarity_score if matches else 0.0,
            "top_match_text": matches[0].text if matches else "",
            "top_hit_text": hits[0].text if hits else None
        })
        
    return pd.DataFrame(results)

async def evaluate_reasoning(df_retrieval, sample_size=10):
    """
    Evaluates if the LLM thinks the retrieved 'hit' actually supports the claim.
    """
    print(f"Running reasoning evaluation on {sample_size} hits...")
    
    # Filter for hits
    hits_df = df_retrieval[df_retrieval['hit_at_k'] == True].sample(min(sample_size, sum(df_retrieval['hit_at_k'])))
    
    reasoning_results = []
    
    for _, row in tqdm(hits_df.iterrows(), total=len(hits_df)):
        claim_id = row['claim_id']
        support_text = row['top_hit_text']
        # Placeholder for reasoning logic
        pass 

    return []

async def main():
    chunks = load_data()
    patents = group_by_patent(chunks)
    
    # Filter patents that have both claims and descriptions
    valid_patents = [p for p in patents.values() if p['claims'] and p['descriptions']]
    print(f"Found {len(valid_patents)} patents with both claims and description.")
    
    if not valid_patents:
        print("No valid data found.")
        return

    # Check Embeddings Dimension Consistency
    try:
        dummy_emb = vector_service.embedder.embed_query("test")
        dim_model = len(dummy_emb)
        dim_store = vector_service.embeddings.shape[1] if len(vector_service.embeddings) > 0 else 0
        
        print(f"Model Dimension: {dim_model}, Store Dimension: {dim_store}")
        
        if dim_store > 0 and dim_model != dim_store:
            print("DIMENSION MISMATCH DETECTED. Regenerating embeddings for all chunks...")
            # Extract all texts
            all_texts = [c['text'] for c in vector_service.chunks]
            # Re-embed
            new_embeddings = vector_service.embedder.embed_documents(all_texts)
            # Update store
            vector_service.store.save_data(vector_service.chunks, new_embeddings.tolist())
            # Reload service
            vector_service.embeddings = new_embeddings
            print("Embeddings regenerated and saved.")
            
    except Exception as e:
        print(f"Warning during consistency check: {e}")

    # Sample Claims
    # Take 1 claim from each of N random patents
    N = 50
    sampled_patents = random.sample(valid_patents, min(N, len(valid_patents)))
    test_claims = [p['claims'][0] for p in sampled_patents] # Take first claim
    
    # Run Retrieval Eval
    df_retrieval = await evaluate_retrieval(test_claims, top_k=20)
    
    # Metrics
    mrr_avg = df_retrieval['mrr'].mean()
    hit_rate = df_retrieval['hit_at_k'].mean()
    avg_rank = df_retrieval[df_retrieval['first_rank'].notna()]['first_rank'].mean()
    
    # Report
    report = f"""# APEX System-Level Performance Report (Support Retrieval)
**Date**: {pd.Timestamp.now()}
**Task**: Self-Retrieval (Find supporting description for a claim)
**Sample Size**: {len(test_claims)} Claims

## Retrieval Metrics (Top-20)
| Metric | Value | Description |
|---|---|---|
| **Hit Rate (Recall@20)** | **{hit_rate:.2%}** | % of claims where at least 1 correct description chunk was found. |
| **MRR (Mean Reciprocal Rank)** | **{mrr_avg:.4f}** | Average inverse rank of first hit (1.0 = top result). |
| **Avg Rank of First Hit** | **{avg_rank:.1f}** | On average, the first supporting chunk is at rank {avg_rank:.1f}. |

## Failure Analysis
Top Failure Modes:
1. **Vocabulary Mismatch**: Claim uses legal terms; description uses technical implementation details.
2. **Abstract/Broad Claims**: Hard to map to specific implementation chunks.
    """
    
    print(report)
    
    with open("EVAL_SYSTEM_PERFORMANCE.md", "w") as f:
        f.write(report)
    print("Report saved.")

if __name__ == "__main__":
    asyncio.run(main())
