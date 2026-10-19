# Task 2 — Vector search

Status: in review — hit@k waits for the owner's eval rewrite (D-003)
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

- `src/ask_ragu/retrieval/vector.py` — `vector_search(conn, query_vector) -> [(chunk_id, note_id, cosine)]`, best first, `RETRIEVAL_CANDIDATES` at most
- `tests/test_vector.py` — cosine ranking with exact scores, ties by id, vector length doesn't matter, candidate cap (mutation-checked: L2 `<->` and inner product `<#>` both fail all 3)

Decisions made here:

- Cosine `<=>`, the metric bge is trained for. Its vectors are normalized, so inner product would rank alike, but cosine stays right with any model.
- Takes the query vector, not the question: `embed_query` runs once outside (off the event loop via `asyncio.to_thread`), and the eval harness reuses it.
- No HNSW: exact search is p50 20 / p95 27 ms over 1,965 chunks on the laptop (100 runs, 4 generic questions); `embed_query` adds p50 10–16 / p95 21–50 ms. That's well inside the 300 ms retrieval budget, and an index would make results approximate and use RAM on the 1 GB Micro. Re-check on the Micro (Task 6, after sprint-1/task_6): HNSW only if it misses the budget.
- Hit@k on eval v0 is not recorded: the questions are drafts the owner rewrites first (D-003).

Gotchas:

- `ORDER BY embedding <=> q` with the same expression in SELECT computes the distance twice per row: p50 37 ms. `ORDER BY score DESC` (the alias) computes it once: p50 20 ms, same ids. An HNSW index would need the operator form back.
- No migration and no new setting: `RETRIEVAL_CANDIDATES` (Task 1) caps both retrievers.
