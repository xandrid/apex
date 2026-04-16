from typing import List, Dict, Any, Optional
from app.services.retrieval.base import Retriever, SearchResult
from app.services.vector_search import get_vector_service

class DenseRetriever(Retriever):
    def __init__(self):
        self.vector_service = get_vector_service()

    async def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        # Simple dense retrieval
        matches = await self.vector_service.search(query, top_k=top_k)
        
        return [
            SearchResult(
                id=m.paragraph_id,
                text=m.text,
                score=m.similarity_score,
                metadata=m.metadata,
                vector_score=m.similarity_score,
                rank=i+1
            )
            for i, m in enumerate(matches)
        ]
