import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from db import SessionLocal
from models import Paper

# Loaded once at import time (the model is baked into the Docker
# image at build time — see Dockerfile — so this is fast, not a
# network call).
_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> list[float]:
    return _model.encode(text, normalize_embeddings=True).tolist()


def embed_text_batch(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """
    Embeds many texts at once. Batching lets the model process
    several inputs per forward pass instead of one at a time — the
    difference between ingesting 100k papers in minutes vs. hours.
    Used by ingest.py; live per-query embedding (one query, one
    paper at a time in rank_papers) doesn't need this.
    """
    if not texts:
        return []
    embeddings = _model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
    return embeddings.tolist()


def _get_or_cache_embedding(session, paper: dict) -> list[float]:
    """
    Returns the cached embedding for this paper if we've seen it
    before; otherwise embeds it now and stores it for next time.
    """
    cached = session.get(Paper, paper["paper_id"])
    if cached is not None:
        return cached.embedding

    vector = embed_text(paper["abstract"])
    session.add(Paper(
        paper_id=paper["paper_id"],
        title=paper["title"],
        abstract=paper["abstract"],
        embedding=vector,
    ))
    session.commit()
    return vector


def rank_papers(query: str, papers: list[dict]) -> list[dict]:
    """
    Ranks candidate papers by cosine similarity between the query
    embedding and each paper's (cached-or-fresh) abstract embedding.
    Adds a `relevance_score` field (0-1, higher = more relevant) and
    returns papers sorted descending by that score.
    """
    if not papers:
        return []

    query_vec = np.array(embed_text(query))

    with SessionLocal() as session:
        paper_vecs = [
            np.array(_get_or_cache_embedding(session, p)) for p in papers
        ]

    # Embeddings are already normalized (normalize_embeddings=True),
    # so dot product == cosine similarity here.
    scores = [float(np.dot(query_vec, pv)) for pv in paper_vecs]

    ranked = [
        {**paper, "relevance_score": round(score, 4)}
        for paper, score in zip(papers, scores)
    ]
    ranked.sort(key=lambda p: p["relevance_score"], reverse=True)
    return ranked
