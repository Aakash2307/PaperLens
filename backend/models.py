# pyrefly: ignore [missing-import]
from sqlalchemy import String, Integer, JSON, Boolean
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
# pyrefly: ignore [missing-import]
from pgvector.sqlalchemy import Vector

# MiniLM-L6-v2 outputs 384-dimensional vectors.
EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    pass


class Paper(Base):
    """
    Our own corpus of ingested papers — the search engine's index, not
    just an embedding cache anymore (that was Phase 2's role for this
    same table; Phase 6 repurposes it as the real thing being searched).

    `search_vector` (a generated tsvector column) and its GIN index are
    added via raw SQL in db.py's init_db() — SQLAlchemy's ORM doesn't
    have first-class support for Postgres generated columns, so that
    piece is deliberately handled outside the declarative model.
    """
    __tablename__ = "papers"

    paper_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    abstract: Mapped[str] = mapped_column(String)
    authors: Mapped[list] = mapped_column(JSON, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))


class IngestionProgress(Base):
    """
    Tracks per-field ingestion state so re-running ingest.py resumes
    instead of restarting from page 1 of every field. Without this,
    a completed field gets fully re-fetched AND re-embedded on every
    re-run before the DB insert quietly no-ops (ON CONFLICT DO NOTHING)
    — the embedding step is the expensive part, and it was being
    wasted entirely. This table is the fix: a completed field is
    skipped outright, and a partially-done field resumes from its
    actual saved cursor.
    """
    __tablename__ = "ingestion_progress"

    field: Mapped[str] = mapped_column(String, primary_key=True)
    cursor: Mapped[str | None] = mapped_column(String, nullable=True)
    collected: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
