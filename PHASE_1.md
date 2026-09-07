# Phase 1 — Retrieval

**Builds on:** Phase 0 (runs inside that Docker/FastAPI skeleton)
**Feeds into:** Phase 2 (ranking operates on what this retrieves),
Phase 4 (evaluation compares against this endpoint), Phase 6 (ingestion
reuses this phase's OpenAlex client, extended for bulk pulls)

## Objective

Prove the retrieval half of PaperLens works: given a topic, can we
reliably get back real, usable candidate papers? Deliberately no
ranking yet — this phase is about recall (get plausible candidates),
not precision (order them well). That's Phase 2's job.

**Definition of done:** `curl "http://localhost:8000/search?query=..."`
returns real papers (title, abstract, authors, year) for an arbitrary
topic, reliably, without erroring.

**Status:** ✅ Done.

## What was built

- `backend/paper_source.py` — calls OpenAlex (`api.openalex.org/works`)
  for candidate papers; reconstructs abstracts from OpenAlex's
  word-position index format (abstracts aren't stored as plain text);
  returns clean dicts (`paper_id`, `title`, `abstract`, `authors`,
  `year`, `url`, `citation_count`)
- `backend/main.py` — `/search?query=...` endpoint wired to the above

## Key decisions

- **Retrieval source: OpenAlex, not Semantic Scholar (switched
  mid-phase).** Semantic Scholar's unauthenticated tier (100 req/5min,
  shared globally) throttled development almost immediately. Rather
  than fight it with retries, switched entirely to OpenAlex — no API
  key, ~10 req/sec, similar coverage (~250M works), CC0-licensed
  metadata aggregated from Crossref/PubMed/arXiv/publishers — not
  scraped from arbitrary pages.
- **Only metadata, never full text.** The `url` field links out to the
  actual paper; PaperLens never hosts or reproduces content. This
  becomes a real constraint later (Phase 6's roadmap notes several
  post-MVP features are blocked on this).

## Blockers hit and fixed

- Semantic Scholar 429s → switched retrieval source entirely (see above)
- Missing `docker-compose.yml` in the project root on first real run →
  `no configuration file provided`

## Concepts learned

- Two-stage IR pattern: retrieval (recall) separated from ranking
  (precision) — the architectural split this entire project is built
  around
- API rate-limit design: shared unauthenticated pools vs. switching
  providers entirely vs. retry/backoff
- What "extracted from the internet" actually means for a licensed
  metadata aggregator vs. a scraper — this distinction matters again
  explicitly in Phase 6, when the question of building a web crawler
  came up and was deliberately rejected for the same underlying reason
