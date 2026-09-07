# Phase 4 — Evaluation

**Builds on:** Phase 1 (retrieval) + Phase 2 (ranking) — isolates
ranking as the one variable being tested
**Feeds into:** nothing downstream depends on this, but its findings
directly motivated Phase 6 (the "federated learning privacy" result —
keyword beating semantic — is the concrete evidence that hybrid search
was worth building)

## Objective

PaperLens is fundamentally a ranking system — this phase exists to
prove the ranking is actually doing something, not just "looks like it
works." A small, honest, hand-checked comparison is enough; no
research-grade framework needed.

**Definition of done:** ranked vs. naive (OpenAlex default order)
compared across a diverse query set, judged by hand, written up
honestly — including where ranking does *not* help.

**Status:** ✅ Done. Result stands independently of later phases — see
note below on why this doesn't get invalidated by Phase 6.

## What was built

- `backend/main.py` — `?naive=true` on `/search`, skips ranking so
  ranked and naive results come from identical retrieval, isolating
  ranking as the only variable
- `backend/evaluate.py` — runs 10 fixed queries spanning distinct
  fields (NLP, biology, policy, robotics, quantum computing, medicine,
  GNNs, urban planning, ML privacy, LLM safety), fetches top-5 for both
  modes, writes a side-by-side comparison with a blank verdict column
  for hand judging

## Results

**3 better · 6 same · 1 worse**, out of 10 queries.

- **Clearest win** (quantum computing error correction): naive's #1 was
  a materials-simulation paper matched purely on the word "quantum" —
  completely unrelated. Ranked's #1 was directly on-topic. Textbook
  case of semantic ranking beating keyword matching fooled by shared
  vocabulary.
- **Where naive won** (federated learning privacy): naive's #1 was
  precisely about differential privacy in FL; ranked's #1 was a
  broader general survey. Real limitation: semantic similarity can
  favor topical breadth over term-specific precision.
- **Unplanned finding:** two queries surfaced the exact same paper
  twice under different OpenAlex IDs (likely preprint + published
  versions) — a data-quality issue, not a ranking bug, later folded
  into `ROADMAP.md` as evidence-backed justification for a "duplicate
  detection" feature.

## Why this evaluation still holds after Phase 6

Phase 6 adds a *new* endpoint (`/search/corpus`) rather than modifying
`/search`. This was a deliberate choice specifically so this phase's
numbers wouldn't be silently invalidated by later architecture changes
— the 3/6/1 result is about Phase 2's ranking method against Phase 1's
retrieval, and remains true regardless of what Phase 6 builds
alongside it.

## Concepts learned

- Isolating a variable in an evaluation (same retrieval, only ranking
  toggled) so the comparison tests what it claims to test
- Why a mixed, honest result is more credible — and more useful for
  finding real failure modes — than a uniformly positive one
- Semantic similarity's actual failure mode (favors breadth over
  term-specific precision) as a concrete, evidenced fact rather than a
  theoretical caveat — this is the exact finding that later justified
  building hybrid search in Phase 6, rather than that being a
  hypothetical justification invented after the fact
