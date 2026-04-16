# Tasks

- [x] Inspect existing codebase and diagnose state <!-- id: 0 -->
- [x] Create Current Implementation Snapshot <!-- id: 1 -->
- [x] Plan `/analyze-claim` pipeline implementation <!-- id: 2 -->
- [x] Implement/Update `/analyze-claim` endpoint <!-- id: 3 -->
- [x] Verify end-to-end flow with sample claim <!-- id: 4 -->
- [x] Start Backend Server <!-- id: 5 -->
- [x] Start Frontend Application <!-- id: 6 -->
- [ ] Verify functionality in browser <!-- id: 7 -->

## Data & Corpus Expansion (Alpha)
- [x] Create `DOC_CORPUS_PLAN.md` <!-- id: 8 -->
- [x] Implement BigQuery Ingestion Script (`ingest_bq.py`) <!-- id: 9 -->
- [x] Implement Embedding Pipeline with EmbeddingGemma <!-- id: 10 -->
- [x] Run Ingestion (Target: 100 patents for Eval) <!-- id: 11 -->

## Evaluation Strategy (Alpha)
- [x] Create `EVALUATION_PLAN.md` <!-- id: 13 -->
- [x] Implement `eval/generate_test_set.py` (Self-retrieval) <!-- id: 14 -->
- [x] Implement `eval/run_eval.py` <!-- id: 15 -->
- [x] Execute Baseline Evaluation <!-- id: 16 -->

## Gap Closure - Architect (You)
- [x] Implement `JobStore` (SQLite) <!-- id: 26 -->
- [x] Refactor `VectorSearchService` (Abstraction) <!-- id: 27 -->
- [x] Update `main.py` with Async/Job Pattern <!-- id: 28 -->

## Gap Closure - Data & Infrastructure (Agent: Data Engineer)
- [x] Check Docker availability & Select Vector DB (Failed: Docker/Chroma incompatible with Python 3.14) <!-- id: 17 -->
- [x] Setup Vector DB (Qdrant) <!-- id: 18 -->
- [x] Refactor `ingest_bq.py` for Stream/Batch Ingestion <!-- id: 19 -->

## Gap Closure - Retrieval (Agent: Retrieval Engineer)
- [ ] Implement Sliding Window Chunker <!-- id: 20 -->
- [ ] Implement Query Expansion (HyDE/Synonyms) <!-- id: 21 -->

## Gap Closure - Reasoning (Agent: Prompt Designer)
- [ ] Implement Chain-of-Thought in `VertexLLM` <!-- id: 22 -->
- [ ] Define `OfficeActionDraft` Output Schema <!-- id: 23 -->

## Gap Closure - Evaluation (Agent: Eval Engineer)
- [ ] Create Hard Negative Test Set <!-- id: 24 -->
- [ ] Measure Reasoning Consistency <!-- id: 25 -->
