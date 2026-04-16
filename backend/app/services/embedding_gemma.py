import os
print(f"DEBUG: HF_TOKEN in env: {os.getenv('HF_TOKEN')}")
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingGemmaService:
    """
    Local embedding service using SentenceTransformers.
    Refers to 'EmbeddingGemma' as the architectural component name.
    """
    def __init__(self, model_name: str = "google/embeddinggemma-300m"):
        print(f"Loading local embedding model: {model_name}...")
        try:
             # trust_remote_code=True is often needed for newer/custom models like Gemma
             # token=True will use HF_TOKEN from env or hf-cli login
             import os
             from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError
             
             self.model = SentenceTransformer(
                 model_name, 
                 trust_remote_code=True,
                 token=os.getenv("HF_TOKEN") or True 
             )
             print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            print("Falling back to all-MiniLM-L6-v2 for robustness...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Embeds a list of texts and returns a numpy array.
        """
        if not texts:
            return np.array([])
        
        # SentenceTransformers returns numpy array by default
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings

    def embed_query(self, text: str) -> np.ndarray:
        """
        Embeds a single query string.
        """
        return self.model.encode([text])[0]
