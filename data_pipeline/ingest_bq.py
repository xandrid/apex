import os
import sys
# Add backend to path immediately
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

import json
import re
import html
import time
import numpy as np
from typing import List, Dict, Any
from google.cloud import bigquery
from app.services.embedding_gemma import EmbeddingGemmaService
from app.services.embedding_gemma import EmbeddingGemmaService
from app.services.qdrant_vector_store import QdrantVectorStore
import numpy as np
import uuid
from dotenv import load_dotenv

# Load env from backend/.env
# We assume running from root
env_path = os.path.join(os.path.dirname(__file__), "../backend/.env")
load_dotenv(env_path)

# Configuration
PROJECT_ID = "majestic-cairn-480103-f1"
DATA_DIR = os.path.join(os.path.dirname(__file__), "../apex_data")
CHUNKS_FILE = os.path.join(DATA_DIR, "chunks.json")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "embeddings.npy")
TARGET_LIMIT = 100

def get_bq_client():
    return bigquery.Client(project=PROJECT_ID)

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespace (replace tabs, newlines, multi-spaces with single space)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_patents_bq(limit: int = 500) -> List[Dict[str, Any]]:
    client = get_bq_client()
    query = f"""
        SELECT
            publication_number,
            publication_date,
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
            AND kind_code = 'B2'
            -- Coalesce dates to ensure we filter correctly regardless of schema variance
            AND COALESCE(grant_date, publication_date) > 20230101
            AND (
                EXISTS(SELECT 1 FROM UNNEST(cpc) AS c WHERE c.code LIKE 'G06%') OR
                EXISTS(SELECT 1 FROM UNNEST(cpc) AS c WHERE c.code LIKE 'H04%')
            )
        LIMIT {limit}
    """
    print("Executing BigQuery...")
    query_job = client.query(query)
    results = []
    for row in query_job:
        pub_date_str = str(row.publication_date) if row.publication_date else None
        formatted_date = f"{pub_date_str[:4]}-{pub_date_str[4:6]}-{pub_date_str[6:]}" if pub_date_str and len(pub_date_str) == 8 else None
        
        results.append({
            "publication_number": row.publication_number,
            "publication_date": formatted_date,
            "title": row.title,
            "abstract": row.abstract,
            "claims": row.claims,
            "description": row.description,
            "cpc_codes": row.cpc_codes
        })
    print(f"Fetched {len(results)} patents.")
    return results

def smart_chunk(text: str) -> List[str]:
    """
    Smart chunking:
    1. Split by newlines (preserve paragraphs).
    2. Normalize whitespace within paragraphs.
    3. If paragraph > Threshold (e.g. 3200 chars ~ 800 tokens), apply sliding window.
       Window = 3200 chars, Overlap = 400 chars.
    4. Keep paragraphs > 50 chars.
    """
    if not text:
        return []
        
    paragraphs = text.split('\n')
    chunks = []
    
    # 1 Token ~ 4 Chars
    WINDOW_SIZE = 3200 
    OVERLAP = 400
    MIN_LENGTH = 50
    
    for p in paragraphs:
        # Clean: resolve HTML and fix whitespace *within* the paragraph
        # We assume one paragraph is one logical unit
        cleaned = clean_text(p)
        
        if len(cleaned) < MIN_LENGTH:
            continue
            
        if len(cleaned) <= WINDOW_SIZE:
            chunks.append(cleaned)
        else:
            # Sliding Window
            # Simple char-based sliding window for stability
            start = 0
            while start < len(cleaned):
                end = start + WINDOW_SIZE
                # If we are near the end, just take the rest
                if end >= len(cleaned):
                    chunks.append(cleaned[start:])
                    break
                
                # Try to break on space if possible
                slice_candidate = cleaned[start:end]
                
                # If we aren't at end, back off to last space to avoid cutting words
                if end < len(cleaned):
                    last_space = slice_candidate.rfind(' ')
                    if last_space > WINDOW_SIZE * 0.8: # Only back off if space is reasonably far
                         end = start + last_space + 1 # Include space
                
                chunks.append(cleaned[start:end])
                start += (end - start) - OVERLAP # Move forward by stride
                
    return chunks

