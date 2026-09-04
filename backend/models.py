from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pgvector.sqlalchemy import Vector

# MiniLM-L6-v2 outputs 384-dimensional vectors.
EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    pass


class Paper(Base):
    """
    Cache of papers we've already embedded, keyed by OpenAlex paper_id.
    Avoids re-computing the embedding every time the same paper shows
    up as a candidate for a different query.
    """
    __tablename__ = "papers"

    paper_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    abstract: Mapped[str] = mapped_column(String)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
