import numpy as np
from typing import List, Dict, Any, Optional
# from rank_bm25 import BM25Okapi # Removed
from .vector_search import VectorSearchService, get_vector_service
# from app.services.data_store import LocalDataStore # Removed
from app.services.retrieval.base import Retriever, SearchResult

class HybridRetriever(Retriever):
    def __init__(self):
        self.vector_service = get_vector_service() # Use the singleton/factory
        from app.services.lexical_search import LexicalSearchService
        self.lexical_service = LexicalSearchService()
        
    def _initialize_index(self):
        pass # Scalable service doesn't need in-memory init

    async def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Performs scalable hybrid retrieval (Qdrant Dense + SQLite FTS5).
        """
        # 1. Vector Search
        # Fetch more for fusion (e.g. top_k * 2)
        vector_matches_raw = await self.vector_service.search(query, top_k=top_k * 2)
        
        vector_results = []
        for m in vector_matches_raw:
            vector_results.append({
                "id": m.paragraph_id,
                "score": m.similarity_score,
                "text": m.text,
                "metadata": m.metadata
            })
            
        # 2. Lexical Search
        keyword_results = self.lexical_service.search(query, top_k=top_k * 2)
        
        # 3. Fusion (RRF)
        fused_docs = self._combine_scores(vector_results, keyword_results, top_k=top_k)
        
        # Output
        output = []
        for i, doc in enumerate(fused_docs):
            output.append(SearchResult(
                id=doc["id"],
                text=doc.get("text", ""),
                score=doc["score"], # RRF Score
                metadata=doc.get("metadata", {}),
                vector_score=doc.get("vector_score", 0.0), # Original vector score if present
                rank=i+1
            ))

        return output
        
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Backward compatibility wrapper.
        """
        results = await self.retrieve(query, top_k)
        return [r.model_dump() for r in results]

    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Delegates to LexicalSearchService.
        """
        return self.lexical_service.search(query, top_k=top_k)

    def _combine_scores(self, vector_results: List[Dict], keyword_results: List[Dict], top_k: int) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF)
        score = 1 / (k + rank)
        """
        k = 60
        doc_scores = {}
        
        # Process Vector Ranks
        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"score": 0, "doc": doc, "vector_score": doc["score"]}
            else:
                # If already present (from keyword?), keep the max vector score if available
                doc_scores[doc_id]["vector_score"] = max(doc_scores[doc_id].get("vector_score", 0), doc["score"])
            
            doc_scores[doc_id]["score"] += 1 / (k + rank + 1)
            
        # Process Keyword Ranks
        for rank, doc in enumerate(keyword_results):
            doc_id = doc["id"]
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"score": 0, "doc": doc}
            doc_scores[doc_id]["score"] += 1 / (k + rank + 1)
            
        # Convert to list and sort
        final_results = [val["doc"] for val in doc_scores.values()]
        # Update scores to RRF scores but keep vector_score
        for doc in final_results:
            doc["score"] = doc_scores[doc["id"]]["score"]
            doc["vector_score"] = doc_scores[doc["id"]].get("vector_score", 0.0)
            
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:top_k]

# Alias for backward compatibility
HybridSearchService = HybridRetriever
