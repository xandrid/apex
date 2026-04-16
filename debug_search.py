import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.services.data_store import LocalDataStore
from app.services.qdrant_vector_store import QdrantVectorStore
from app.services.embedding_gemma import EmbeddingGemmaService

async def main():
    print("--- Debug Search ---")
    
    # 1. Get a chunk
    store = LocalDataStore()
    chunks = store.get_all_chunks()
    if not chunks:
        print("No chunks found.")
        return
        
    target = chunks[0]
    print(f"Target Chunk ID: {target.get('id')}")
    print(f"Target PID: {target.get('metadata', {}).get('patent_id')}")
    print(f"Text Snippet: {target.get('text')[:50]}...")
    
    # 2. Search Qdrant
    qdrant = QdrantVectorStore()
    embedder = EmbeddingGemmaService()
    
    print("Embedding query...")
    emb = embedder.embed_query(target.get('text'))
    
    print("Searching...")
    results = qdrant.search(emb, top_k=5)
    
    print(f"Found {len(results)} results.")
    for i, r in enumerate(results):
        print(f"Rank {i+1}: Score={r['score']:.4f}")
        print(f"  ID: {r['id']}")
        print(f"  PID: {r['metadata'].get('patent_id')}")
        print(f"  Text: {r['text'][:50]}...")
        
    # Check if target is in results
    target_pid = target.get('metadata', {}).get('patent_id')
    found = any(r['metadata'].get('patent_id') == target_pid for r in results)
    print(f"Target Found? {found}")

if __name__ == "__main__":
    asyncio.run(main())
