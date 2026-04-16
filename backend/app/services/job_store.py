import sqlite3
import json
import uuid
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

class JobStore:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result JSON
            )
        """)
        conn.commit()
        conn.close()

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (id, status, result) VALUES (?, ?, ?)",
            (job_id, "PENDING", None)
        )
        conn.commit()
        conn.close()
        return job_id

    def update_job(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if result:
            cursor.execute(
                "UPDATE jobs SET status = ?, result = ? WHERE id = ?",
                (status, json.dumps(result), job_id)
            )
        else:
            cursor.execute(
                "UPDATE jobs SET status = ? WHERE id = ?",
                (status, job_id)
            )
        conn.commit()
        conn.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, status, created_at, result FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "status": row[1],
                "created_at": row[2],
                "result": json.loads(row[3]) if row[3] else None
            }
        return None
