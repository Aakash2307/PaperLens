import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ping_db() -> bool:
    """Returns True if we can actually talk to Postgres."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


def init_db(max_retries: int = 5, base_delay_seconds: float = 2.0):
    """
    Enables the pgvector extension and creates any tables that don't
    exist yet. Safe to call every startup — all operations are
    idempotent (CREATE EXTENSION IF NOT EXISTS / create_all only
    creates missing tables).

    Retries with exponential backoff on connection failure. This
    matters in cloud deploys where the database service and its
    internal DNS name may not be immediately reachable the instant
    this service starts — a transient failure here shouldn't crash
    the whole app.
    """
    from models import Base  # imported here to avoid a circular import

    last_error = None
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            Base.metadata.create_all(engine)
            _init_search_indexes()
            return
        except Exception as e:
            last_error = e
            delay = base_delay_seconds * (2 ** attempt)
            print(f"[init_db] attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)

    raise RuntimeError(f"init_db failed after {max_retries} attempts: {last_error}")


def _init_search_indexes():
    """
    Phase 6 additions, all idempotent:

    1. `search_vector` — a generated tsvector column (title + abstract,
       weighted so title matches score higher). This is what makes
       full-text/BM25-style search possible; SQLAlchemy's ORM has no
       first-class concept of a Postgres generated column, so it's
       added here via raw DDL instead of in models.py.
    2. A GIN index on that column — the actual inverted index that
       makes keyword search fast over 100k+ rows instead of a full
       table scan.
    3. An ivfflat index on `embedding` — pgvector's approximate
       nearest-neighbor index. At 20 candidates (Phase 1-2 scale) an
       exact scan in Python was fine; at 100k rows, semantic search
       needs an actual index too, not just a table column.
    """
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE papers
            ADD COLUMN IF NOT EXISTS search_vector tsvector
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(abstract, '')), 'B')
            ) STORED
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS papers_search_vector_idx
            ON papers USING GIN (search_vector)
        """))
        # ivfflat needs at least a few rows to build meaningful clusters;
        # harmless to attempt on an empty table, just builds a trivial index.
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS papers_embedding_idx
            ON papers USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))
        conn.commit()
