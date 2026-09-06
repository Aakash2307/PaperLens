"""
Phase 6 — bulk ingestion.

Pulls a broad, multi-field sample from OpenAlex into our own `papers`
table, so search runs against a corpus we own instead of a live API
call per query. This is what turns PaperLens from "a client of
OpenAlex's search engine" into "a search engine with its own index."

Run from inside the container (or locally against the deployed DB):
    docker compose exec api python ingest.py

Idempotent: re-running skips papers already in the table (upsert on
paper_id), so it's safe to re-run if it's interrupted partway.
"""
import asyncio
import time

from sqlalchemy.dialects.postgresql import insert as pg_insert

from db import SessionLocal, engine
from models import Paper
from paper_source import fetch_papers_page, RetrievalError
from ranking import embed_text_batch

# Ten broad fields, chosen for topical diversity rather than any
# particular research interest — the goal is a corpus that can
# meaningfully answer queries from many domains, not just AI/CS.
FIELDS = [
    "computer science",
    "medicine",
    "physics",
    "biology",
    "economics",
    "psychology",
    "environmental science",
    "mathematics",
    "engineering",
    "sociology",
]

PAPERS_PER_FIELD = 10_000
PAGE_SIZE = 200
EMBED_BATCH_SIZE = 64
REQUEST_DELAY_SECONDS = 0.15  # stay comfortably under OpenAlex's ~10 req/sec


def upsert_papers(papers: list[dict]):
    """
    Batch upsert — insert new papers, skip ones already in the table
    (same paper can legitimately appear across different field
    searches; we don't want duplicate rows or to re-embed it).
    """
    if not papers:
        return

    abstracts = [p["abstract"] for p in papers]
    embeddings = embed_text_batch(abstracts)

    rows = [
        {
            "paper_id": p["paper_id"],
            "title": p["title"],
            "abstract": p["abstract"],
            "authors": p["authors"],
            "year": p["year"],
            "url": p["url"],
            "citation_count": p["citation_count"],
            "embedding": emb,
        }
        for p, emb in zip(papers, embeddings)
    ]

    with SessionLocal() as session:
        stmt = pg_insert(Paper).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["paper_id"])
        session.execute(stmt)
        session.commit()


async def ingest_field(field: str, target_count: int):
    collected = 0
    cursor = "*"

    while collected < target_count:
        try:
            papers, next_cursor = await fetch_papers_page(field, cursor=cursor, per_page=PAGE_SIZE)
        except RetrievalError as e:
            print(f"  [{field}] error, stopping this field early: {e}")
            break

        if not papers:
            print(f"  [{field}] no more results (got {collected}/{target_count})")
            break

        upsert_papers(papers)
        collected += len(papers)
        print(f"  [{field}] {collected}/{target_count} ingested")

        if not next_cursor:
            break
        cursor = next_cursor
        time.sleep(REQUEST_DELAY_SECONDS)


async def main():
    print(f"Ingesting ~{PAPERS_PER_FIELD} papers each across {len(FIELDS)} fields "
          f"(~{PAPERS_PER_FIELD * len(FIELDS):,} total target)...\n")

    for field in FIELDS:
        print(f"Field: {field}")
        await ingest_field(field, PAPERS_PER_FIELD)
        print()

    with SessionLocal() as session:
        total = session.query(Paper).count()
    print(f"Done. Corpus now contains {total:,} papers.")


if __name__ == "__main__":
    asyncio.run(main())
