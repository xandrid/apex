import json
import os
import random
import re

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "../apex_data")
CHUNKS_FILE = os.path.join(DATA_DIR, "chunks.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "eval_set.json")
SAMPLE_SIZE = 20  # Start small for rapid iteration

def generate_test_set():
    if not os.path.exists(CHUNKS_FILE):
        print(f"Error: {CHUNKS_FILE} not found. Run ingestion first.")
        return

    print(f"Loading chunks from {CHUNKS_FILE}...")
    with open(CHUNKS_FILE, "r") as f:
        chunks = json.load(f)

    # Group by patent_id
    patents = {}
    for c in chunks:
        pid = c['metadata']['patent_id']
        if pid not in patents:
            patents[pid] = {"claims": [], "abstract": "", "title": c['metadata'].get("title", "")}
        
        ctype = c['metadata'].get('type', '')
        if "claim" in ctype:
            patents[pid]["claims"].append(c['text'])
        elif "abstract" in ctype:
            patents[pid]["abstract"] = c['text']

    print(f"Found {len(patents)} unique patents.")

    # Select candidates (must have claims)
    candidates = [pid for pid, data in patents.items() if data["claims"]]
    
    if len(candidates) < SAMPLE_SIZE:
        print(f"Warning: Only {len(candidates)} candidates found. Using all.")
        selected_ids = candidates
    else:
        selected_ids = random.sample(candidates, SAMPLE_SIZE)

    eval_set = []
    for pid in selected_ids:
        # Heuristic: Take the first claim chunk. 
        # Ideally we'd parse specifically for "Claim 1", but chunking might have split it.
        # We'll take the first non-empty claim chunk.
        claim_text = patents[pid]["claims"][0]
        
        eval_set.append({
            "patent_id": pid,
            "title": patents[pid]["title"],
            "claim_text": claim_text,
            "gold_standard": pid # The patent itself is the target
        })

    print(f"Generated {len(eval_set)} evaluation cases.")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(eval_set, f, indent=2)
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_test_set()
