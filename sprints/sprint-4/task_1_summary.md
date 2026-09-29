# Task 1 — Lexical search

Status: todo
Est: 60m
Spec: SPEC.md §9 step 2

What: Full-text search over chunks with a weighted tsvector (title/heading A, body B) and `websearch_to_tsquery`.

Approach: GIN index on the tsvector; rank with ts_rank_cd; return top-k with ranks.

Read first:

- Postgres: Controlling Text Search (setweight, ts_rank_cd, websearch_to_tsquery)

Watch out for:

- `to_tsquery` throws on raw user input; `websearch_to_tsquery` doesn't.
- The 'english' config stems prose well but mangles acronyms and code identifiers — check eval questions that use them.
- An all-stopword question yields an empty query — handle it, don't error.

Done when: Lexical hit@k on eval v0 recorded here.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
