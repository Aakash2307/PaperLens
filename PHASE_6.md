# Phase 6 — Building an Actual Search Engine

**Builds on:** Phase 1 (`paper_source.py` extended, not replaced) +
Phase 2 (`Paper` model and `embed_text` reused and extended) — this is
explicitly a from-Phase-2 evolution, not a rewrite
**Feeds into:** nothing yet — this phase isn't finished

## Objective

Phases 1-5 gave PaperLens real ranking, but retrieval was entirely
outsourced to OpenAlex — every query was a live API call, and nothing
was owned. A search engine has two separate jobs: **retrieval**
(finding candidates, normally via an inverted index + keyword scoring)
and **ranking** (ordering them well). Phases 1-2 only ever built the
second one. This phase builds the first — genuinely, not by rebranding
what already existed.

**Definition of done:** a `/search/corpus` endpoint that searches a
locally-owned ~100k-paper corpus using hybrid (keyword + semantic)
ranking, with no live OpenAlex call at query time.

**Status:** 🟡 Partially verified — `/search/corpus` confirmed working against a
real (partial) corpus of 13,599 papers (computer science field fully
ingested at 10,000; medicine partially ingested before repeated OpenAlex
rate-limiting; 7 fields not yet started). Query `neural networks`
returned genuinely relevant, correctly-ranked results — the core
mechanism (own corpus, own inverted index, hybrid RRF ranking) is
proven to work end-to-end. Full ~90-100k target corpus not yet reached
due to OpenAlex rate limits during bulk ingestion (see blockers below).
Ingestion is resumable (progress tracked per field) — running it again
after a cooldown period will continue, not restart.

## What "using the API again" actually means here

OpenAlex is still used — but only at **ingestion time** (once, offline,
in `ingest.py`), never at **query time** anymore. Every prior phase
called OpenAlex live, per search. Once ingestion finishes, `/search/corpus`
never touches OpenAlex again — it queries our own Postgres table, using
our own inverted index. That shift (query-time API dependency → zero)
is the actual technical claim of this phase.

