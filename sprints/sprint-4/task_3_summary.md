# Task 3 — RRF fusion + relevance floor

Status: done 2026-10-19 (owner-verified) — hybrid hit@k waits for the owner's eval rewrite (D-003)
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

- `src/ask_ragu/retrieval/fuse.py` — `reciprocal_rank_fusion(lexical, vector) -> [(chunk_id, note_id, rrf_score)]`, best first, at most 8 seeds
- `tests/test_fuse.py` — overlap beats single-list, rank-not-score (mutation-checked: swapping in raw scores both pass), TOP_K cap, floor refusal (below and above), floor skipped when vector is empty
- `src/ask_ragu/settings.py`, `.env.example` — `RETRIEVAL_RELEVANCE_FLOOR=0.3`

Decisions made here:

- RRF with k=60 (Cormack et al. 2009 standard): rank-only, so ts_rank_cd and cosine can't disagree on scale. A chunk in both lists gets 1/60 + 1/(60+rank); a chunk in one gets just 1/(60+rank).
- TOP_K=8 as a module constant (SPEC §9 step 2 says k≈8), not a setting — it's a design constant from the spec, not a tunable. RRF_K=60 is also a constant from the paper.
- Relevance floor on the best vector cosine (`RETRIEVAL_RELEVANCE_FLOOR=0.3`): if the closest semantic match can't clear 0.3, the vault doesn't cover the question — refuse early with []. Lexical surface matches alone aren't enough; they produce noise on shared words without semantic relevance.
- No HNSW or RRF index changes needed: RRF is pure Python on already-fetched candidate lists, no SQL.
- Hybrid hit@k not recorded: the 18 questions are drafts the owner rewrites first (D-003).

Gotchas:

- `ORDER BY` in RRF is done in Python, not SQL — the two lists are already ranked by their respective retrievers; fusing needs a single sort across both. Same as Task 1's GIN note: keep the SQL retrievers simple, do the cross-retriever logic in the app.
- The floor default (0.3) is a placeholder, not measured: bge-small cosine for unrelated chunks hovers near 0, but answerable-question thresholds depend on the real vault and the rewritten eval. Set it too high and you refuse answerable questions; too low and unanswerable ones slip through. The eval harness (Task 5) will sweep it.
- Both lists must come from the same `RETRIEVAL_CANDIDATES` pool (50): a chunk ranked #50 in lexical but #1 in vector is still a strong match, not a weak one — RRF handles this naturally by position, not score. 
