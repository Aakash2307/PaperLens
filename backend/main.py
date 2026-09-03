# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException

from db import ping_db
from paper_source import search_papers, RetrievalError

app = FastAPI(title="PaperLens API")


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
async def search(query: str, limit: int = 20):
    """
    Phase 1: returns raw candidate papers for a query, no ranking yet.
    Ranking (Phase 2) will reorder this list by semantic relevance.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")

    try:
        papers = await search_papers(query, limit=limit)
    except RetrievalError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"query": query, "count": len(papers), "results": papers}