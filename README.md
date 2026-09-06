# PaperLens

**A semantic search and ranking engine for academic paper discovery.**

Tell it what you're researching — it doesn't just search, it ranks what to read first.

🔗 **Live:** [paperlens-production-xxxx.up.railway.app](https://paperlens-production-33ed.up.railway.app/) 

---

## What it does

Give PaperLens a research topic — "transformer attention mechanisms," "CRISPR off-target effects," anything — and it:

1. Retrieves real candidate papers (title, abstract, authors, citations)
2. Ranks them by **actual semantic relevance** to your query, not just keyword overlap or a search API's default order
3. Returns a prioritized list you can act on immediately

Most search tools stop at "here are 50 results." PaperLens's entire premise is that *ranking is a separate, harder problem worth solving explicitly* — and it proves that with a real evaluation, not just a demo (see [Evaluation](#evaluation) below).

## Why this exists

Built as a from-scratch demonstration of applied information retrieval — the goal was to build something technically credible enough to explain and defend in depth, not just something that runs. Every architectural decision below has a documented reason, and every real bug hit along the way (rate limits, DNS timing, volume mounts, index tradeoffs) is written up rather than smoothed over — see [`/docs`](#documentation) for the full build log.

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              User query                  │
                    └──────────────────┬────────────────────────┘
                                        │
                    ┌───────────────────▼────────────────────┐
                    │         FastAPI (backend/main.py)        │
                    └───────────────────┬────────────────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                │                                                │
    ┌───────────▼────────────┐                    ┌─────────────▼─────────────┐
    │   /search (live)         │                    │   /search/corpus (owned)   │
    │   OpenAlex API call      │                    │   Postgres full-text (BM25)│
    │   → semantic re-rank     │                    │   + pgvector semantic      │
    │                          │                    │   → Reciprocal Rank Fusion │
    └──────────────────────────┘                    └────────────────────────────┘
                │                                                │
                └───────────────────────┬────────────────────────┘
                                        │
                        ┌───────────────▼────────────────┐
                        │   Postgres + pgvector           │
                        │   (embedding cache / owned corpus)│
                        └──────────────────────────────────┘
```

Two retrieval paths exist deliberately: `/search` (Phase 1-2, calls OpenAlex live, semantically re-ranks the result) and `/search/corpus` (Phase 6, searches a self-owned ~100k-paper corpus via hybrid keyword+semantic search). The first was kept unchanged specifically so the evaluation results below stay valid regardless of later additions.

## Tech stack

- **Backend:** FastAPI, Python 3.11
- **Database:** PostgreSQL + [pgvector](https://github.com/pgvector/pgvector)
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim, runs locally — no external inference API)
- **Retrieval:** [OpenAlex](https://openalex.org) (CC0-licensed academic metadata, ~250M works)
- **Frontend:** Single-file HTML/CSS/JS, no framework, no build step
- **Infra:** Docker Compose (local), Railway (production)

## Evaluation

PaperLens's ranking was evaluated against naive (unranked) order across 10 queries spanning distinct fields — with retrieval held constant so ranking was the only variable being tested.

**Result: 3 better · 6 same · 1 worse.**

A deliberately honest, mixed result rather than a cherry-picked perfect scorecard — including a documented case where keyword matching outperformed semantic ranking on term-specific precision. Full methodology and per-query breakdown: [`PHASE_4.md`](./PHASE_4.md).

## Getting started (local)

```bash
git clone https://github.com/<you>/PaperLens.git
cd PaperLens
docker compose up --build
```

Then:
```bash
curl http://localhost:8000/health
# {"status":"ok","database":"connected"}
```

Open `http://localhost:8000` in a browser for the search UI.

## Project structure

```
PaperLens/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py            # FastAPI app, routes
│   ├── db.py               # DB engine, schema/index setup
│   ├── models.py            # SQLAlchemy Paper model
│   ├── paper_source.py       # OpenAlex client (live + bulk pagination)
│   ├── ranking.py             # Embeddings + semantic ranking
│   ├── hybrid_search.py        # Keyword + semantic fusion (RRF)
│   ├── ingest.py                # Bulk corpus builder
│   ├── evaluate.py                # Ranked vs. naive evaluation harness
│   └── frontend/index.html         # Search UI
├── PHASE_0.md … PHASE_6.md    # Build log — objective, decisions, bugs hit, concepts learned, per phase
├── VISION.md                   # Long-term differentiation strategy
├── ROADMAP.md                   # Prioritized post-MVP feature list
└── DEPLOY.md                     # Deployment runbook (Railway)
```

## Documentation

The full build process — including every real bug hit and how it was diagnosed — is written up phase by phase:

| Phase | What |
|---|---|
| [PHASE_0](./PHASE_0.md) | Docker/Postgres setup |
| [PHASE_1](./PHASE_1.md) | Retrieval (OpenAlex) |
| [PHASE_2](./PHASE_2.md) | Embeddings + ranking |
| [PHASE_3](./PHASE_3.md) | Frontend |
| [PHASE_4](./PHASE_4.md) | Evaluation |
| [PHASE_5](./PHASE_5.md) | Deployment |
| [PHASE_6](./PHASE_6.md) | Self-owned search engine (hybrid retrieval) — in progress |

Post-MVP planning: [`VISION.md`](./VISION.md) (differentiation strategy vs. Elicit/Consensus/Scholar) and [`ROADMAP.md`](./ROADMAP.md) (30-item feature brainstorm, prioritized by effort/value).

## License

MIT
