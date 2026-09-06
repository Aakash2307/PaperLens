from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from db import ping_db, init_db
from paper_source import search_papers, RetrievalError
from ranking import rank_papers
from hybrid_search import hybrid_search

app = FastAPI(title="PaperLens API")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    """
    Confirms the API is up AND can reach Postgres.
    This is our Phase 0 definition of done.
    """
    try:
        ping_db()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {e}")
    return {"status": "ok", "database": "connected"}


@app.get("/search")
async def search(query: str, limit: int = 20, naive: bool = False):
    """
    Returns candidate papers for a query, ranked by semantic
    relevance (cosine similarity between query and abstract
    embeddings, not just OpenAlex's default ordering).

    Pass ?naive=true to skip ranking and see OpenAlex's raw order
    instead — used for Phase 4 evaluation (ranked vs. naive).
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")

    try:
        papers = await search_papers(query, limit=limit)
    except RetrievalError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if naive:
        return {"query": query, "count": len(papers), "results": papers}

    ranked = rank_papers(query, papers)
    return {"query": query, "count": len(ranked), "results": ranked}


@app.get("/search/corpus")
def search_corpus(query: str, limit: int = 20):
    """
    Phase 6: searches our own ingested corpus (see ingest.py) instead
    of calling OpenAlex live. Combines keyword search (Postgres
    full-text, ts_rank) and semantic search (pgvector cosine
    similarity) via Reciprocal Rank Fusion.

    This is the "actual search engine" endpoint — /search above still
    exists and is unchanged, since Phase 4's evaluation was measured
    against it and shouldn't silently change meaning.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")

    results = hybrid_search(query, limit=limit)
    return {"query": query, "count": len(results), "results": results}


# Mounted last and at "/" so /health and /search (declared above) still
# take priority for those exact paths — this only catches everything else.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
