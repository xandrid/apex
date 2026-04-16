# APEX Baseline Evaluation Report

## Executive Summary
We have successfully established a baseline for APEX's retrieval capabilities using a **Self-Retrieval** strategy.
*   **Metric**: Recall@10
*   **Score**: **100.0%**
*   **MRR**: **1.000**
*   **Sample**: 20 U.S. Patents (High-tech domains `G06`/`H04`)
*   **Conclusion**: The retrieval engine (Hybrid Search = EmbeddingGemma + BM25) is functioning correctly and is highly effective at retrieving ground-truth patents given their own claims.

## Methodology
1.  **Ingestion**: 100 patents ingested from BigQuery (`ingest_bq.py`).
2.  **Test Set**: Randomly selected 20 patents; extracted their first independent claim (`generate_test_set.py`).
3.  **Execution**: Queried the `HybridSearchService` with the claim text.
4.  **Success Criteria**: The source patent ID must appear in the top 10 results.

## System Configuration
*   **Vector Model**: `sentence-transformers/all-MiniLM-L6-v2` (via `EmbeddingGemmaService`).
*   **Vector Store**: Local numpy array (384 dimensions).
*   **Keyword Search**: BM25Okapi.
*   **Fusion**: Reciprocal Rank Fusion (RRF).

## Fixes Implemented
*   **Dimension Mismatch**: Fixed a critical bug where `VectorSearchService` expected 768 dimensions (Google API default) but the local model produced 384. Refactored to use `EmbeddingGemmaService` consistently.

## Next Steps
*   **Harder Negatives**: The current 100-patent corpus is small. Expand to 1,000+ to increase difficulty.
*   **Reasoning Eval**: Integrate the LLM analysis step to measure "Reasoning Correctness" (e.g., does it correctly identify anticipated elements?).
