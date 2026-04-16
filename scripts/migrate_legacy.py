import asyncio
import os
import sys

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
from dotenv import load_dotenv
load_dotenv()

from app.services.data_store import LocalDataStore
from app.services.qdrant_vector_store import QdrantVectorStore
from app.services.embedding_gemma import EmbeddingGemmaService
from qdrant_client.models import PointStruct
import uuid

async def migrate():
    print("--- Migrating Legacy Data to Qdrant (Partial) ---")
    
    # 1. Load Legacy Data
    store = LocalDataStore()
    chunks = store.get_all_chunks()
    # Limit for quick verification
    chunks = chunks[:1500] 
    print(f"Loaded {len(chunks)} chunks (Partial Limit).")
    
    if not chunks:
        print("No chunks to migrate.")
        return

    # 2. Embed
    embedder = EmbeddingGemmaService()
    texts = [c['text'] for c in chunks]
    
    print("Generating embeddings...")
    # Process in batches
    BATCH_SIZE = 64
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i+BATCH_SIZE]
        print(f"Embedding batch {i}/{len(texts)}...")
        emb_batch = embedder.embed_documents(batch_texts)
        all_embeddings.extend(emb_batch)
        
    print(f"Generated {len(all_embeddings)} embeddings.")

    # 3. Upsert to Qdrant
    qdrant = QdrantVectorStore()
    points = []
    
    print("Preparing Qdrant points...")
    for i, chunk in enumerate(chunks):
        # Stable UUID
        unique_str = f"{chunk['metadata'].get('publication_number', 'unknown')}_{chunk['metadata'].get('id', i)}"
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_str))
        
        payload = {
            "text": chunk.get('text', ''),
            "metadata": chunk.get('metadata', {})
        }
        
        points.append(PointStruct(
            id=point_id,
            vector=all_embeddings[i].tolist(), # Unnamed vector
            payload=payload
        ))
        
    print(f"Upserting {len(points)} points to Qdrant...")
    # Upsert in chunks
    for i in range(0, len(points), 100):
        batch = points[i:i+100]
        qdrant.client.upsert(
            collection_name=qdrant.collection_name,
            points=batch,
            wait=False
        )
        
    print("Migration Complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
