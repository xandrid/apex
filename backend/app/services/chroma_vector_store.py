import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import os
import uuid
from app.services.vector_store_protocol import VectorStore

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "../../../apex_data/chroma_db")

class ChromaVectorStore(VectorStore):
    """
    ChromaDB implementation for persistent vector storage.
    """
    def __init__(self, collection_name: str = "patent_chunks"):
        print(f"Initializing ChromaDB at {CHROMA_DB_DIR}...")
        self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        
        # Get or create collection
        # Note: We rely on external embedding function (EmbeddingGemma) to provide embeddings,
        # so we don't pass an embedding function here (defaults to None or simple).
        # Actually Chroma requires one if we pass text-only, but we pass embeddings.
        self.collection = self.client.get_or_create_collection(name=collection_name)
        print(f"Chroma Collection '{collection_name}' ready. Count: {self.collection.count()}")

    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        
        # Parse results
        # Chroma returns lists of lists
        match_list = []
        if not results["ids"]:
            return []
            
        ids = results["ids"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]
        distances = results["distances"][0] # Lower is better for L2, but we want similarity?
        # Chroma default is L2. 
        # API expects "score". For L2, score = 1/(1+distance) or just return distance and handle upstream.
        # Let's return similarity = 1 - distance (approx) or just raw distance.
        # HybridSearch expects higher = better.
        # We should strictly configure Chroma to use Cosine if possible, or convert L2.
        # Cosine distance: range 0-2. Similarity = 1 - dist.
        
        for i, m_id in enumerate(ids):
            dist = distances[i]
            # Approximate conversion for compatibility
            score = 1.0 / (1.0 + dist) 
            
            match_list.append({
                "id": m_id,
                "score": score,
                "text": documents[i],
                "metadata": metadatas[i] or {}
            })
            
        return match_list

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        if not chunks:
            return
            
        # Chroma expects lists of items
        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        # Batching is recommended for large inserts
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            self.collection.add(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=texts[i:end],
                metadatas=metadatas[i:end]
            )
        print(f"Added {len(ids)} documents into ChromaDB.")
