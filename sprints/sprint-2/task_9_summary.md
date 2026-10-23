# Task 9 — Eval set v0

Status: done — 18 drafts pass the checker; owner rewrites them before Sprint 4 (D-003)
Est: 60m
Spec: SPEC.md §12 · D-003

What: 15-20 questions you'd really ask your vault, each with the note(s) that should answer it.

Approach: Mix single-note facts, cross-note questions needing a link hop, MOC-level overviews, and 2 questions the vault can't answer (tests refusal); YAML.

Read first:

- SPEC §12

Watch out for:

- Personal content: `eval/questions.private.yaml` is gitignored; commit a synthetic `questions.sample.yaml` for the public repo.
- Never store it inside the vault — it would get indexed and leak answers into retrieval.
- Write before tuning retrieval (D-003), or you'll unconsciously pick questions it already gets right.

Done when: ≥ 15 questions with gold note paths; at least 4 need a graph hop.

---

Filled in while working

Files touched:

- `eval/questions.private.yaml` — the real set (gitignored via `eval/*.private.*`; never committed, never in the vault)
- `eval/questions.sample.yaml` — synthetic public sample that documents the format
- `src/ask_ragu/evalset.py` — `load()` + `check()`; `uv run python -m ask_ragu.evalset <file> [vault]`
- `tests/test_evalset.py` — the checker against a throwaway vault matching the sample
- `.gitignore`

Decisions made here:

- Format (YAML): `id`, `kind` (`single` | `hop` | `overview` | `unanswerable`), `question`, `gold` (vault paths that must **all** be in the assembled context for a hit; empty for unanswerable), `via` (hop only: the note the question is about), `origin` (`owner` | `draft`).
- A hop is checked, not assumed: the checker parses the `via` note at the vault's HEAD and requires a link from it to every other gold note. All 7 draft hops pass this against the real vault.
- The checker reads the vault through the indexer's own code (`git ls-tree`, `read_blobs`, `parse_note`, `is_indexable`), so "gold path exists" means "exists and is indexable at the committed state", the same view retrieval will have.
- Loader lives in `src/ask_ragu/evalset.py` (not `scripts/`) because Sprint 4 Task 5's harness loads the same file.
- Drafts: Claude drafted 18 candidates from the MOCs and the actual link graph (6 single, 7 hop, 3 overview, 2 unanswerable), all marked `origin: draft`; the checker warns until each is rewritten in the owner's words or replaced. D-003's point is that the questions are the owner's and fixed before retrieval tuning (Sprint 4), so the rewrite must happen before Sprint 4 starts.
- Unanswerable questions are adjacent-but-absent topics (<Topic A> next to <Topic B>; <Topic C> next to <Topic D>), verified absent from every chunk on 2026-10-06. They test refusal better than random trivia, which a model is tempted to answer from its own knowledge.

Gotchas:

- `git status` shows `eval/` but never the private file: `git check-ignore -v eval/questions.private.yaml` confirms the rule. The Docker image doesn't copy `eval/` at all (`COPY` lists only `src`, `migrations`).
- Gold paths are tied to the vault's current paths: renaming a gold note breaks the file. Rerun the checker after big vault reorganisations (it names the broken path).
- The draft hops lean on concept → concept links; the vault's `## Part of` parent links (concept → MOC) would also make hop questions, once Sprint 3 decides how those edges are typed.
