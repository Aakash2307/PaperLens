import os
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


def init_db():
    """
    Enables the pgvector extension and creates any tables that don't
    exist yet. Safe to call every startup — all operations are
    idempotent (CREATE EXTENSION IF NOT EXISTS / create_all only
    creates missing tables).
    """
    from models import Base  # imported here to avoid a circular import

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(engine)
