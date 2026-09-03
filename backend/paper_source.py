"""
Paper retrieval via OpenAlex (https://openalex.org).

Why OpenAlex over Semantic Scholar: no API key required, and the free
tier allows ~10 requests/sec (vs Semantic Scholar's unauthenticated
100 requests per 5 minutes, shared across every anonymous caller
globally). Similar scale of coverage. Good default for an MVP under
a deadline — swap back to Semantic Scholar later if you get a key
and want its citation-graph features.
"""
import httpx

SEARCH_URL = "https://api.openalex.org/works"

# OpenAlex asks you to identify yourself via a "mailto" param for
# their politeness pool (higher limits, but no auth required).
# Not a secret — safe to hardcode for a portfolio project.
POLITE_POOL_EMAIL = "paperlens-project@example.com"


class RetrievalError(Exception):
    """Raised when OpenAlex can't be reached or returns an error."""


async def search_papers(query: str, limit: int = 20) -> list[dict]:
    """
    Queries OpenAlex for candidate papers matching `query`.
    Returns a list of dicts with only the fields we need downstream.
    Papers with no reconstructable abstract are dropped — we can't
    embed/rank them without text.
    """
    params = {
        "search": query,
        "per-page": limit,
        "mailto": POLITE_POOL_EMAIL,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(SEARCH_URL, params=params)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RetrievalError(f"OpenAlex error: {e}") from e
        data = resp.json()

    return _parse_papers(data)


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """
    OpenAlex stores abstracts as {word: [positions]} to save space.
    We rebuild the plain-text abstract from that.
    """
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    if not positions:
        return None
    return " ".join(positions[i] for i in sorted(positions))


def _parse_papers(data: dict) -> list[dict]:
    papers = []
    for item in data.get("results", []):
        abstract = _reconstruct_abstract(item.get("abstract_inverted_index"))
        if not abstract:
            continue
        papers.append({
            "paper_id": item.get("id"),
            "title": item.get("title") or item.get("display_name", ""),
            "abstract": abstract,
            "authors": [
                a["author"]["display_name"]
                for a in item.get("authorships", [])
                if a.get("author")
            ],
            "year": item.get("publication_year"),
            "url": item.get("doi") or item.get("id"),
            "citation_count": item.get("cited_by_count", 0),
        })
    return papers
