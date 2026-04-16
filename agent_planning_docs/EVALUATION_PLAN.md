# APEX Evaluation Plan: Retrieval & Reasoning

## 1. Objective
Establish a reproducible baseline for APEX's end-to-end performance.
**Goal**: Quantify how often APEX correctly retrieves and identifies relevant prior art for a given claim.

## 2. Evaluation Strategy: "Self-Retrieval" (Gold Standard)
Since we lack manually labeled novelty reports for thousands of patents, we will use **Self-Retrieval** as the proxy for v1 evaluation.
*   **Hypothesis**: A patent's own description is the *perfect* prior art for its claims (it fully anticipates them).
*   **Method**: 
    1.  Select $N$ patents from our local corpus.
    2.  Extract Claim 1 (Independent) from Patent $P$.
    3.  Run APEX on Claim 1.
    4.  **Success**: If Patent $P$ is retrieved in the Top-K results.

## 3. Evaluation Harness

### A. Test Set Generation (`eval/generate_test_set.py`)
*   **Input**: `apex_data/chunks.json` (The ingested corpus).
*   **Process**:
    *   Group chunks by `patent_id`.
    *   Extract the first chunk tagged as `claim`.
    *   Select random sample of 20-50 patents.
*   **Output**: `apex_data/eval_set.json`
    ```json
    [
      { "patent_id": "US-1234567-B2", "claim_text": "A widget comprising..." }
    ]
    ```

### B. Execution Engine (`eval/run_eval.py`)
*   **Loop**: Iterate through `eval_set.json`.
*   **Call**: `HybridSearchService.search(claim_elements)`
*   **Metrics Collection**:
    *   **Retrieval**: Rank of the Gold Patent ID.
    *   **Reasoning**: (Optional for v1) Check if `VertexLLM.analyze` flags it as "Assumed Known" or "Anticipated".

## 4. Success Metrics

### Retrieval Metrics
*   **Recall@K** (Primary): Percentage of queries where Gold Patent is in top $K$ (e.g., K=5, 10).
    *   *Target v1*: Recall@10 > 80%.
*   **MRR (Mean Reciprocal Rank)**: Average of $1/Rank$. Rewards higher placement.

### Reasoning Metrics (Qualitative/Heuristic)
*   **Detection Rate**: If Gold Patent is retrieved, does the LLM classify at least 80% of elements as "Anticipated"?
*   **False Positive Rate**: How often are *random* unrelated patents in the top lists marked as "Anticipated"? (Requires manual spot check).

## 5. Minimum Viable Corpus (MVC)
To make evaluation fast but meaningful:
*   **Size**: 100 patents.
*   **Domain**: High-overlap CPCs (e.g., 100 patents all in `G06N` - AI/Computers).
*   **Rationale**: High overlap makes retrieval harder (distractors are semantically similar), providing a realistic stress test.

## 6. Iteration Loops
1.  **Retrieval Failure** (Gold patent not in Top-10):
    *   *Action*: Inspect chunks. Are claims too abstract? Is chunking cutting keywords?
    *   *Fix*: Adjust `HybridSearch` weights (Vector vs Keyword) or Chunking strategy.
2.  **Reasoning Failure** (Gold patent retrieved but "Low Risk"):
    *   *Action*: Inspect Decomposition. Did verified citations fail?
    *   *Fix*: Refine `Strict Mode` prompt or element parsing.

## 7. Implementation Checklist
- [ ] Ensure Ingestion of MVC (100 patents, `G06` prefix).
- [ ] Implement `eval/generate_test_set.py`.
- [ ] Implement `eval/run_eval.py`.
- [ ] Run Baseline & Report Metrics.
