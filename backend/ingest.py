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

from sqlalchemy.dialects.postgresql import insert as pg_insert # pyright: ignore[reportMissingImports]

from db import SessionLocal, engine
from models import Paper, IngestionProgress
from paper_source import fetch_papers_page, RetrievalError
from ranking import embed_text_batch

# Ten broad fields, chosen for topical diversity rather than any
# particular research interest — the goal is a corpus that can
# meaningfully answer queries from many domains, not just AI/CS.
FIELDS = [
    
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
REQUEST_DELAY_SECONDS = 0.4  # ~2.5 req/sec sustained — conservative for a long bulk run


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


def _load_progress(field: str) -> tuple[str, int, bool]:
    """Returns (cursor, collected, completed) for a field — fresh start if never seen before."""
    with SessionLocal() as session:
        row = session.get(IngestionProgress, field)
        if row is None:
            return "*", 0, False
        return row.cursor or "*", row.collected, row.completed


def _save_progress(field: str, cursor: str | None, collected: int, completed: bool):
    with SessionLocal() as session:
        stmt = pg_insert(IngestionProgress).values(
            field=field, cursor=cursor, collected=collected, completed=completed
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["field"],
            set_={"cursor": cursor, "collected": collected, "completed": completed},
        )
        session.execute(stmt)
        session.commit()


async def ingest_field(field: str, target_count: int):
    cursor, collected, completed = _load_progress(field)

    if completed:
        print(f"  [{field}] already completed ({collected}/{target_count}) — skipping")
        return

    if collected > 0:
        print(f"  [{field}] resuming from {collected}/{target_count}")

    while collected < target_count:
        try:
            papers, next_cursor = await fetch_papers_page(field, cursor=cursor, per_page=PAGE_SIZE)
        except RetrievalError as e:
            print(f"  [{field}] error, stopping this field for now (progress saved): {e}")
            _save_progress(field, cursor, collected, completed=False)
            return

        if not papers:
            print(f"  [{field}] no more results (got {collected}/{target_count})")
            _save_progress(field, cursor, collected, completed=True)
            return

        upsert_papers(papers)
        collected += len(papers)
        print(f"  [{field}] {collected}/{target_count} ingested")

        if not next_cursor:
            _save_progress(field, cursor, collected, completed=True)
            return

        cursor = next_cursor
        _save_progress(field, cursor, collected, completed=(collected >= target_count))
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
