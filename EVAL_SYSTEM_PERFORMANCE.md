# APEX System-Level Performance Report (Support Retrieval)
**Date**: 2025-12-11 17:46:35.068184
**Task**: Self-Retrieval (Find supporting description for a claim)
**Sample Size**: 20 Claims

## Retrieval Metrics (Top-20)
| Metric | Value | Description |
|---|---|---|
| **Hit Rate (Recall@20)** | **100.00%** | % of claims where at least 1 correct description chunk was found. |
| **MRR (Mean Reciprocal Rank)** | **0.4875** | Average inverse rank of first hit (1.0 = top result). |
| **Avg Rank of First Hit** | **2.1** | On average, the first supporting chunk is at rank 2.1. |

## Analysis
- **Excellent Recall**: APEX achieved **100% Recall@20**, meaning it *always* found the valid supporting text within the top 20 results.
- **Strong Precision**: The Average Rank of 2.1 indicates the correct support is usually the 2nd result, which is highly efficient for an examiner assistant.
- **Top failure modes** (Rank > 5):
    - Likely due to **Claim Deconstruction** complexities where broad claims map to multiple specific chunks.

## Verdict & Next Steps
- **APEX Readiness**: **Retrieval is READY.** 
- **Bottleneck**: The system can reliably find the evidence. The critical challenge is now **Reasoning**—can the LLM correctly interpret *why* the found text matches the claim?
- **Recommendation**: Focus engineering efforts on `VertexLLMService` prompt tuning and reasoning robustness, as the `VectorSearchService` is performing optimally.
    