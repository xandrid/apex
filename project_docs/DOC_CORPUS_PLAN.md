# Evaluation Corpus Plan: "Citation Recap"

## Objective
Establish a quantitative benchmark for APEX's retrieval capabilities using historical data as Ground Truth.

## Strategy: Citation-Based Retrieval
We will strictly evaluate **Prior Art Retrieval**.
- **Theory**: If Patent A cites Patent B, then Patent B is relevant prior art for Patent A.
- **Task**: Given the Claims of Patent A, retrieval must find Patent B.

## Dataset Composition
We will construct a controlled dataset `apex_eval_v1`.

### 1. The Query Set (Probes)
- **Source**: 50 recently granted US Patents (2023-2024).
- **Filter**: 
  - CPC: `G06` (Computing), `H04` (Comms).
  - Must have > 5 citations.
- **Input**: The text of **Claim 1** of these patents.

### 2. The Corpus (Haystack)
- **Total Size**: ~2,000 Patents.
- **Composition**:
  - **Ground Truths (Positive Samples)**: All patents cited by the Query Set. (~500 patents).
  - **Distractors (Negative Samples)**: ~1,500 random patents from the same CPC codes/Timeframe, *not* cited by the Query Set.

## Data Structures

### `golden_dataset.json` (The Test)
```json
[
  {
    "query_id": "US-11111111-B2",
    "query_text": "1. A computer implemented method...",
    "relevant_docs": ["US-9999999-B2", "US-8888888-B2"] 
  }
]
```

### `corpus.jsonl` (The Index)
The standard ingestion format for `ingest.py`.
```json
{"publication_number": "US-9999999-B2", "title": "...", "description": "...", ...}
{"publication_number": "US-8888888-B2", "title": "...", "description": "...", ...}
...
```

## Implementation Steps

1. **Modify `bigquery_client.py`**:
   - Add capability to fetch `citation` field.
   - logic to "expand" a list of patent IDs (to fetch the cited patents).

2. **Create `build_eval_dataset.py`**:
   - Step 1: Fetch 50 "Head" patents.
   - Step 2: Extract their citation list.
   - Step 3: Fetch the full text of those cited patents (The Ground Truths).
   - Step 4: Fetch random distractors to fill quota to 2000.
   - Step 5: Save `apex_data/eval/corpus.jsonl` and `apex_data/eval/golden.json`.

3. **Ingest**:
   - Run `ingest.py` on `corpus.jsonl`.

4. **Evaluate**:
   - Run a benchmark script against `golden.json` measuring Recall@10.

## Success Metrics
- **Deterministic**: The dataset generation script is seeded or saves the precise list of IDs.
- **Versioned**: Output files saved to `apex_data/eval/v1/`.
