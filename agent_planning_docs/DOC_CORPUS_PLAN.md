# APEX Corpus Strategy & Ingestion Plan

## Overview
This document outlines the strategy for building the initial local vector corpus for APEX using Google Patents Public Data.
**Target**: 500–1,000 US Patents (Full Text).
**Embedding Backend**: Local `EmbeddingGemma`.

## 1. Data Source Selection
We will use the **Google Cloud BigQuery Public Dataset**: `patents-public-data.patents.publications`.
*   **Why**: Contains full text (claims, abstract, description) and CPC classifications.
*   **Cost Control**: Strict filters on `country_code`, `grant_date`, and `LIMIT` clauses to minimize processed bytes.

## 2. Corpus Composition (v0 Target: ~500 Patents)
We will create a specialized dataset focused on high-tech domains relevant to common testing scenarios (e.g., consumer electronics, software, communications).

| Segment | CPC Prefixes | Quantity | Rationale |
| :--- | :--- | :--- | :--- |
| **Primary** | `G06` (Computing), `H04` (Comms), `G02` (Optics), `H01` (Elements) | ~450 | Core domain for AI/Software patent testing. |
| **Secondary** | `A61` (Medical), `B60` (Vehicles) | ~50 | Variety to test generalization. |

## 3. BigQuery Ingestion Strategy ("Zero Cost" Approach)
Directly querying the full `publications` table can be expensive (TB-scale). To mitigate this:
1.  **Partition Pruning**: Always filter by `country_code` (if partitioned) or `publication_date`.
2.  **Field Selection**: Select ONLY necessary text fields (`publication_number`, `title`, `abstract`, `claims.text`, `description.text`, `cpc`).
3.  **Limits**: Hard `LIMIT` on every query.

### SQL Skeleton
```sql
SELECT
  publication_number,
  title_localized[SAFE_OFFSET(0)].text AS title,
  abstract_localized[SAFE_OFFSET(0)].text AS abstract,
  (SELECT STRING_AGG(text, "\\n") FROM UNNEST(claims_localized)) AS claims,
  -- Fallback for description: try index 0, else aggregate all
  COALESCE(
      description_localized[SAFE_OFFSET(0)].text,
      (SELECT STRING_AGG(text, "\\n") FROM UNNEST(description_localized))
  ) AS description,
  (SELECT STRING_AGG(code, ",") FROM UNNEST(cpc)) AS cpc_codes
FROM
  `patents-public-data.patents.publications`
WHERE
  country_code = 'US'
  AND kind_code = 'B2' -- Granted Patents
  -- Coalesce dates to ensure we filter correctly regardless of schema variance
  AND COALESCE(grant_date, publication_date) > 20230101
  AND (
    EXISTS(SELECT 1 FROM UNNEST(cpc) AS c WHERE c.code LIKE 'G06%') OR
    EXISTS(SELECT 1 FROM UNNEST(cpc) AS c WHERE c.code LIKE 'H04%')
  )
LIMIT 500
```
*Note: We may need to adjust `grant_date` integer format or date type depending on exact schema version.*

## 4. Ingestion Pipeline
The pipeline will run as a standalone Python script `data_pipeline/ingest.py`.

### Step 1: Query & Fetch
*   Connect to BigQuery using `google-cloud-bigquery`.
*   Execute the SQL query.
*   Save raw results to `apex_data/raw_patents.jsonl`.

### Step 2: Processing & Chunking
*   **Input**: `apex_data/raw_patents.jsonl`.
*   **Cleaning**: 
    *   Normalize whitespace (collapse multiple spaces/tabs to single space).
    *   Strip excessive newlines.
    *   Decode HTML entities.
    *   *Filter*: Discard empty chunks or those < 50 chars.
*   **Logic**:
    1.  Parse JSONL.
    2.  Extract `abstract`, `claims`, `description`.
    3.  **Chunking**: Split text into paragraphs (~100-300 words).
        *   Keep context: `patent_id`, `type` (claim/desc), `chunk_id`.
    4.  **Output**: `apex_data/processed_chunks.json`.

### Step 3: Embedding (EmbeddingGemma)
*   **Input**: `apex_data/processed_chunks.json`.
*   **Model**: Use the local `EmbeddingGemma` service (via `app.services.embedding_gemma` or equivalent).
*   **Batching**: Process in batches (e.g., 32 chunks) to manage memory.
*   **Output**: `apex_data/embeddings.npy` (numpy array) and updated `apex_data/chunks.json` (with metadata).

### Step 4: Index Updates
*   The system currently uses `LocalDataStore` which reloads `chunks.json` and `embeddings.npy` on startup.
*   Simply saving these files to `apex_data/` triggers the update for the next restart.

## 5. Implementation Checklist (Data Engineer)
- [ ] pip install `google-cloud-bigquery` `pandas` `scikit-learn` (for simple chunking helpers if needed).
- [ ] Create `data_pipeline/ingest_bq.py`.
- [ ] Implement `fetch_patents_bq(limit=500)` function.
- [ ] Implement `chunk_patent_text(patent_blob)` function.
- [ ] Implement `embed_chunks(chunks_list)` using `EmbeddingGemma`.
- [ ] Run full pipeline and verify `apex_data/` output sizes.
