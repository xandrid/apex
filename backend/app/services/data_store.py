import json
import os
import numpy as np
from typing import List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../../apex_data")
CHUNKS_FILE = os.path.join(DATA_DIR, "chunks.json")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "embeddings.npy")

class LocalDataStore:
    """
    Manages local persistence of patent data and embeddings.
    Replaces mock in-memory lists with file-based storage.
    """
    def __init__(self):
        self._ensure_data_dir()
        self.chunks: List[Dict[str, Any]] = self._load_chunks()
        self.embeddings: np.ndarray = self._load_embeddings()

    def _ensure_data_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _load_chunks(self) -> List[Dict[str, Any]]:
        if os.path.exists(CHUNKS_FILE):
            try:
                with open(CHUNKS_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading chunks: {e}")
                return []
        return []

    def _load_embeddings(self) -> np.ndarray:
        if os.path.exists(EMBEDDINGS_FILE):
            try:
                return np.load(EMBEDDINGS_FILE)
            except Exception as e:
                print(f"Error loading embeddings: {e}")
                return np.array([])
        return np.array([])

    def save_data(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Overwrites the current data with new data.
        """
        # Save chunks
        with open(CHUNKS_FILE, "w") as f:
            json.dump(chunks, f, indent=2)
        
        # Save embeddings
        # Convert to numpy array
        emb_array = np.array(embeddings, dtype="float32")
        np.save(EMBEDDINGS_FILE, emb_array)
        
        # Update in-memory
        self.chunks = chunks
        self.embeddings = emb_array
        print(f"Saved {len(chunks)} chunks and {emb_array.shape} embeddings to {DATA_DIR}")

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        return self.chunks

    def get_all_embeddings(self) -> np.ndarray:
        return self.embeddings
