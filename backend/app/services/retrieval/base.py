from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = {}
    vector_score: Optional[float] = None
    rank: Optional[int] = None

class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        pass
