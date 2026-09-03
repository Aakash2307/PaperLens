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
