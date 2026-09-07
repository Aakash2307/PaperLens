# Phase 2 — Embeddings + Ranking

**Builds on:** Phase 1 (ranks what retrieval returns)
**Feeds into:** Phase 3 (frontend displays these scores), Phase 4
(evaluation measures this ranking against naive order), Phase 6
(`embed_text`/`Paper` model reused and extended into a full corpus)

## Objective

Turn the flat candidate list from Phase 1 into something ranked by
genuine relevance, not just OpenAlex's default order. This is the core
"AI" claim of the MVP: does the system actually understand the query,
or is it just keyword matching in disguise?

**Definition of done:** `/search` results include a `relevance_score`
and are sorted by it, and the top result should be more topically
on-point than lower-ranked ones — even without exact keyword overlap.

**Status:** ✅ Done. Confirmed on `query=transformer attention mechanism`:
top result was directly on-topic (0.6566) ahead of a more tangential
paper (0.5484), despite no shared exact keywords in the titles.

## What was built

- `backend/models.py` — `Paper` table: `paper_id`, `title`, `abstract`,
  `embedding` (384-dim, pgvector `Vector` type)
- `backend/ranking.py` — loads `all-MiniLM-L6-v2` once at import;
  `embed_text()`; `_get_or_cache_embedding()` (cache-aside pattern);
  `rank_papers()` (cosine similarity via dot product on pre-normalized
  vectors)
- `backend/db.py` — added `init_db()` (enables pgvector extension,
  creates tables, idempotent)
- `backend/main.py` — calls `init_db()` on startup; `/search` now
  ranks before returning

## Key decisions

- **Ranking happens in Python, in memory, per request — not in SQL.**
  With ~20 candidates per query, an exact scan is fast enough that
  doing it in SQL would be premature optimization. pgvector's actual
  job at this stage is *caching* (avoid re-embedding a paper seen
  before), not similarity search itself.
  **This assumption changes explicitly in Phase 6** — once the corpus
  is ~100k rows instead of ~20 candidates, exact-scan-in-Python stops
  being viable and an actual vector index (`ivfflat`) becomes
  necessary. Phase 2's choice was correct *for its own scale*, not
  wrong in hindsight.
- **Query embeddings are never cached** (every query differs by
  definition) — only paper embeddings are.

## Concepts learned

- Embeddings: text → vectors where distance ≈ semantic difference
- Cosine similarity via dot product, and why pre-normalizing makes
  that valid
- Cache-aside pattern: check cache → compute on miss → store → return
- The precision/recall tradeoff implicit in choosing an in-memory scan
  over an index — a decision that's about scale, not correctness, and
  is revisited directly once scale changes in Phase 6
