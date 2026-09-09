import psycopg2
from psycopg2.extras import DictCursor
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dotauser:dotapassword@localhost:5432/dotadb")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_lifecycle_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS patches (
                    patch_version VARCHAR(50) PRIMARY KEY,
                    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    released_at TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS patch_lifecycle (
                    id SERIAL PRIMARY KEY,
                    patch_version VARCHAR(50) REFERENCES patches(patch_version),
                    state VARCHAR(50) NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dataset_metadata (
                    id SERIAL PRIMARY KEY,
                    patch_version VARCHAR(50) REFERENCES patches(patch_version),
                    dataset_version VARCHAR(50) NOT NULL,
                    match_count INT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_ready BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
        conn.commit()

def detect_patch(version: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO patches (patch_version) VALUES (%s) ON CONFLICT DO NOTHING", (version,))
            cur.execute("SELECT COUNT(*) FROM patch_lifecycle WHERE patch_version = %s", (version,))
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO patch_lifecycle (patch_version, state) VALUES (%s, %s)", 
                            (version, 'PATCH_DETECTED'))
        conn.commit()

def transition_state(version: str, new_state: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE patch_lifecycle SET state = %s, updated_at = CURRENT_TIMESTAMP WHERE patch_version = %s", 
                        (new_state, version))
        conn.commit()

def get_current_state(version: str) -> str:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT state FROM patch_lifecycle WHERE patch_version = %s ORDER BY updated_at DESC LIMIT 1", (version,))
            res = cur.fetchone()
            return res[0] if res else None

def register_dataset(version: str, dataset_version: str, match_count: int, is_ready: bool = False):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dataset_metadata (patch_version, dataset_version, match_count, is_ready)
                VALUES (%s, %s, %s, %s)
            """, (version, dataset_version, match_count, is_ready))
        conn.commit()
