from typing import List, Optional, Dict, Any
from app.services.retrieval.base import Retriever, SearchResult
from app.services.retrieval.reranker import Reranker

class RerankedRetriever(Retriever):
    def __init__(self, base_retriever: Retriever, reranker: Reranker):
        self.base_retriever = base_retriever
        self.reranker = reranker

    async def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        # Fetch more candidates for reranking
        # Rule of thumb: fetch 10x or at least 50-100 candidates
        fetch_k = max(top_k * 10, 50) 
        
        initial_results = await self.base_retriever.retrieve(query, top_k=fetch_k, filters=filters)
        
        reranked_results = self.reranker.rerank(query, initial_results, top_k=top_k)
        
        return reranked_results
