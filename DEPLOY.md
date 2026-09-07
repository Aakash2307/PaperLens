# Deploying PaperLens (Railway)

Two services, deployed separately from the same repo: `db` (Postgres +
pgvector) and `api` (FastAPI, includes the frontend).

## Prerequisites

- Push this repo to GitHub (Railway deploys from a GitHub repo)
- A free Railway account: https://railway.app

## 1. Create the project

In Railway: **New Project → Deploy from GitHub repo** → select your PaperLens repo.
Railway will try to auto-detect a service — delete whatever it creates; we're
adding both services manually so we control exactly what runs.

## 2. Add the database service

**New → Empty Service.** Rename it `db`. Go to **Settings → Source** and set:
- **Deploy from Docker Image:** `pgvector/pgvector:pg16`

Go to **Variables** and add:
```
POSTGRES_USER=paperlens
POSTGRES_PASSWORD=<generate a real password, not "paperlens">
POSTGRES_DB=paperlens
```

Go to **Settings → Volumes** and add a volume mounted at `/var/lib/postgresql/data`
— without this, your database wipes every time Railway redeploys.

## 3. Add the API service

**New → GitHub Repo** → same repo again. Rename it `api`. Go to **Settings**:
- **Root Directory:** `backend` (so Railway builds from the Dockerfile there)
- **Networking → Generate Domain** — this gives you a public URL

Go to **Variables** and add:
```
DATABASE_URL=postgresql+psycopg://paperlens:<same password as above>@${{db.RAILWAY_PRIVATE_DOMAIN}}:5432/paperlens
```

`${{db.RAILWAY_PRIVATE_DOMAIN}}` is Railway's syntax for referencing another
service's internal hostname — it resolves automatically, you don't fill in
a literal value there.

## 4. Deploy

Both services should build and start automatically once variables are saved.
Watch the `api` service's build logs — first build takes a few minutes
(same torch/sentence-transformers download as local).

## 5. Verify

Open the domain Railway generated for `api`:
```
https://<your-generated-domain>.up.railway.app/health
```
Expect `{"status":"ok","database":"connected"}`. Then open the root URL in
a browser to use the actual search UI.

## Notes

- The `POLITE_POOL_EMAIL` in `paper_source.py` is hardcoded — fine for a
  portfolio project, but if you want OpenAlex's higher-limit "polite pool"
  tied to a real address, change it before deploying.
- Local dev (`docker compose up`) is unaffected by any of this — it's a
  separate, fully local setup.
