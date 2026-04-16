import os
import sys
import json
import random
import asyncio
import numpy as np
import pandas as pd
from tqdm import tqdm

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.retrieval.factory import get_retriever

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

import time

async def evaluate_mode(mode: str, test_claims: list):
    print(f"\nEvaluating mode: {mode}")
    retriever = get_retriever(mode)
    
    results = []
    
    for claim in tqdm(test_claims):
        query = claim['text']
        true_pid = claim['metadata']['patent_id']
        
        start_t = time.perf_counter()
        # Retrieve
        search_results = await retriever.retrieve(query, top_k=50) # Fetch top 50
        duration = time.perf_counter() - start_t
        
        # Check hits
        hits = [r for r in search_results if r.metadata.get('patent_id') == true_pid]
        
        # Ranks of correct hits (1-based)
        ranks = [r.rank for r in hits]
        
        res = {
            "mode": mode,
            "mrr": 1.0 / ranks[0] if ranks else 0.0,
            "latency": duration
        }
        
        for k in [1, 5, 10, 20, 50]:
            res[f"hit_at_{k}"] = any(r <= k for r in ranks)
            
        results.append(res)
        
    df = pd.DataFrame(results)
    return df

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100, help='Number of patents to test')
    args = parser.parse_args()

    chunks = load_data()
    patents = group_by_patent(chunks)
    
    # Filter patents that have both claims and descriptions (valid for self-retrieval test)
    valid_patents = [p for p in patents.values() if p['claims'] and p['descriptions']]
    print(f"Found {len(valid_patents)} valid patents for evaluation.")
    
    if not valid_patents:
        print("No valid data found.")
        return

    # Sample Claims (1 per patent)
    # Using all valid patents for better stats, or sample if too large
    limit = args.limit
    test_claims = [p['claims'][0] for p in valid_patents[:limit]]
    print(f"Testing on {len(test_claims)} claims (Limit: {limit}).")
    
    modes = ["hybrid", "qdrant_dense"]
    final_results = []
    
    for mode in modes:
        df = await evaluate_mode(mode, test_claims)
        
        metrics = {
            "Mode": mode,
            "MRR": df['mrr'].mean(),
            "Avg Latency (s)": df['latency'].mean()
        }
        for k in [1, 5, 10, 20, 50]:
            metrics[f"Recall@{k}"] = df[f"hit_at_{k}"].mean()
            
        final_results.append(metrics)
        
    # Display Leaderboard
    leaderboard = pd.DataFrame(final_results)
    # Reorder columns
    cols = ["Mode", "Recall@1", "Recall@5", "Recall@10", "Recall@20", "Recall@50", "MRR", "Avg Latency (s)"]
    leaderboard = leaderboard[cols]
    
    print("\n=== RETRIEVAL LEADERBOARD ===")
    print(leaderboard.to_markdown(index=False))
    
    # Save to RESULTS.md
    with open("RESULTS_V2.md", "w") as f:
        f.write("# Retrieval System Evaluation Results (V2)\n\n")
        f.write(leaderboard.to_markdown(index=False))
    
    print("\nSaved to RESULTS_V2.md")

if __name__ == "__main__":
    asyncio.run(main())
