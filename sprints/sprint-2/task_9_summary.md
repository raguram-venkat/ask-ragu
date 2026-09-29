# Task 9 — Eval set v0

Status: todo
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

- 

Decisions made here:

- 

Gotchas:

- 
