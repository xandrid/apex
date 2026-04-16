# Migration to ChromaDB

## Goal
Replace the current in-memory `numpy` vector store with **ChromaDB** to enable scaling beyond 100 patents to stateful, persistent storage.

## User Review Required
*   **Vector DB Choice**: Using **ChromaDB** (pip installable) instead of Qdrant (Docker) because Docker is not available in the current environment.

## Proposed Changes

### Data Layer (`app/services/vector_store.py`) [NEW]
*   Create a clean abstraction `VectorStore` to encapsulate ChromaDB logic.
*   **Methods**:
    *   `add_documents(chunks: List[dict], embeddings: List[list])`
    *   `search(query_embedding: List[float], top_k: int)`

### Ingestion Pipeline (`data_pipeline/ingest_bq.py`) [MODIFY]
*   **Refactor**: Remove `numpy.save` logic.
*   **Streaming**: Initialize `VectorStore` and push chunks in batches (e.g., 100 chunks).

### Search Service (`app/services/hybrid_search.py` & `vector_search.py`) [MODIFY]
*   **Refactor**: Replace `LocalDataStore` calls with `VectorStore` queries.
*   **Logic**: `VectorSearchService.search()` will now delegate to ChromaDB's ANN index.

## Verification Plan

### Automated Verification
*   Create a script `verify_chroma.py`:
    1.  Initialize store.
    2.  Add 5 dummy documents.
    3.  Perform a vector search.
    4.  Assert results are returned.

### Manual Verification
*   Run the full `ingest_bq.py` with `TARGET_LIMIT=10` (small run).
*   Run `eval/run_eval.py` to ensure the Baseline Recall remains 100%.
