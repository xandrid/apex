from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from app.services.retrieval.base import SearchResult

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        print(f"Loading Reranker model: {model_name}...")
        self.model = CrossEncoder(model_name)
        print("Reranker model loaded.")

    def rerank(self, query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        if not results:
            return []

        # Prepare pairs for cross-encoder
        pairs = [[query, res.text] for res in results]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Update scores and sort
        for res, score in zip(results, scores):
            res.score = float(score) # Update the main score to the reranker score
            # We preserve vector_score in metadata or separate field if needed, 
            # but SearchResult has vector_score, so that stays.
        
        # Sort by new score
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Re-assign ranks
        reranked = results[:top_k]
        for i, res in enumerate(reranked):
            res.rank = i + 1
            
        return reranked
