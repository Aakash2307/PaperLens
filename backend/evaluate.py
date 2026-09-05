"""
Phase 4 evaluation script.

Fetches both the ranked and naive (unranked) top-5 for a fixed set of
test queries spanning different research areas, and writes them
side-by-side into EVALUATION.md with a blank "Verdict" column.

This automates the tedious fetching/formatting so the only manual
work left is the actual judgment call: read both top-5s, decide if
ranking helped, hurt, or made no difference. That judgment is
intentionally NOT automated — a hand-checked, honest eval is the
whole point (see PaperLens brief, section 14).

Run from inside the running container:
    docker compose exec api python evaluate.py
"""
import httpx

API = "http://localhost:8000"

# Deliberately spans different fields so results aren't cherry-picked
# toward whatever the ranking model happens to be good at.
TEST_QUERIES = [
    "transformer attention mechanisms",
    "CRISPR gene editing off-target effects",
    "climate change mitigation policy",
    "reinforcement learning for robotics",
    "quantum computing error correction",
    "mRNA vaccine development",
    "graph neural networks",
    "sustainable urban development",
    "federated learning privacy",
    "large language model hallucination",
]


def fetch(query: str, naive: bool) -> list[dict]:
    resp = httpx.get(f"{API}/search", params={"query": query, "naive": naive, "limit": 20}, timeout=30.0)
    resp.raise_for_status()
    return resp.json()["results"][:5]


def format_list(papers: list[dict]) -> str:
    if not papers:
        return "_(no results)_"
    lines = []
    for i, p in enumerate(papers, 1):
        lines.append(f"{i}. {p['title']}")
    return "\n".join(lines)


def main():
    sections = []
    for query in TEST_QUERIES:
        print(f"Fetching: {query}")
        ranked = fetch(query, naive=False)
        naive = fetch(query, naive=True)

        section = f"""## Query: "{query}"

**PaperLens (ranked)** | **Naive (OpenAlex default order)**
---|---
{format_list(ranked)} | {format_list(naive)}

**Verdict (fill in by hand):** better / same / worse
**Why:**
"""
        sections.append(section)

    output = "# Phase 4 — Evaluation Results\n\n" \
             "Ranked (PaperLens) vs. naive (OpenAlex's default order) top-5, " \
             "for 10 queries spanning different fields.\n\n" \
             "For each query: read both abstracts (not just titles) if the " \
             "titles alone don't make it obvious, then judge whether the top " \
             "PaperLens result is more relevant to the query than the top " \
             "naive result.\n\n" + "\n---\n\n".join(sections)

    with open("EVALUATION.md", "w") as f:
        f.write(output)

    print("\nWrote EVALUATION.md — fill in the Verdict lines by hand.")


if __name__ == "__main__":
    main()
