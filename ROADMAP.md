# PaperLens — Feature Roadmap (post-MVP)

Not implemented. For evaluation after MVP ships — see VISION.md for the
differentiation strategy this should be filtered through before building
anything here.

## Full feature list (as given), mapped to pipeline stage, effort, and value

| Stage | Feature | Effort | Value | Note |
|---|---|---|---|---|
| Discover | Filters/sorting (year, citations, exclude preprints) | Low | High | Just query params + WHERE clause |
| Discover | Related/similar papers | Low | High | Free — reuses embeddings already cached |
| Discover | Multi-source retrieval (arXiv, PubMed, Crossref, S2) | Med | High | Real engineering: dedup, merge conflicting metadata |
| Discover | Duplicate detection & metadata merging | Med | Med | Needed *if* multi-source is built; validated as real by Phase 4 eval (found actual duplicate records) |
| Discover | Author/lab discovery | Med | Med | OpenAlex already has this data |
| Discover | "What's new" feed / personalization | High | Med | Needs accounts + background jobs |
| Understand | AI-generated paper summaries | Med | High | LLM call over the abstract already retrieved |
| Understand | "Explain this paper" mode | Med | High | Deeper version of summaries |
| Understand | Chat with a research paper | High | High | **Blocked** — needs full paper text, not just abstracts |
| Understand | Section-by-section explanations | High | Med | **Blocked** — same full-text limitation |
| Understand | PDF reader with search/highlighting | High | Low* | **Blocked**; also low AI-demo value — mostly UI engineering |
| Compare | Paper comparison | Med | High | Embeddings + LLM synthesis, reuses existing pipeline |
| Compare | Citation graph / citation intelligence | Med-High | High | OpenAlex has `referenced_works` — real graph-theory + viz |
| Explore field | Research topic/field mapping | Med | High | Clustering + dimensionality reduction on embeddings — strong ML demo |
| Explore field | Research trend analysis | High | Med | Needs a real corpus over time, data-heavy |
| Gaps/directions | Research gap discovery | High | Low-Med | Genuinely hard to do non-superficially; risk of feeling gimmicky if shallow |
| Gaps/directions | Research question generator | Med | Low-Med | Easy to build shallow, hard to make genuinely good |
| Gaps/directions | Research idea / thesis idea generation | Med | Low-Med | Same risk as above |
| Lit review | Literature review assistant | High | Med | Multi-doc synthesis — ambitious, real capstone-level feature |
| Lit review | Citation generator (APA/MLA/IEEE/BibTeX) | Low | High | Pure formatting from metadata already retrieved |
| Lit review | Export literature/references | Low | Med | Pairs naturally with citation generator |
| Workspace | Personal paper library | High | Med | Needs accounts |
| Workspace | Collections/folders/tags/bookmarks | High | Med | Needs accounts |
| Workspace | Notes and annotations on papers | High | Med | Needs accounts |
| Workspace | Research project workspace | High | Med | Needs accounts |
| Workspace | Reading progress tracking | High | Med | Needs accounts |
| Workspace | Research dashboard w/ stats & insights | High | Med | Needs accounts, mostly aggregation UI |
| Discovery | "What's new" feed for saved topics | High | Med | Needs accounts + background jobs |
| Discovery | Personalized recommendations | High | Med | Needs accounts + usage history |
| Discovery | Researcher/lab discovery | Med | Med | Duplicate of the "Discover" row above — same feature, listed twice in original brainstorm |

*(Original brainstorm had "Research lab/university discovery" and "Author/researcher discovery"
as separate items — folded together above since OpenAlex's data model treats them as one feature.)*

## Recommendation (given at time of writing)

**First 3 after MVP ships**, in priority order: **related papers → citation
generator → filters.** All three reuse data/embeddings already in the
system — no new infrastructure, no new external dependency, each
independently demoable.

**Best "wow" feature with a real week to spend:** citation graph or
topic mapping — both are legitimate IR/ML demonstrations (graph
algorithms, clustering/dimensionality reduction) beyond "I called an
embedding model once."

**Correctly last, if ever:** the entire workspace cluster and
personalization — real product value, but accounts-and-infrastructure
work with almost no AI/IR content, which isn't what this portfolio
piece is for.

**Cross-reference:** before committing engineering time to any single
item here, run it through VISION.md's test — "what unique value does
PaperLens provide here that Elicit/Consensus/Scholar don't already?"
Several items above (AI summaries, basic filters) score well on
effort/value but poorly on differentiation — they may still be worth
building as infrastructure for a differentiated feature, but shouldn't
be pitched as the differentiator themselves.
