from fastapi import FastAPI, HTTPException

from db import ping_db

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
