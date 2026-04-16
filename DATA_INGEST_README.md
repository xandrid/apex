# APEX Data Ingestion Guide

This guide describes how to use `data_pipeline/ingest.py` to create corpora from BigQuery.

## Prerequisites

1. **Google Cloud Auth**: You must be authenticated to use BigQuery.
   ```bash
   gcloud auth application-default login
   ```
   Or set `GOOGLE_APPLICATION_CREDENTIALS` to your service account key.

2. **Hugging Face Token**: Required for EmbeddingGemma.
   Set `HF_TOKEN` in `backend/.env`.

---

## Usage

The `ingest.py` script now supports building custom corpora.

### Basic Usage

Fetch 50 random US patents (default):
```bash
python data_pipeline/ingest.py --limit 50
```

### Advanced Usage

Fetch 100 US patents related to "G06" (Computing) or "H04" (Electric Comm):
```bash
python data_pipeline/ingest.py \
  --source bigquery \
  --country US \
  --cpc_prefixes G06,H04 \
  --limit 100 \
  --output apex_data/patents_parsed/corpus_tech.jsonl
```

### Local Re-indexing

If you have already downloaded a corpus (jsonl file) and want to re-chunk/re-embed it without hitting BigQuery:

```bash
python data_pipeline/ingest.py \
  --source local \
  --output apex_data/patents_parsed/corpus_tech.jsonl
```

## Output

The script generates:
1. **Raw Corpus**: `apex_data/patents_parsed/<name>.jsonl` (if specified)
2. **Chunk Index**: `apex_data/chunks.json`
3. **Embeddings**: `apex_data/embeddings.npy`

The backend (`vector_search.py`) automatically loads the latest `chunks.json` and `embeddings.npy`.
