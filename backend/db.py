import os
import time
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
# pyrefly: ignore [missing-import]
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
            return
        except Exception as e:
            last_error = e
            delay = base_delay_seconds * (2 ** attempt)
            print(f"[init_db] attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)

    raise RuntimeError(f"init_db failed after {max_retries} attempts: {last_error}")