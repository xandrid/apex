# Architect Implementation Plan

## 1. State Management (Job Store)
**Objective**: Move away from stateless/in-memory processing to a robust Job Queue pattern.
**Implementation**:
*   New Service: `app/services/job_store.py` wrapping SQLite.
*   Schema: `jobs` table (`id`, `status`, `created_at`, `result_json`).
*   Update `main.py`:
    *   `POST /analyze-claim` -> Creates Job, returns `job_id`.
    *   `GET /jobs/{job_id}` -> Returns status/result.

## 2. API Evolution (Search Abstraction)
**Objective**: Decouple `HybridSearchService` from `LocalDataStore` to allow the Data Engineer to plug in ChromaDB.
**Implementation**:
*   Define `VectorStoreInterface` (Protocol).
*   Refactor `VectorSearchService` to accept an injected instance of the store.
*   Default valid implementation: `LocalVectorStore` (wrapping the current numpy logic).
*   Future implementation (for Data Engineer): `ChromaVectorStore`.

## 3. Execution Order
1.  Implement `JobStore`.
2.  Refactor `main.py` to use Jobs (Async pattern).
3.  Refactor `VectorSearchService` to use Dependency Injection.
