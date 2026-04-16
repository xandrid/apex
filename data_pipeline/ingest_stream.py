import os
import json
import asyncio
import argparse
from typing import List, Dict, Any, Generator
from datetime import datetime

# Adjust paths
# Fix paths
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(script_dir)) # Add root (apex-app)
sys.path.append(os.path.join(script_dir, '../backend'))

from dotenv import load_dotenv
env_path = os.path.join(script_dir, '../backend/.env')
load_dotenv(dotenv_path=env_path)

from app.services.embedding_gemma import EmbeddingGemmaService
from app.services.qdrant_vector_store import QdrantVectorStore
from data_pipeline.chunking import SmartChunker
from data_pipeline.bigquery_client import BigQueryClient

# Constants
CHECKPOINT_FILE = os.path.join(script_dir, "../../ingest_state.json")
if os.path.exists("E:/apex/ingest_state.json"):
    CHECKPOINT_FILE = "E:/apex/ingest_state.json"

BATCH_SIZE_FETCH = 100 # Patents per BQ fetch
BATCH_SIZE_UPSERT = 64 # Points per Qdrant upsert

def load_checkpoint() -> int:
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_processed_date', 0)
        except:
            return 0
    return 0

def save_checkpoint(date_int: int):
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({'last_processed_date': date_int, 'updated_at': str(datetime.now())}, f)

def get_patent_stream(client: BigQueryClient, start_date: int, limit: int) -> Generator[List[Dict], None, None]:
    """
    Yields batches of patents from BigQuery.
    Ideally BQ client should support pagination or cursor.
    For now, we simulate streaming by fetching in chunks if implemented,
    or just one big fetch if the client is limited. 
    
    Update: The BigQueryClient.fetch_patents is simple. 
    For true "Scanning", we generally use `LIMIT N OFFSET M` or iterate by date.
    Iterating by date is safer for massive offsets.
    """
    # Simple iterator implementation:
    # We will assume calling fetch_patents with a limit is okay for "Phase 2" 
    # if we manage the loop externally or if fetch_patents returns a generator.
    # Current BigQueryClient fetch_patents returns a LIST.
    # So for this script, we'll fetch once (or in pages if we modify client).
    
    # Let's trust the Limit for now.
    offset = 0
    # Note: BQ LIMIT/OFFSET is expensive (scan).
    # Better: WHERE date >= last_seen_date AND publication_number > last_seen_id
    
    # MVP Phase 2: Just fetch the requested limit.
    patents = client.fetch_patents(limit=limit, start_date=start_date, country_code='US')
    
    # Yield in small batches to manage local RAM during chunk/embed
    for i in range(0, len(patents), BATCH_SIZE_FETCH):
        yield patents[i:i+BATCH_SIZE_FETCH]

async def ingest_stream(limit: int = 1000, start_date: int = 20240101, reset_checkpoint: bool = False):
    print(f"--- Streaming Ingestion (Limit: {limit}) ---")
    
    if reset_checkpoint:
        print("Resetting checkpoint...")
        save_checkpoint(0)
        current_date = start_date
    else:
        last_date = load_checkpoint()
        current_date = max(start_date, last_date)
        print(f"Resuming from date: {current_date}")

    from app.services.lexical_search import LexicalSearchService # Import here to avoid circular
    
    # Initialize Services
    bq_client = BigQueryClient()
    embedder = EmbeddingGemmaService()
    vector_store = QdrantVectorStore(collection_name="apex_patents_v1")
    lexical_store = LexicalSearchService()
    
    if reset_checkpoint:
       lexical_store.reset()
    
    total_processed = 0
    
    # Stream Batches
    stream = get_patent_stream(bq_client, start_date=current_date, limit=limit)
    
    for batch_patents in stream:
        print(f"Processing batch of {len(batch_patents)} patents...")
        
        # 1. Chunking
        batch_chunks = []
        for p in batch_patents:
            chunks = SmartChunker.process_patent(p)
            batch_chunks.extend(chunks)
            
        if not batch_chunks:
            continue
            
        print(f"  Generated {len(batch_chunks)} chunks.")
        
        # We process chunks in mini-batches to avoid OOM or slow embedding steps
        for i in range(0, len(batch_chunks), BATCH_SIZE_UPSERT):
            chunk_sub_batch = batch_chunks[i:i+BATCH_SIZE_UPSERT]
            texts = [c['text'] for c in chunk_sub_batch]
            
            # Embed
            try:
                embeddings = embedder.embed_documents(texts)
            except Exception as e:
                print(f"  Error embedding batch: {e}")
                continue

            # Delegate to vector store (handles point creation)
            if embeddings.size > 0: # Check if numpy array is valid
                 # convert to list of lists
                 emb_list = embeddings.tolist()
                 vector_store.add_documents(chunk_sub_batch, emb_list)
                 lexical_store.add_documents(chunk_sub_batch)
        
        total_processed += len(batch_patents)
        print(f"  Upserted chunks for {len(batch_patents)} patents. Total: {total_processed}")
        
        # Simple Checkpoint: Just update date?
        # Since we fetch one big BQ list, this checkpoint is coarse.
        # Ideally we'd loop BQ by date.
        
    print("Ingestion Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--start_date', type=int, default=20240101)
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()
    
    asyncio.run(ingest_stream(args.limit, args.start_date, args.reset))
