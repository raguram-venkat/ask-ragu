# Task 3 — RRF fusion + relevance floor

Status: todo
Est: 60m
Spec: SPEC.md §9 step 2

What: Merge the two rankings with Reciprocal Rank Fusion into top-k seed chunks, and refuse early when nothing is relevant.

Approach: score = Σ 1/(60 + rank) across lists; relevance floor on the best vector similarity, tuned on eval v0 including the unanswerable questions.

Read first:

- Cormack, Clarke & Büttcher 2009 — Reciprocal Rank Fusion (2 pages)

Watch out for:

- RRF ignores raw scores on purpose — that's why it works across incomparable scales. Don't "fix" it by mixing scores in.
- Floor too high → refusals on answerable questions. Pick it from eval data, not intuition.

Done when: Hybrid hit@k ≥ both single methods, or the gap explained here.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