def run_ingestion():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # 1. Fetch
    patents = fetch_patents_bq(limit=TARGET_LIMIT)
    
    # 2. Process & Chunk
    all_chunks = []
    
    print("Processing and chunking...")
    for pat in patents:
        pid = pat['publication_number']
        title = pat.get('title', '')
        pub_date = pat.get('publication_date')
        cpc = pat.get('cpc_codes', '')
        
        base_meta = {
            "patent_id": pid, 
            "title": title,
            "publication_date": pub_date,
            "cpc_codes": cpc
        }
        
        # Chunk specific fields
        # Abstract
        abs_text = clean_text(pat.get('abstract', ''))
        if len(abs_text) > 50:
            meta = base_meta.copy()
            meta["type"] = "abstract"
            meta["chunk_id"] = f"{pid}_abs"
            all_chunks.append({
                "id": str(uuid.uuid4()),
                "text": abs_text,
                "metadata": meta
            })
            
        # Claims
        claims_chunks = smart_chunk(pat.get('claims', ''))
        for i, c in enumerate(claims_chunks):
            meta = base_meta.copy()
            meta["type"] = "claim"
            meta["chunk_id"] = f"{pid}_clm_{i}"
            all_chunks.append({
                "id": str(uuid.uuid4()),
                "text": c,
                "metadata": meta
            })
            
        # Description
        desc_chunks = smart_chunk(pat.get('description', ''))
        for i, c in enumerate(desc_chunks):
            meta = base_meta.copy()
            meta["type"] = "description"
            # Qdrant requires strict UUID or Int. We use random UUID for ID.
            # We store the "logical ID" in metadata payload.
            meta["chunk_id"] = f"{pid}_dsc_{i}"
            
            all_chunks.append({
                "id": str(uuid.uuid4()),
                "text": c,
                "metadata": meta
            })
            
    print(f"Total chunks created: {len(all_chunks)}")
    
    # 3. Embed and Push to Qdrant
    print("Initializing Embedding Service...")
    embedder = EmbeddingGemmaService()
    
    print("Initializing Qdrant Store...")
    vector_store = QdrantVectorStore()
    
    texts = [c['text'] for c in all_chunks]
    
    print(f"Embedding {len(texts)} chunks and pushing to Qdrant (this may take a moment)...")
    batch_size = 32
    total_pushed = 0
    
    # Process in batches: Embed -> Push -> Repeat
    # This saves memory compared to embedding everything first
    
    current_batch_chunks = []
    current_batch_texts = []
    
    for i, chunk in enumerate(all_chunks):
        current_batch_chunks.append(chunk)
        current_batch_texts.append(chunk['text'])
        
        if len(current_batch_chunks) >= batch_size:
            embeddings_matrix = embedder.embed_documents(current_batch_texts)
            # vector_store expects list of lists
            embeddings_list = embeddings_matrix.tolist()
            
            vector_store.add_documents(current_batch_chunks, embeddings_list)
            
            total_pushed += len(current_batch_chunks)
            print(f"Processed & Pushed {total_pushed}/{len(all_chunks)}")
            
            # Reset
            current_batch_chunks = []
            current_batch_texts = []

    # Final batch
    if current_batch_chunks:
        embeddings_matrix = embedder.embed_documents(current_batch_texts)
        embeddings_list = embeddings_matrix.tolist()
        vector_store.add_documents(current_batch_chunks, embeddings_list)
        total_pushed += len(current_batch_chunks)
        
    print(f"Done! {total_pushed} documents pushed to Qdrant.")

if __name__ == "__main__":
    # Ensure backend path is in python path to find app.services
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
    run_ingestion()
