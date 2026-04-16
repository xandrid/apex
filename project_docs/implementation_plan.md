# APEX Overhaul Plan: Production Readiness

## Goal
Transform APEX from a "functional prototype" into a robust, sellable product that handles varied user inputs gracefully. Address the user's concern that "it simply does not work" by expanding data coverage and improving feedback for low-relevance searches.

## User Review Required
> [!IMPORTANT]
> **Data Expansion**: We will increase the BigQuery limit from 10 to **100 patents**. This is still well within the free tier but provides 10x more coverage.
> **Search Thresholds**: We will introduce a "Relevance Threshold". If no patent exceeds this score, the system will explicitly report "No Relevant Prior Art Found" instead of forcing a comparison with irrelevant documents.

## Proposed Changes

### 1. Data Pipeline Expansion
#### [MODIFY] [bigquery_client.py](file:///Users/matthew/.gemini/antigravity/scratch/apex-app/data_pipeline/bigquery_client.py)
- Increase default `limit` to **100**.
- Add error handling for quota limits.

#### [MODIFY] [ingest.py](file:///Users/matthew/.gemini/antigravity/scratch/apex-app/data_pipeline/ingest.py)
- Ensure the ingestion script handles the larger batch size efficiently.

### 2. Search Quality & Confidence
#### [MODIFY] [hybrid_search.py](file:///Users/matthew/.gemini/antigravity/scratch/apex-app/backend/app/services/hybrid_search.py)
- Return raw similarity scores.
- Implement a `similarity_threshold` (e.g., 0.3).

#### [MODIFY] [main.py](file:///Users/matthew/.gemini/antigravity/scratch/apex-app/backend/app/main.py)
- Check search scores before sending to LLM.
- If all scores are below threshold, return an "Insufficient Prior Art" response immediately (saving LLM costs and user confusion).

### 3. Frontend UX Improvements
#### [MODIFY] [AnalysisResult.tsx](file:///Users/matthew/.gemini/antigravity/scratch/apex-app/frontend/components/AnalysisResult.tsx)
- Add a "Search Confidence" indicator.
- If confidence is low, display a warning: *"⚠️ No highly relevant prior art found in the local database. Results may be generic."*
- Improve the "Unsupported" element visualization to clearly show *why* the risk is Low (i.e., "Missing Element: X").

## Verification Plan
### Automated Tests
- Run `ingest.py` to fetch 100 patents.
- Run `evaluate.py` to ensure accuracy remains 100% on the Golden Case.

### Manual Verification
- **Test Case A (Golden)**: Should still be High Risk.
- **Test Case B (Toaster)**: Should now say "No Relevant Art Found" (or Low Confidence) instead of just "Low Risk".
- **Test Case C (Complex)**: Should show improved relevance if any ML patents are picked up in the larger batch.
