from typing import List, Protocol, Dict, Any

class VectorStore(Protocol):
    """
    Interface for vector storage backends (Local, ChromaDB, Qdrant).
    """
    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """
        Returns a list of matches.
        Each match must have: {'id': str, 'score': float, 'metadata': dict, 'text': str}
        """
        ...
        
    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Adds documents and their embeddings to the store.
        """
        ...
