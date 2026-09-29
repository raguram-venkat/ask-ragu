# Task 2 — Vector search

Status: todo
Est: 45m
Spec: SPEC.md §9 step 2

What: Cosine kNN over chunk embeddings for the embedded question.

Approach: Start with exact search (no ANN index); measure latency at the real chunk count; add HNSW only if exact exceeds the budget.

Read first:

- pgvector README: distance operators, exact vs approximate, HNSW

Watch out for:

- Operator must match the model's metric (cosine for bge).
- HNSW makes results approximate and costs build time — at a few thousand chunks it's probably unnecessary. Decide with numbers.
- Use the query-side embedding path from Sprint 2 Task 5.

Done when: Vector hit@k and latency recorded; HNSW decision written here.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
