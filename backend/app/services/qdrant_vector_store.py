from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any
import uuid
import os
from app.services.vector_store_protocol import VectorStore

class QdrantVectorStore(VectorStore):
    """
    Qdrant implementation for persistent vector storage.
    """
    def __init__(self, collection_name: str = "apex_patents_v1", embedding_dim: int = 768):
        # Default to localhost, but allow ENV override
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        print(f"Initializing Qdrant client at {url} for collection '{collection_name}'...")
        
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        
        # Ensure collection exists
        self._init_collection(embedding_dim)

    def _init_collection(self, dim: int):
        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
            print(f"Qdrant collection '{self.collection_name}' exists.")
        except Exception:
            print(f"Creating Qdrant collection '{self.collection_name}' with dim={dim}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            with_payload=True
        ).points
        
        matches = []
        for r in results:
            matches.append({
                "id": r.id,
                "score": r.score,
                "text": r.payload.get("text", ""),
                "metadata": r.payload.get("metadata", {})
            })
            
        return matches

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        if not chunks:
            return
            
        points = []
        for i, chunk in enumerate(chunks):
            # Qdrant requires UUID or Int ID
            # Our chunk['id'] is likely UUID string already
            uid = chunk.get("id") or str(uuid.uuid4())
            
            points.append(models.PointStruct(
                id=uid,
                vector=embeddings[i],
                payload={
                    "text": chunk["text"],
                    "metadata": chunk["metadata"]
                }
            ))
            
        self.upsert_batch(points)
        print(f"Added {len(points)} documents to Qdrant.")

    def upsert_batch(self, points: List[models.PointStruct]):
        """
        Upserts a batch of points directly.
        """
        if not points:
            return
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
