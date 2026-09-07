# Phase 3 — Frontend

**Builds on:** Phase 2 (displays its ranked output)
**Feeds into:** Phase 5 (this is what gets served publicly once deployed)

## Objective

Make PaperLens usable by someone who isn't running curl commands.
Search box in, ranked list out — nothing more.

**Definition of done:** open a URL in a browser, type a topic, see a
ranked list of real papers with enough context (title, authors, year,
citations, relevance, abstract snippet) to decide what to read first.

**Status:** ✅ Done.

## What was built

- `backend/frontend/index.html` — single self-contained file, no
  framework, no build step; plain `fetch()` to `/search`
- `backend/main.py` — `app.mount("/", StaticFiles(...))`, added
  **after** the `/health` and `/search` route declarations so those
  keep taking priority for their exact paths

## Key decisions

- **Served by FastAPI itself, not a separate frontend server.** No
  CORS config needed, one container to run, one URL to open — right
  scope for a solo project with a hard deadline.
- **Visual direction: journal/index-card aesthetic, not a SaaS
  dashboard.** Serif titles, hairline rules, one accent color;
  relevance shown as plain text ("87% match"), not a colored badge —
  deliberately avoided rounded cards/shadows/badges as defaults.

## Blockers hit and fixed

- `frontend/` folder was created **outside** `backend/` — Docker only
  mounts `./backend:/app`, so anything outside that path is invisible
  to the container, regardless of where it sits on the host. Fixed by
  moving the folder in.

## Concepts learned

- Static file serving from a backend framework vs. a dedicated
  frontend server — simplicity now vs. independent-scaling flexibility
  later
- FastAPI/Starlette route resolution order: explicit routes beat
  mounted catch-alls, but only if declared first
- Docker volume mounts only expose what's explicitly mounted — nothing
  outside that path exists inside the container
- Restraint in UI design as a real decision, not an afterthought — what
  to leave out (badges, shadows, cards) shapes the tool's feel as much
  as what's included
