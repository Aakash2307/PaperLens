# Phase 0 — Setup

**Builds on:** nothing (starting point)
**Feeds into:** Phase 1 (retrieval runs inside this skeleton), Phase 5 (this is what gets deployed)

## Objective

Prove the two core pieces of infrastructure can run together before
building any PaperLens-specific logic: a FastAPI container and a
Postgres/pgvector container, talking over Docker's internal network.

**Definition of done:** `docker compose up` starts both containers, and
`curl http://localhost:8000/health` confirms the API can actually reach
Postgres — not just that both happen to be running independently.

**Status:** ✅ Done.

## What was built

- `docker-compose.yml` — two services, `db` (`pgvector/pgvector:pg16`)
  and `api` (built from `backend/Dockerfile`), `api` depends on `db`
  passing a healthcheck first
- `backend/Dockerfile` — installs Python deps, pre-downloads the
  embedding model at *build* time so the first real API call never
  stalls on a ~90MB download
- `backend/requirements.txt` — FastAPI, SQLAlchemy, psycopg, pgvector,
  sentence-transformers, httpx
- `backend/db.py` (first version) — `create_engine()` + `SessionLocal`
  reading `DATABASE_URL`, plus `ping_db()` (`SELECT 1`)
- `backend/main.py` (first version) — just the FastAPI app object and
  `/health`

## Key decisions

- **Postgres talked to over a Docker service name (`db`), not
  `localhost`.** Inside Docker's internal network, each service gets a
  real, resolvable hostname — this pattern gets reused unchanged all
  the way through Phase 5's production deploy.
- **Model baked into the image at build time, not downloaded on first
  request.** A recurring pattern in this project: pay one-time costs
  upfront (build time) rather than on the runtime path a user actually
  waits on.

## Blockers hit and fixed

- Docker wasn't installed → installed `docker.io`, enabled the daemon,
  added the user to the `docker` group
- `docker compose` subcommand missing (Ubuntu's `docker.io` doesn't
  ship it) → downloaded the Compose plugin manually, `chmod +x`'d it
- `sudo docker compose` failed even after that → plugin was only
  visible to the user, not root → copied it to
  `/usr/local/lib/docker/cli-plugins/`

## Concepts learned

- Docker Compose: multi-container orchestration, `depends_on` +
  healthchecks, internal service-name networking
- The gap between "Docker is installed" and "Docker Compose works" —
  not the same thing, not bundled together by default on Ubuntu
- Why hostnames inside Docker differ from `localhost`
