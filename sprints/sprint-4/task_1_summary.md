# Task 1 — Lexical search

Status: done 2026-10-13 (owner-verified) — hit@k on eval v0 waits for the owner's eval rewrite (D-003)
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

- `src/ask_ragu/retrieval/lexical.py` — `lexical_search(conn, question) -> [(chunk_id, note_id, score)]`, best first
- `migrations/0005_chunks_tsv_gin.sql` — GIN index on `chunks.tsv`
- `tests/test_lexical.py` — OR semantics, exact ranking (heading vs body weights, ties by id), lexemes as indexed (`node.js`, a quote inside a URL lexeme), empty/stopword/punctuation/very long questions (no hits, no notice), input never acts as syntax (injection, operators, `-negation`), candidate cap
- `src/ask_ragu/settings.py`, `.env.example` — `RETRIEVAL_CANDIDATES=50` (per retriever, before fusion)
- `adr/0019-…`, `BACKLOG.md` (IDF)

Decisions made here:

- OR the question's own lexemes instead of `websearch_to_tsquery` (ADR-0019): AND semantics found 0 chunks for 5 of 5 natural questions on the real vault.
- The lexemes come from `to_tsvector('english', question)`, the same config the index uses. Each is quoted as a tsquery literal and cast without re-parsing, so query and index can't disagree. The escaping is tested with a real lexeme containing a quote (`x.com/a'b`).
- `ts_rank_cd` as is, no length normalisation: chunks are capped at 1,500 chars, so length differences are small. Ties are broken by chunk id (deterministic).
- No IDF yet: whether it's needed is a Task 5 ablation question on the rewritten eval (BACKLOG). Changing ranking from made-up questions would be tuning on guesses.
- GIN index added (it was a ponytail in 0002): p50 21 → 12 ms in the A/B test (rolled-back index), and p50 8 / p95 18 ms for `lexical_search` with 4 sample questions afterwards.
- Hit@k on eval v0 is not recorded: the 18 questions are drafts the owner rewrites first (D-003). It goes here once they're rewritten.

Gotchas:

- `ts_rank_cd` weights: one heading match (A, 1.0) outranks two body matches (B, 0.4 each).
- English stemmer: "competes" → compet but "competition" → competit, so they don't match. "O'Neil" → `o` + `neil`, "C++" → `c`: single letters match widely (BACKLOG).
- An empty query yields `q = NULL`, so `tsv @@ NULL` matches nothing with no notice: no special case needed (I'd added a guard, but a test showed it was dead code, so it's gone).
- A MOC's `## Links` chunk can rank first (e.g. a question naming a MOC section). This is known (BACKLOG, Task 4 assembly).
- OR is broad: a generic question matches up to ~30% of chunks, so precision depends on ranking and fusion.
