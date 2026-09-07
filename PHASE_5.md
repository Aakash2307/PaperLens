# Phase 5 — Deploy + Polish

**Builds on:** Phase 0 (same Docker setup, now targeting production)
+ everything through Phase 4 (this is what actually goes live)
**Feeds into:** nothing further in the original MVP scope — this
closed out the MVP. Phase 6 later builds *on top of* this live
deployment rather than replacing it.

## Objective

Get PaperLens genuinely live on the internet — a public URL you can
hand to anyone, no "works on my machine" caveat.

**Definition of done:** a public URL where `/health` confirms the API
and database are talking, and the root path loads the actual search UI.

**Status:** ✅ Done. Live on Railway.

## What was built / changed

- `backend/Dockerfile` — CMD reads `$PORT` from the environment instead
  of hardcoding it; dropped `--reload` (dev-only, real overhead in
  production)
- `docker-compose.yml` — added a `command:` override so local dev keeps
  `--reload`, while the Dockerfile's own CMD (used in production) stays
  reload-free — one file, two behaviors depending on where it runs
- `backend/db.py` — `init_db()` retries with exponential backoff
  instead of crashing instantly on connection failure
- `.gitignore`, `DEPLOY.md` — repo hygiene and a reproducible deployment
  runbook

## Platform: Railway

Two services: `pgvector` (Postgres + pgvector, via Docker image — not
Railway's managed Postgres, which lacks the extension) and
`PaperLens`/`api` (built from `backend/Dockerfile` via GitHub).

## Real problems hit and fixed

- **Railway's auto-builder ignored the Dockerfile** — had to explicitly
  set Root Directory (`backend`) and Builder (`Dockerfile`); auto-detection
  existing isn't the same as it being used
- **Postgres `initdb` failing every boot** — Railway volumes always
  contain a `lost+found` folder at their root; Postgres refuses to
  initialize into a non-empty directory. Fixed by keeping the volume at
  the standard mount path but pointing Postgres's actual data directory
  at a subfolder via `PGDATA`
- **`Name or service not known` connecting to the internal DB
  hostname** — Railway's private DNS for a newly-configured hostname
  didn't resolve instantly; root-caused as a timing issue, not a config
  error. Fixed by confirming resolution on redeploy, and more durably,
  by the retry-with-backoff added to `init_db()`

## Concepts learned

- Cloud auto-detection (Railpack) as a convenience, not a guarantee it
  picks the build method you actually specified
- `$PORT` as a runtime contract between platform and app
- Volume mount points vs. a database's actual data directory can, and
  sometimes must, differ
- Private networking/internal DNS between services, and that DNS
  propagation isn't always instantaneous
- Retry-with-backoff as a general pattern for any dependency that might
  not be ready the instant a service starts — same pattern already used
  for OpenAlex rate limits back in Phase 1, now applied to the database
  connection too

## MVP status at the close of this phase

All 5 phases done — retrieval, ranking, frontend, evaluation,
deployment. Live, working, defensible end-to-end, ahead of the Sept 20
deadline. Everything from Phase 6 onward is explicitly post-MVP work
built on top of this, not a correction of it.
