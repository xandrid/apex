from typing import List, Dict, Any
import numpy as np
from app.services.vector_store_protocol import VectorStore
from app.services.data_store import LocalDataStore

class LocalVectorStore(VectorStore):
    """
    Adapter for the legacy LocalDataStore (numpy/json).
    """
    def __init__(self):
        self.store = LocalDataStore()
        # Pre-load data
        self.embeddings = self.store.get_all_embeddings()
        self.chunks = self.store.get_all_chunks()
        
    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        if len(self.embeddings) == 0:
            return []
            
        q_emb = np.array(query_embedding, dtype="float32")
        
        # Cosine Similarity
        # Assuming normalized embeddings? If not, we should normalize.
        # But for now, we trust the embedder.
        scores = np.dot(self.embeddings, q_emb)
        
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        matches = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            matches.append({
                "id": chunk['metadata'].get('id', 'unknown'),
                "score": float(scores[idx]),
                "text": chunk.get('text', ''),
                "metadata": chunk.get('metadata', {})
            })
            
        return matches

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        # Local store relies on file reload, so this is a no-op or requires file writing.
        # For abstraction sake, we pass. The Data Pipeline handles file writing.
        pass
