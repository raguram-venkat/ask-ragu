# Sprint 2 — Webhook & Incremental Indexing

Goal: A push to the vault repo is HMAC-verified, acknowledged within GitHub's 10 s window, and incrementally indexed (parse → chunk → embed → upsert) in a background task.

Spec reference: SPEC.md §7, §8, §12, §16 Phase 2 · D-001, D-003, D-006, D-008

Status: active — starts 2026-10-04, developed locally (D-008)
Started: 2026-10-04
Closed: 
Estimated effort: ~11.2 h across 9 tasks

## Tasks

- [x] [Task 1 — Vault profiling (data before design)](task_1_summary.md) · 60m
- [x] [Task 2 — Schema v1](task_2_summary.md) · 60m
- [x] [Task 3 — Note parser & cleaning](task_3_summary.md) · 90m
- [x] [Task 4 — Heading-aware chunker + fixture vault](task_4_summary.md) · 90m
- [x] [Task 5 — Local embeddings on ARM](task_5_summary.md) · 60m
- [x] [Task 6 — Full index command](task_6_summary.md) · 75m
- [x] [Task 7 — Webhook receiver](task_7_summary.md) · 90m
- [x] [Task 8 — Incremental sync & reconciliation](task_8_summary.md) · 90m
- [ ] [Task 9 — Eval set v0](task_9_summary.md) · 60m

## Definition of Done

- Editing, renaming, and deleting a note in a local clone, then syncing, is reflected in Postgres; a rename keeps the note's id. The live GitHub → VM check waits for Sprint 1 Tasks 4–6 (D-008)
- Locally signed requests: wrong signature → 401, repeated delivery id → no-op, ping → 200; force-push → full reindex instead of a crash
- Fixture-vault tests cover every exclusion, cleaning, link-syntax, and chunking rule
- Incremental sync ends in exactly the same DB state as a full index
- Eval set v0 (private) has ≥ 15 questions with gold notes

## Deviations from plan

- D-008 — developed locally; live webhook delivery verified once the A1 is up

## ADRs touched

- ADR-0003 self-hosted embeddings — accepted
- ADR-0004 incremental git diff — accepted
- ADR-0005 ack-fast background sync — accepted
- ADR-0011 index is disposable — proposed

## Outcome

_(fill in at close)_
