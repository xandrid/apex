import asyncio
from bigquery_client import BigQueryClient
from ingest import ingest_patents
from chunking import SmartChunker
from app.services.vector_search import VectorSearchService
from app.services.data_store import LocalDataStore
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

async def ingest_golden():
    print("Ingesting Golden Patent...")
    bq = BigQueryClient()
    patents = bq.fetch_by_ids(["US-12019264-B2"])
    
    if not patents:
        print("Failed to fetch Golden Patent!")
        return

    print(f"Fetched {len(patents)} patent(s).")
    
    # Chunk
    all_chunks = []
    for p in patents:
        chunks = SmartChunker.process_patent(p)
        all_chunks.extend(chunks)
        
    print(f"Generated {len(all_chunks)} chunks.")
    
    # Embed
    vector_service = VectorSearchService()
    all_embeddings = []
    for chunk in all_chunks:
        try:
            embedding = vector_service.get_embedding(chunk['text'])
            all_embeddings.append(embedding)
        except Exception as e:
            print(f"Error embedding: {e}")
            all_embeddings.append([0.0]*768)
            
    # Save (Append)
    store = LocalDataStore()
    
    # Load existing
    existing_chunks = store.get_all_chunks()
    existing_embeddings = store.get_all_embeddings()
    
    # Convert existing embeddings to list if numpy
    if hasattr(existing_embeddings, 'tolist'):
        existing_embeddings_list = existing_embeddings.tolist()
    else:
        existing_embeddings_list = []
        
    print(f"Loaded {len(existing_chunks)} existing chunks.")
    
    # Append
    combined_chunks = existing_chunks + all_chunks
    combined_embeddings = existing_embeddings_list + all_embeddings
    
    print(f"Saving total {len(combined_chunks)} chunks...")
    store.save_data(combined_chunks, combined_embeddings)
    
    print("Golden Patent Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(ingest_golden())
