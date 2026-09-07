# PaperLens — Vision (post-MVP)

**Not implemented. Do not build against this until MVP + roadmap prioritization is done.**

## Core positioning

> Google helps you find information. Google Scholar helps you find papers.
> PaperLens should help you understand a research field and decide where to look next.

Product direction: move from "search for papers" toward "help me navigate research" —
from a single search box to a guided pipeline:

```
Research Question
→ Discover papers
→ Understand papers
→ Organize into themes
→ Compare studies
→ Identify agreement / disagreement
→ Identify gaps
→ Explore emerging areas
→ Generate research directions
```

## Differentiation check (honest, done Sept 2026)

Tested against: Google Scholar, Semantic Scholar, Elicit, Consensus.

**Already commoditized — Elicit/Consensus do these well today:**
- Research-question-first search (Elicit)
- Per-paper extraction: methodology, findings, limitations (Elicit)
- Evidence synthesis / agreement-disagreement framing (Consensus)

Leading with these as "differentiators" is a losing pitch — it's catch-up, not novelty.

**Genuinely less crowded — where a real claim can be made:**
- Chaining gap-discovery → direction-generation → defensible next-step suggestions.
  Most tools stop at synthesis; almost none reliably get you to "here's an
  underexplored angle you could actually pursue."
- Journey/sequencing as the product, not any single feature — guiding someone
  who doesn't know a field yet through foundational → established → emerging →
  open questions, rather than a flat search result.
- Literal navigable research maps / trend structure, vs. synthesis-as-text.

**Working thesis:** PaperLens's real pitch is at the *gap-finding and
direction-generating* end of the pipeline, not the *paper-summary* end.
Lead with "what should I research next and why isn't this already being done,"
not "we also have AI summaries."

## Feature list (raw, for later triage — see ROADMAP.md for MVP-adjacent items)

1. Research-question-first search (intent, not just keywords)
2. "Why this paper matters" — contribution/methodology/findings/limitations
3. Research maps — foundational → established → emerging subtopics
4. Evidence landscape — support / conflict, tied back to source papers
5. Find disagreements — compare datasets/methods/metrics behind conflicting findings
6. Potential research gaps — grounded in cited evidence, never presented as fact
7. Research journey/workspace — question → papers → themes → notes → gaps → ideas
8. Beginner research mode — guided entry into an unfamiliar field
9. Research-oriented paper cards (structured extraction per paper)
10. Research directions — literature-grounded, not free-floating suggestions
11. Research trends — topic evolution, emerging keywords, momentum
12. Researcher/lab discovery

## Standing rule before building any of this

Before implementing any V2 feature from this list, ask:
**"What unique value does PaperLens provide here that Elicit/Consensus/Scholar don't already?"**
If the honest answer is "we also have AI summaries/search" — it's not enough on its own.
It may still be worth building as *infrastructure* for the differentiated features above
(e.g. structured paper cards are a prerequisite for gap-discovery), but it's not a
pitch on its own.
