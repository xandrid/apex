import json
import asyncio
import os
import sys
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add backend to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from bigquery_client import BigQueryClient
from chunking import SmartChunker
try:
    from app.services.vector_search import VectorSearchService
    from app.services.data_store import LocalDataStore
except ImportError:
    # Fallback if running from data_pipeline dir without proper package structure
    sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
    from app.services.vector_search import VectorSearchService
    from app.services.data_store import LocalDataStore

# Load env variables correctly using absolute path
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '../backend/.env')
load_dotenv(dotenv_path=env_path)

DATA_DIR = os.path.join(os.path.dirname(__file__), "../apex_data")
PARSED_DIR = os.path.join(DATA_DIR, "patents_parsed")

def ensure_directories():
    if not os.path.exists(PARSED_DIR):
        os.makedirs(PARSED_DIR)

def save_patents_to_jsonl(patents: List[Dict[str, Any]], output_path: str):
    """Saves patents to a single JSONL file."""
    # Ensure dir exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'w') as f:
        for p in patents:
            f.write(json.dumps(p) + '\n')
    print(f"Saved {len(patents)} patents to {output_path}")

def load_patents_from_jsonl(input_path: str) -> List[Dict[str, Any]]:
    """Loads patents from a JSONL file."""
    patents = []
    try:
        with open(input_path, 'r') as f:
            for line in f:
                if line.strip():
                    patents.append(json.loads(line))
    except FileNotFoundError:
        print(f"Error: File {input_path} not found.")
    return patents

async def ingest_corpus(
    source: str = 'bigquery',
    country: str = 'US',
    cpc_prefixes: List[str] = None,
    limit: int = 50,
    output_file: str = None,
    confirm: bool = False
):
    print("Initializing APEX Data Pipeline...")
    ensure_directories()
    
    patents = []

    # 1. Fetch Data
    if source == 'bigquery':
        bq_client = BigQueryClient()
        
        # Guardrail: Check cost first
        print("Estimating BigQuery cost...")
        estimated_bytes = bq_client.fetch_patents(
            limit=limit,
            country_code=country,
            cpc_prefixes=cpc_prefixes,
            dry_run=True
        )
        
        est_mb = estimated_bytes / 1e6
        print(f"Estimated query size: {est_mb:.2f} MB")
        
        if not confirm:
            # Interactive Prompt
            response = input("Do you want to proceed? [y/N]: ")
            if response.lower() != 'y':
                print("Aborted by user.")
                return

        print(f"Fetching max {limit} patents from BigQuery...")
        print(f"filters: Country={country}, CPC={cpc_prefixes}")
        
        patents = bq_client.fetch_patents(
            limit=limit,
            country_code=country,
            cpc_prefixes=cpc_prefixes
        )
        
        if not patents:
            print("No patents fetched.")
            return

        print(f"Fetched {len(patents)} patents.")
        
        # Save if output specified
        if output_file:
            save_patents_to_jsonl(patents, output_file)
    
    elif source == 'local':
        if not output_file:
            # Default fallback or error
            print("Error: --output file must be specified when source is local.")
            return
        print(f"Loading from local file: {output_file}")
        patents = load_patents_from_jsonl(output_file)
        if not patents:
            print("No local patents found.")
            return

    # 2. Process & Chunk
    print(f"Chunking {len(patents)} patents...")
    all_chunks = []
    for patent in patents:
        chunks = SmartChunker.process_patent(patent)
        all_chunks.extend(chunks)
    
    print(f"Total chunks generated: {len(all_chunks)}")

    # 3. Generate Embeddings
    if not all_chunks:
        print("No chunks to embed. Exiting.")
        return

    print("Generating embeddings (using local EmbeddingGemma)...")
    vector_service = VectorSearchService()
    
    all_embeddings = []
    batch_size = 20 # Increased slightly for local processing
    
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        print(f"  Batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}...")
        
        for chunk in batch:
            try:
                embedding = vector_service.get_embedding(chunk['text'])
                if embedding:
                    all_embeddings.append(embedding)
                else:
                    print(f"    Warning: Empty embedding for {chunk['metadata'].get('id')}")
                    all_embeddings.append([0.0] * 768)
            except Exception as e:
                print(f"    Error generating embedding: {e}")
                all_embeddings.append([0.0] * 768)

    # 4. Save Index
    # Note: Currently LocalDataStore overwrites the global index. 
    # Future enhancement: Support named/separated indices.
    from app.services.data_store import LocalDataStore
    store = LocalDataStore()
    store.save_data(all_chunks, all_embeddings)

    print("\nIngestion Pipeline Complete.")
    print(f"Index updated with {len(all_chunks)} chunks.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='APEX Patent Ingestion Tool')
    parser.add_argument('--source', choices=['bigquery', 'local'], default='bigquery', help='Source of data')
    parser.add_argument('--country', type=str, default='US', help='Country code (e.g., US)')
    parser.add_argument('--cpc_prefixes', type=str, help='Comma-separated CPC prefixes (e.g., G06,H04)')
    parser.add_argument('--limit', type=int, default=50, help='Max patents to fetch')
    parser.add_argument('--output', type=str, default=os.path.join(PARSED_DIR, "latest_corpus.jsonl"), help='Path to save/load JSONL')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()
    
    prefixes = args.cpc_prefixes.split(',') if args.cpc_prefixes else None
    
    asyncio.run(ingest_corpus(
        source=args.source,
        country=args.country,
        cpc_prefixes=prefixes,
        limit=args.limit,
        output_file=args.output,
        confirm=args.yes
    ))
