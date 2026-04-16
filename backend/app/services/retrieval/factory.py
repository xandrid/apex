from typing import Optional
from app.services.retrieval.base import Retriever
from app.services.hybrid_search import HybridRetriever
from app.services.retrieval.reranker import Reranker
from app.services.retrieval.pipeline import RerankedRetriever

from app.services.retrieval.dense import DenseRetriever

_hybrid_retriever: Optional[HybridRetriever] = None
_dense_retriever: Optional[DenseRetriever] = None
_reranker: Optional[Reranker] = None

def get_retriever(mode: str = "hybrid") -> Retriever:
    global _hybrid_retriever, _dense_retriever, _reranker
    
    # Lazy Init
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()

    if mode == "hybrid":
        return _hybrid_retriever
    
    elif mode == "qdrant_dense":
        if _dense_retriever is None:
            _dense_retriever = DenseRetriever()
        return _dense_retriever
    
    elif mode == "hybrid_rerank":
        if _reranker is None:
            _reranker = Reranker()
        return RerankedRetriever(_hybrid_retriever, _reranker)
    
    elif mode == "colbert":
        # Fallback 
        print("WARNING: ColBERT mode requested but not available. Falling back to Hybrid.")
        return _hybrid_retriever
        
    elif mode == "colbert_rerank":
         print("WARNING: ColBERT mode requested but not available. Falling back to Hybrid + Rerank.")
         if _reranker is None:
            _reranker = Reranker()
         return RerankedRetriever(_hybrid_retriever, _reranker)
         
    else:
        # Default fallback
        print(f"WARNING: Unknown retrieval mode '{mode}'. Defaulting to Hybrid.")
        return _hybrid_retriever
