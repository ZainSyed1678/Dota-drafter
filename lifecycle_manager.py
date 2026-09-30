import psycopg2
from psycopg2.extras import DictCursor
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dotauser:dotapassword@localhost:5432/dotadb")

def get_conn():
    return psycopg2.connect(DATABASE_URL, connect_timeout=15)

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
                    is_ready BOOLEAN NOT NULL DEFAULT FALSE,
                    UNIQUE (patch_version, dataset_version)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feature_metadata (
                    id SERIAL PRIMARY KEY,
                    dataset_id INT REFERENCES dataset_metadata(id),
                    feature_version VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (dataset_id, feature_version)
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
                ON CONFLICT (patch_version, dataset_version)
                DO UPDATE SET match_count = EXCLUDED.match_count, is_ready = EXCLUDED.is_ready
            """, (version, dataset_version, match_count, is_ready))
        conn.commit()


def register_feature(dataset_id: int, feature_version: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO feature_metadata (dataset_id, feature_version) VALUES (%s, %s) ON CONFLICT DO NOTHING", (dataset_id, feature_version))
        conn.commit()

def get_dataset_info(patch: str, version: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM dataset_metadata WHERE patch_version = %s AND dataset_version = %s", (patch, version))
            return cur.fetchone()


def get_patches_in_state(state: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT patch_version FROM patch_lifecycle WHERE state = %s", (state,))
            return [r[0] for r in cur.fetchall()]
