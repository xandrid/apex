import os
import time
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient,models
from qdrant_client.http import models as rest
from dotenv import load_dotenv

load_dotenv()

class QdrantVectorStore:
    def __init__(self, collection_name: str = "apex_patents_v1"):
        self.collection_name = collection_name
        
        # Connect to local Qdrant
        # Assuming docker-compose is running on localhost:6333
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY", None)
        
        print(f"Connecting to Qdrant at {self.url}...")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        
        self.vector_size = 384 # all-MiniLM-L6-v2
        self._ensure_collection()

    def _ensure_collection(self):
        """
        Creates the collection if it doesn't exist.
        Configured for on_disk vectors (Memmap) for scale.
        """
        if not self.client.collection_exists(self.collection_name):
            print(f"Creating collection '{self.collection_name}'...")
            
            # Vectors Config (Dense)
            # Efficient HNSW for disk usage (m=16, ef=100)
            vectors_config = {
                "dense": models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                    on_disk=True, # Critical for RAM saving
                )
            }
            
            # Sparse Vectors Config (for Hybrid Search)
            sparse_vectors_config = {
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        on_disk=True # Also on disk
                    )
                )
            }

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
                # Optimizers
                optimizers_config=models.OptimizersConfigDiff(
                    memmap_threshold=20000 # Map to disk early
                )
            )
            print("Collection created successfully.")
        else:
            print(f"Collection '{self.collection_name}' exists.")

    def upsert_batch(self, points: List[models.PointStruct]):
        """
        Upserts a batch of points.
        """
        if not points:
            return
            
        # Retry logic could be added here
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=False # Async compatible
            )
        except Exception as e:
            print(f"Error upserting batch: {e}")
            raise e

    def count(self) -> int:
        return self.client.count(self.collection_name).count

    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """
        Performs dense vector search using Qdrant.
        """
        # Dense Search using Query API (query_points)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            using="dense",
            limit=top_k,
            with_payload=True
        )
        
        results = response.points
        
        # Convert to standard format
        matches = []
        for hit in results:
            matches.append({
                "id": hit.id, # Qdrant ID (UUID)
                "score": hit.score,
                "text": hit.payload.get('text', ''), # Needs to be in payload!
                "metadata": hit.payload
            })
        return matches

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Adds documents to Qdrant.
        chunks: List of specific chunk format (text, metadata).
        embeddings: List of vectors.
        """
        from qdrant_client.models import PointStruct
        import uuid
        
        points = []
        for i, chunk in enumerate(chunks):
            # Generate UUID
            unique_str = f"{chunk['metadata'].get('publication_number', 'unknown')}_{chunk['metadata'].get('id', i)}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_str))
            
            payload = chunk.get('metadata', {}).copy()
            payload['text'] = chunk.get('text', '')
            
            points.append(PointStruct(
                id=point_id,
                vector={"dense": embeddings[i]},
                payload=payload
            ))
            
        self.upsert_batch(points)

