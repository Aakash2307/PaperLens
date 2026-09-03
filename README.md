# PaperLens

A research assistant that ranks academic papers by semantic relevance to a query.

## Status: Phase 0 — setup

Two containers: `api` (FastAPI) and `db` (Postgres + pgvector).

## Run it

```bash
docker compose up --build
```

First build takes a few minutes (installs deps + downloads the embedding model).

Then check:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","database":"connected"}`

## Stop it

```bash
docker compose down          # stop, keep DB data
docker compose down -v       # stop and wipe DB data
```

## Structure

```
paperlens/
  docker-compose.yml   # wires api + db together
  backend/
    Dockerfile
    requirements.txt
    main.py            # FastAPI app, /health endpoint
    db.py              # SQLAlchemy engine + connection check
```
