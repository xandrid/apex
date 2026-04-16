# APEX System Status & Architecture

## 1. Intended Architecture Summary
APEX is an AI-powered patent examination simulator designed to analyze a single claim against a vector index of prior art.

*   **Flow**: Claim Input $\rightarrow$ Decomposition (LLM) $\rightarrow$ Element-level Search (Vector/Hybrid) $\rightarrow$ Prior Art Retrieval $\rightarrow$ Element-wise Analysis (LLM) $\rightarrow$ Risk Scoring $\rightarrow$ Final Report.
*   **Key Components**:
    *   **Claim Decomposition**: Breaks claim into structured limitations.
    *   **Vector/Hybrid Search**: Retrieves relevant paragraphs for each limitation.
    *   **Reasoning Engine**: Generates examiner-style "anticipated/obvious/unsupported" classifications.
    *   **Risk Logic**: Aggregates element findings into overall Novelty & Obviousness scores.

## 2. Current Implementation Snapshot

### Backend (`/backend`)
*   **Framework**: FastAPI.
*   **Status**: **Largely Implemented**.
*   **Endpoint**: `POST /analyze-claim` is fully defined in `main.py`.
    *   **Decomposition**: Calls `VertexLLMService.decompose_claim`.
    *   **Search**: Uses `HybridSearchService` (Vector + BM25 with RRF Fusion).
    *   **Analysis**: Calls `VertexLLMService.analyze_patent` which supports "Strict Mode" (citation verification).
    *   **Risk Scoring**: Implemented in `main.py` (checking support for all elements).
*   **Data Layer**:
    *   `LocalDataStore` loads `chunks.json` and `embeddings.npy`.
    *   `VectorSearchService` uses Google `text-embedding-004`.
    *   `VertexLLMService` uses `gemini-2.0-flash-lite`.

### Frontend (`/frontend`)
*   **Framework**: Next.js (React).
*   **Status**: Structure exists. (Detailed inspection pending, but `node_modules` and `package.json` are present).

### Gaps vs Intended Behavior
*   **Backend**: The implementation is **Complete and Verified**.
    *   *Verified*: `/analyze-claim` successfully decomposes claims, executes hybrid search, and generates strict-mode analysis.
    *   *Verified*: Risk scoring logic correctly identifies "Low Risk" when elements are unsupported.
*   **Data**: `LocalDataStore` correctly loads the provided `chunks.json` (202 chunks).
*   **Frontend**: Structure exists, but integration verification is next step (though code looks correct).

## 3. Plan
1.  **Verify Backend**: Run the server and test `/analyze-claim` with a sample claim.
2.  **Verify Search Quality**: Check if `HybridSearchService` returns meaningful results.
3.  **Frontend Integration**: Ensure frontend correctly calls the backend.
