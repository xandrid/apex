import sys
import os
import json
import asyncio
from typing import List

# Ensure backend path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
from dotenv import load_dotenv
load_dotenv(dotenv_path='../backend/.env')

from app.services.vector_search import VectorSearchService

DATA_DIR = os.path.join(os.path.dirname(__file__), "../apex_data")
EVAL_DIR = os.path.join(DATA_DIR, "eval/v1")
GOLDEN_FILE = os.path.join(EVAL_DIR, "golden_dataset.json")

async def run_sanity_check():
    print("--- Evaluation Sanity Check ---")
    
    if not os.path.exists(GOLDEN_FILE):
        print(f"Error: Golden file not found at {GOLDEN_FILE}")
        return

    with open(GOLDEN_FILE, 'r') as f:
        golden_data = json.load(f)
        
    print(f"Loaded {len(golden_data)} queries from golden dataset.")
    
    # Initialize Search Service
    print("Initializing Vector Search...")
    search_service = VectorSearchService()
    
    # Check a few
    passed = 0
    checked = 0
    limit = 5
    
    for query_item in golden_data[:limit]:
        checked += 1
        qid = query_item['query_id']
        qtext = query_item['query_text']
        relevant_docs = set(query_item['relevant_docs'])
        
        print(f"\nQuery: {qid}")
        print(f"  Snippet: {qtext[:60]}...")
        print(f"  Targets: {list(relevant_docs)[:3]}... (Total {len(relevant_docs)})")
        
        # Search
        results = await search_service.search(qtext, top_k=20)
        
        # Check recall
        hits = []
        for match in results:
            # Metadata structure depends on chunking. Usually metadata['publication_number'] or similar.
            # In SmartChunker, metadata includes 'id' which is likely 'pub_num_pXX'.
            # We need the parent ID.
            
            # The ingest script saved metadata. Let's assume 'publication_number' is in metadata 
            # OR we can parse it from 'id'.
            found_id = match.metadata.get('publication_number')
            if not found_id and 'id' in match.metadata:
                # heuristic: US-XXXXXX-B2_p0 -> US-XXXXXX-B2
                found_id = match.metadata['id'].split('_p')[0]
                
            if found_id in relevant_docs:
                hits.append(found_id)
        
        unique_hits = set(hits)
        print(f"  Found {len(unique_hits)} relevant docs in top-20: {unique_hits}")
        
        if unique_hits:
            passed += 1
            print("  [SUCCESS]")
        else:
            print("  [FAIL]")

    print(f"\nSanity Check Logic: {passed}/{checked} queries found at least one relevant doc.")

if __name__ == "__main__":
    asyncio.run(run_sanity_check())
