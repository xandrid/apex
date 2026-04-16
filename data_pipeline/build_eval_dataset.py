import os
import random
import json
import argparse
from typing import List, Set, Dict, Any
from dotenv import load_dotenv

# Ensure backend path is available
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from bigquery_client import BigQueryClient

# Correctly locate .env relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '../backend/.env')
load_dotenv(dotenv_path=env_path)

DATA_DIR = os.path.join(os.path.dirname(__file__), "../apex_data")
EVAL_DIR = os.path.join(DATA_DIR, "eval/v1")

def ensure_dirs():
    if not os.path.exists(EVAL_DIR):
        os.makedirs(EVAL_DIR)

def clean_text(text: str) -> str:
    """Normalizes whitespace."""
    return " ".join(text.split())

def extract_claim_1(claims_text: str) -> str:
    """
    Heuristic extraction of Claim 1.
    Assumes claims are numbered "1. ... 2. ...".
    This is a simplification. Real parsing is harder.
    """
    if not claims_text:
        return ""
    
    # Simple split by "2. "
    # Note: This is fragile but sufficient for MVP grounding if text is relatively clean.
    # A better approach (future) is a regex for `^\s*1\.` and stop at `^\s*2\.`
    
    # Normalized search
    normalized = clean_text(claims_text)
    
    # Try to find "1. "
    start_idx = normalized.find("1. ")
    if start_idx == -1:
         # Fallback: return first 500 chars if no "1." found (bad data)
         return normalized[:500]
    
    # Try to find "2. " after that
    end_idx = normalized.find(" 2. ", start_idx)
    if end_idx == -1:
        return normalized[start_idx:]
    
    return normalized[start_idx:end_idx]

def build_dataset(probe_limit: int = 50, corpus_target_size: int = 2000, seed: int = 42):
    random.seed(seed)
    bq = BigQueryClient()
    ensure_dirs()
    
    print(f"--- Building Evaluation Corpus (Seed={seed}) ---")
    
    # 1. Fetch Probes (Query Set)
    print(f"Fetching {probe_limit} potential Probe Patents...")
    # Fetch slightly more to account for filters
    raw_probes = bq.fetch_patents(
        limit=probe_limit * 2, 
        country_code='US', 
        cpc_prefixes=['G06', 'H04'],
        start_date=20230101 # Recent patents
    )
    
    valid_probes = []
    ground_truth_map: Dict[str, List[str]] = {} # ProbeID -> [CitedID]
    all_cited_ids: Set[str] = set()
    
    stats = {
        "fetched_probes": len(raw_probes),
        "filtered_no_citations": 0,
        "citation_total": 0,
        "citation_kept": 0,
        "citation_filtered_non_us": 0,
        "citation_filtered_missing": 0
    }

    for p in raw_probes:
        if len(valid_probes) >= probe_limit:
            break
            
        pid = p['publication_number']
        citations = p.get('citations', [])
        
        if not citations:
            stats["filtered_no_citations"] += 1
            continue
            
        # Filter Citations (US only)
        valid_citations = []
        for cite in citations:
            stats["citation_total"] += 1
            if not cite:
                stats["citation_filtered_missing"] += 1
                continue
            if not cite.startswith("US-"):
                stats["citation_filtered_non_us"] += 1
                continue
            
            valid_citations.append(cite)
            stats["citation_kept"] += 1

        if not valid_citations:
            stats["filtered_no_citations"] += 1
            continue

        # Valid Probe
        # Extract Claim 1
        claim_1 = extract_claim_1(p.get('claims', ''))
        if len(claim_1) < 50: # Too short / bad parse
             continue

        valid_probes.append({
            "query_id": pid,
            "query_text": claim_1,
            # Store full metadata just in case, but golden dataset needs specific format
        })
        
        ground_truth_map[pid] = valid_citations
        all_cited_ids.update(valid_citations)

    print(f"Selected {len(valid_probes)} Probes.")
    print(f"Collected {len(all_cited_ids)} unique Cited IDs (Ground Truth).")
    print("Stats:", json.dumps(stats, indent=2))

    # 2. Fetch Corpus Part A: Cited Patents
    print("\nFetching Full Text for Cited Patents...")
    cited_patents = bq.fetch_by_ids(list(all_cited_ids))
    print(f"Successfully fetched {len(cited_patents)}/{len(all_cited_ids)} cited patents.")
    
    found_cited_ids = {p['publication_number'] for p in cited_patents}
    
    # Update Ground Truth to only include what we actually found
    final_golden = []
    for probe in valid_probes:
        pid = probe['query_id']
        original_cites = ground_truth_map[pid]
        found_cites = [c for c in original_cites if c in found_cited_ids]
        
        if found_cites:
            final_golden.append({
                "query_id": pid,
                "query_text": probe['query_text'],
                "relevant_docs": found_cites
            })
    
    print(f"Refined Golden Dataset: {len(final_golden)} queries with retrievable citations.")

    # 3. Fetch Corpus Part B: Distractors
    current_corpus_size = len(cited_patents)
    needed_distractors = max(0, corpus_target_size - current_corpus_size)
    
    distractors = []
    if needed_distractors > 0:
        print(f"\nFetching {needed_distractors} Distractors...")
        # We need to ensure no overlap.
        # Strategy: Fetch extra, filter out probes and cited.
        
        # We assume fetch_patents returns random-ish recent patents
        # We might need to offset or just fetch a large batch
        exclude_ids = all_cited_ids.union({p['query_id'] for p in valid_probes})
        
        raw_distractors = bq.fetch_patents(
            limit=needed_distractors * 2,
            country_code='US',
            start_date=20220101 # Slightly wider window
        )
        
        for p in raw_distractors:
            pid = p['publication_number']
            if pid not in exclude_ids:
                distractors.append(p)
                exclude_ids.add(pid) # Prevent dupes within list
                if len(distractors) >= needed_distractors:
                    break
                    
        print(f"Fetched {len(distractors)} valid distractors.")

    # 4. Save Artifacts
    
    # corpus.jsonl
    corpus_file = os.path.join(EVAL_DIR, "corpus.jsonl")
    full_corpus = cited_patents + distractors
    with open(corpus_file, 'w') as f:
        for p in full_corpus:
            f.write(json.dumps(p) + '\n')
            
    # golden_dataset.json
    golden_file = os.path.join(EVAL_DIR, "golden_dataset.json")
    with open(golden_file, 'w') as f:
        json.dump(final_golden, f, indent=2)
        
    # manifest.json
    manifest = {
        "seed": seed,
        "version": "v1",
        "timestamp": "2025-12-11",
        "parameters": {
            "probe_limit": probe_limit,
            "corpus_target_size": corpus_target_size,
            "filters": "US Only, G06/H04",
        },
        "stats": {
            "num_queries": len(final_golden),
            "num_corpus": len(full_corpus),
            "num_distractors": len(distractors),
            "num_cited_found": len(cited_patents)
        },
        "query_ids": [q['query_id'] for q in final_golden],
        "corpus_ids": [p['publication_number'] for p in full_corpus]
    }
    manifest_file = os.path.join(EVAL_DIR, "manifest.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"\n--- DONE ---")
    print(f"Corpus saved to: {corpus_file}")
    print(f"Golden dataset saved to: {golden_file}")
    print(f"Manifest saved to: {manifest_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=5, help='Number of probes')
    parser.add_argument('--corpus_size', type=int, default=50, help='Total corpus size')
    args = parser.parse_args()
    
    build_dataset(probe_limit=args.limit, corpus_target_size=args.corpus_size)
