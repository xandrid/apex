from dotenv import load_dotenv
load_dotenv()
from app.services.embedding_gemma import EmbeddingGemmaService
import numpy as np

def test_gemma():
    print("Initializing EmbeddingGemmaService...")
    try:
        service = EmbeddingGemmaService("google/embeddinggemma-300m")
        print("Model loaded.")
        
        text = "This is a patent claim about a widget."
        vec = service.embed_query(text)
        
        print(f"Embedding shape: {vec.shape}")
        print(f"Embedding sample: {vec[:5]}")
        
        if vec.shape[0] == 768:
            print("SUCCESS: Dimension is 768.")
        else:
            print(f"WARNING: Dimension is {vec.shape[0]}, expected 768.")
            
    except Exception as e:
        print(f"FAILED to load/run model: {e}")

if __name__ == "__main__":
    test_gemma()
