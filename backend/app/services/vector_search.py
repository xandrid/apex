from typing import List, Dict, Any
from dotenv import load_dotenv
from app.models import ParagraphMatch
from app.services.embedding_gemma import EmbeddingGemmaService
from app.services.vector_store_protocol import VectorStore
# Default to Qdrant
from app.services.qdrant_vector_store import QdrantVectorStore

# Load environment variables
load_dotenv()

class VectorSearchService:
    def __init__(self, store: VectorStore = None):
        self.embedder = EmbeddingGemmaService()
        self.store = store if store else QdrantVectorStore()
        print(f"VectorSearchService initialized with store: {type(self.store).__name__}")

    def get_embedding(self, text: str) -> List[float]:
        try:
            return self.embedder.embed_query(text).tolist()
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []

    async def search(self, query_text: str, top_k: int = 5) -> List[ParagraphMatch]:
        try:
            query_emb = self.get_embedding(query_text)
            if not query_emb:
                return []
                
            raw_matches = self.store.search(query_emb, top_k)
            
            # Convert to internal model
            return [
                ParagraphMatch(
                    paragraph_id=m['id'],
                    patent_id=m['metadata'].get('patent_id', 'unknown'),
                    text=m['text'],
                    similarity_score=m['score'],
                    metadata=m['metadata']
                ) for m in raw_matches
            ]
        except Exception as e:
            print(f"Error during vector search: {e}")
            return []

# Singleton instance
_vector_service = None

def get_vector_service():
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorSearchService()
    return _vector_service

async def search_paragraphs(element_text: str, top_k: int = 5) -> List[ParagraphMatch]:
    service = get_vector_service()
    return await service.search(element_text, top_k)
