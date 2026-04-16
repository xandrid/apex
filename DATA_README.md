# APEX Data & Vector Index

This directory handles the ingestion of patents, chunking, embedding, and vector search indexing.

## Implementation Details

- **Ingestion**: Fetches patents from BigQuery (or uses local files), saves them as parsed JSON in `apex_data/patents_parsed/`.
- **Chunking**: Splits parsed patents into claims and description paragraphs using `SmartChunker`.
- **Embedding**: Uses **EmbeddingGemma** (locally) to generate embeddings.
- **Indexing**: key-value store in `apex_data/chunks.json` and `apex_data/embeddings.npy` managed by `LocalDataStore`.

## Setup: Hugging Face Token

To use EmbeddingGemma locally (it is a gated model):

1. Go to [Hugging Face Tokens](https://huggingface.co/settings/tokens) and generate a **Read** token.
2. Go to [EmbeddingGemma 300M](https://huggingface.co/google/embeddinggemma-300m) and accept the license.
3. Add the token to your `backend/.env` file:
   ```bash
   HF_TOKEN=hf_...
   ```

## Commands

### 1. Ingest Patents
Run the ingestion script to fetch new patents and rebuild the index:

```bash
# Fetch 50 patents from BigQuery and rebuild index
python data_pipeline/ingest.py --limit 50

# Rebuild index from existing local parsed patents (skipping BigQuery)
python data_pipeline/ingest.py --no-fetch
```

### 2. Search
You can test the search API using the backend service:

```python
import asyncio
from app.services.vector_search import search_paragraphs

async def test():
    matches = await search_paragraphs("neural networks", top_k=3)
    for m in matches:
        print(f"[{m.similarity_score:.4f}] {m.patent_id}: {m.text[:100]}...")

if __name__ == "__main__":
    asyncio.run(test())
```
