import os
import sys
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.services.lexical_search import LexicalSearchService
from app.services.data_store import LocalDataStore

def populate():
    print("--- Populating SQLite FTS5 from Legacy Data ---")
    
    # 1. Load Chunks
    store = LocalDataStore()
    chunks = store.get_all_chunks()
    print(f"Loaded {len(chunks)} chunks.")
    
    # 2. Add to FTS5
    lexical = LexicalSearchService()
    lexical.reset() # Start fresh
    
    print("Indexing into SQLite FTS5...")
    # Add in batches
    BATCH_SIZE = 1000
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        lexical.add_documents(batch)
        print(f"Indexed {i+len(batch)}/{len(chunks)}...")
        
    print("Population Complete.")

if __name__ == "__main__":
    populate()