**Explicitly considered and rejected: building a real web crawler.**
Would mean building robots.txt handling, per-domain rate limiting, HTML
parsing across inconsistent publisher layouts, and paywall/bot-detection
handling — weeks of separate infrastructure, plus real legal exposure
(most academic publishers' ToS explicitly prohibit scraping). OpenAlex
already did this work, legally, once, and licenses the result as CC0.
Bulk-importing from it is standard practice, not a shortcut — it's the
same reasoning Phase 1 used when picking OpenAlex over building a
scraper in the first place.

## What was built

- `backend/models.py` — extended `Paper` with `authors`, `year`, `url`,
  `citation_count` (Phase 2's version only had enough fields for an
  embedding cache)
- `backend/db.py` — `_init_search_indexes()`: generated `tsvector`
  column + GIN index (the actual inverted index), plus an `ivfflat`
  index on `embedding` (approximate nearest-neighbor search, needed
  once the corpus isn't small enough to scan exactly in Python anymore
  — see Phase 2's note on this exact tradeoff)
- `backend/paper_source.py` — added `fetch_papers_page()` (cursor
  pagination for bulk pulls); Phase 1's `search_papers()` untouched,
  still used for live queries
- `backend/ranking.py` — added `embed_text_batch()` (batched inference,
  necessary at 100k-abstract scale; Phase 2's per-item `embed_text()`
  untouched)
- `backend/ingest.py` (new) — pulls ~10k papers each across 10 broad
  fields, batch-embeds, upserts idempotently
- `backend/hybrid_search.py` (new) — keyword search (`ts_rank`) +
  semantic search (pgvector cosine) fused via Reciprocal Rank Fusion
- `backend/main.py` — new `/search/corpus` endpoint; Phase 1's
  `/search` left completely unchanged

## Key concept: Reciprocal Rank Fusion (RRF)

Keyword score and semantic score measure fundamentally different
things — normalizing them onto one scale and adding them is a common,
subtly wrong approach. RRF combines each method's *rank position*
instead: `Σ 1/(k + rank)` across whichever ranked lists a paper appears
in. This is the standard industry technique for combining heterogeneous
ranking signals, not something improvised for this project.

This directly closes the gap **Phase 4's evaluation actually found** —
the "federated learning privacy" case where keyword matching beat
semantic ranking on term precision. Hybrid search isn't a hypothetical
improvement; it's a response to concrete evidence from an earlier phase.

## Design decisions worth defending

- **Corpus scope: broad multi-field (~100k), not narrow** — chosen so
  the engine can be demonstrated across genuinely different domains
- **Full-text search as a column on the same table**, not a separate
  index structure — simpler, standard Postgres pattern at this scale
- **RRF over hand-tuned score normalization** — more robust, standard
  practice
- **Old `/search` endpoint left untouched** — Phase 4's evaluation
  numbers stay valid and comparable regardless of what this phase adds

## Blockers hit and fixed (during actual ingestion)

- **`UndefinedColumn: authors`** — `Base.metadata.create_all()` only
  creates *missing* tables; it never alters an existing one's columns.
  The `papers` table already existed from Phase 2 with just 4 columns;
  Phase 6's model additions (`authors`, `year`, `url`, `citation_count`)
  never actually reached the real table. Fixed with an explicit
  `_migrate_papers_columns()` (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`)
  run before `create_all()`.
- **Bulk ingestion had no retry/backoff at all**, unlike the live
  `/search` endpoint — a real inconsistency between the two OpenAlex-
  calling code paths. Once a sustained bulk pull tripped OpenAlex's
  rate limit, every subsequent field failed instantly on its first
  request, because there was nothing to wait and retry. Fixed by
  adding the same retry-with-exponential-backoff pattern to
  `fetch_papers_page` (15s → 30s → 60s → 120s → 240s), matching the
  pattern already used in Phase 1 for the live endpoint and Phase 5
  for database connection retries — the same idea, applied a third time.
- **Re-running ingestion re-embedded already-ingested papers** before
  discovering the DB insert was a no-op — wasteful, since embedding is
  the expensive step. Fixed with a new `IngestionProgress` table:
  completed fields are now skipped entirely; partial fields resume
  from their actual saved cursor instead of restarting at page 1.
- **OpenAlex's rate-limit window stayed hot for several minutes** even
  after backing off — longer than a simple per-second throttle,
  suggesting a longer cooldown got triggered. Current approach:
  accept the partial corpus, resume ingestion later after a real
  cooldown period, rather than fighting the limit repeatedly in one
  sitting.

## Concepts learned (ingestion-specific)

- The real, load-bearing distinction between retrieval and ranking as
  separate search-engine responsibilities
- Postgres's built-in full-text search (`tsvector`, `ts_rank`, GIN) as
  a genuine inverted index, without needing separate infrastructure
  like Elasticsearch
- `ivfflat` as the vector equivalent of a GIN index — necessary once a
  vector column holds more than a trivial row count (a direct
  continuation of the exact-scan-vs-index tradeoff first noted in
  Phase 2)
- Reciprocal Rank Fusion as the standard way to combine heterogeneous
  ranking signals
- Cursor-based pagination vs. offset pagination for reliably pulling
  large result sets
- Batching as a general performance pattern for per-item ML inference
  at scale
- Why "using an API" isn't inherently at odds with "owning a search
  engine" — the distinction is ingestion-time vs. query-time dependency,
  not whether an external API was ever involved

## What's left before this phase can be marked done

1. Actually run `ingest.py` (long-running — plan for it)
2. Verify `/search/corpus` returns real, sensible results
3. Ideally: re-run Phase 4's evaluation methodology against
   `/search/corpus` vs. the original `/search`, to check whether hybrid-
   over-owned-corpus is a genuine improvement or an architecturally
   purer version of the same result quality
