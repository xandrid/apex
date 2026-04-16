import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

class LexicalSearchService:
    def __init__(self, db_path: str = "E:/apex/apex_lexical.db"):
        self.db_path = db_path
        self._ensure_table()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        # FTS5 virtual table
        # We index 'text' and 'title'. 'metadata' is stored but not indexed (unindexed column if supported, or just separate table).
        # FTS5 tables don't support JSON metadata columns well, so we might just store doc_id and retrieve metadata from Qdrant/Store
        # OR we can store a JSON string in a standard column (but FTS indexes it).
        # Let's keep it simple: id, text.
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
                id UNINDEXED, -- External ID (UUID)
                text,
                content='docs_content', -- External content table? Or just store here.
                content_rowid='rowid'
            )
        """)
        # Actually, simpler usage:
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(id UNINDEXED, text)")
        conn.commit()
        conn.close()

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        chunks: List of specific chunk format (text, metadata).
        We use the SAME ID generation logic as Qdrant to ensure matching.
        """
        import uuid
        conn = self._get_conn()
        cursor = conn.cursor()
        
        data = []
        for i, chunk in enumerate(chunks):
            # Same stable UUID logic
            unique_str = f"{chunk['metadata'].get('publication_number', 'unknown')}_{chunk['metadata'].get('id', i)}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_str))
            
            text = chunk.get('text', '')
            data.append((point_id, text))
            
        cursor.executemany("INSERT INTO search_index(id, text) VALUES (?, ?)", data)
        conn.commit()
        conn.close()
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # FTS5 Search with bm25 ranking (default)
        # Sanitize query: remove punctuation that confuses FTS5
        import re
        sanitized_query = re.sub(r'[^\w\s]', '', query).strip()
        if not sanitized_query:
            return []
        
        # Enclose in quotes or use NEAR if needed, but simple match is fine for now
        # escape double quotes just in case
        sanitized_query = sanitized_query.replace('"', '""')
        
        sql = f"""
            SELECT id, rank, text FROM search_index 
            WHERE search_index MATCH ? 
            ORDER BY rank 
            LIMIT ?
        """
        
        try:
            cursor.execute(sql, (sanitized_query, top_k))
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"FTS5 Search Error: {e}")
            return []
        
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "score": r[1],
                "text": r[2], # Return text
                "metadata": {} # Metadata missing in FTS currently
            })
            
        conn.close()
        
        # Normalize scores to 0-1 range for fusion? 
        # FTS5 rank is raw.
        # For simple fusion (RRF), we just need the Rank Order.
        return results

    def reset(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            self._ensure_table()
