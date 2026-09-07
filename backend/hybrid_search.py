"""
Phase 6 — hybrid search over our own corpus.

Combines two independent retrieval methods against the `papers` table:

1. Full-text/keyword search (Postgres `ts_rank` against the generated
   `search_vector` column — a real BM25-family score, using the GIN
   index set up in db.py).
2. Semantic search (pgvector cosine similarity against `embedding`,
   using the ivfflat approximate-nearest-neighbor index).

The two scores aren't on the same scale (ts_rank and cosine similarity
measure fundamentally different things), so we don't try to normalize
and add them. Instead we use Reciprocal Rank Fusion (RRF): each
method produces its own ranked list, and a paper's final score is the
sum of 1/(k + rank) across whichever lists it appears in. A paper
that ranks well on *either* method scores well overall; one that
ranks well on *both* scores best of all.

This directly addresses a real finding from Phase 4's evaluation:
keyword search sometimes beats semantic search on term-specific
precision (the "federated learning privacy" case). Hybrid search
exists specifically so neither failure mode dominates.
"""
from sqlalchemy import text

from db import SessionLocal
from ranking import embed_text

RRF_K = 60  # standard constant from the original RRF paper; not sensitive to tuning
CANDIDATE_POOL_SIZE = 100  # how many each method retrieves before fusion


def _keyword_search(session, query: str, limit: int) -> list[str]:
    """Returns paper_ids ranked by ts_rank, best first."""
    rows = session.execute(text("""
        SELECT paper_id
        FROM papers
        WHERE search_vector @@ plainto_tsquery('english', :query)
        ORDER BY ts_rank(search_vector, plainto_tsquery('english', :query)) DESC
        LIMIT :limit
    """), {"query": query, "limit": limit}).fetchall()
    return [r[0] for r in rows]


def _semantic_search(session, query_vec: list[float], limit: int) -> list[str]:
    """Returns paper_ids ranked by cosine similarity (via pgvector's <=> operator), best first."""
    rows = session.execute(text("""
        SELECT paper_id
        FROM papers
        ORDER BY embedding <=> (:query_vec)::vector
        LIMIT :limit
    """), {"query_vec": str(query_vec), "limit": limit}).fetchall()
    return [r[0] for r in rows]


def _reciprocal_rank_fusion(*ranked_lists: list[str]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, paper_id in enumerate(ranked_list, start=1):
            scores[paper_id] = scores.get(paper_id, 0.0) + 1.0 / (RRF_K + rank)
    return scores


def hybrid_search(query: str, limit: int = 20) -> list[dict]:
    """
    Runs keyword and semantic search against our own corpus, fuses
    the results with RRF, and returns the top `limit` papers with
    full details plus their fused relevance_score.
    """
    query_vec = embed_text(query)

    with SessionLocal() as session:
        keyword_ids = _keyword_search(session, query, CANDIDATE_POOL_SIZE)
        semantic_ids = _semantic_search(session, query_vec, CANDIDATE_POOL_SIZE)

        fused_scores = _reciprocal_rank_fusion(keyword_ids, semantic_ids)
        if not fused_scores:
            return []

        top_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:limit]

        # Fetch full rows for just the papers we're actually returning.
        placeholders = ", ".join(f":id{i}" for i in range(len(top_ids)))
        params = {f"id{i}": pid for i, pid in enumerate(top_ids)}
        rows = session.execute(text(f"""
            SELECT paper_id, title, abstract, authors, year, url, citation_count
            FROM papers
            WHERE paper_id IN ({placeholders})
        """), params).mappings().fetchall()

    by_id = {r["paper_id"]: dict(r) for r in rows}
    results = []
    for pid in top_ids:
        if pid not in by_id:
            continue
        paper = by_id[pid]
        paper["relevance_score"] = round(fused_scores[pid], 4)
        results.append(paper)

    return results
