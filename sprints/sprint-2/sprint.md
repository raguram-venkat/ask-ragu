# Sprint 2 — Webhook & Incremental Indexing

Goal: A push to the vault repo is HMAC-verified, acknowledged within GitHub's 10 s window, and incrementally indexed (parse → chunk → embed → upsert) in a background task.

Spec reference: SPEC.md §7, §8, §12, §16 Phase 2 · D-001, D-003, D-006

Status: planned
Started: 
Closed: 
Estimated effort: ~11.2 h across 9 tasks

## Tasks

- [ ] [Task 1 — Vault profiling (data before design)](task_1_summary.md) · 60m
- [ ] [Task 2 — Schema v1](task_2_summary.md) · 60m
- [ ] [Task 3 — Note parser & cleaning](task_3_summary.md) · 90m
- [ ] [Task 4 — Heading-aware chunker + fixture vault](task_4_summary.md) · 90m
- [ ] [Task 5 — Local embeddings on ARM](task_5_summary.md) · 60m
- [ ] [Task 6 — Full index command](task_6_summary.md) · 75m
- [ ] [Task 7 — Webhook receiver](task_7_summary.md) · 90m
- [ ] [Task 8 — Incremental sync & reconciliation](task_8_summary.md) · 90m
- [ ] [Task 9 — Eval set v0](task_9_summary.md) · 60m

## Definition of Done

- Editing, renaming, and deleting a note then pushing is reflected in Postgres within ~1 minute; a rename keeps the note's id
- Wrong signature → 401; redelivered webhook → no-op; ping → 200; force-push → full reindex instead of a crash
- Fixture-vault tests cover every exclusion, cleaning, link-syntax, and chunking rule
- Incremental sync ends in exactly the same DB state as a full index
- Eval set v0 (private) has ≥ 15 questions with gold notes

## Deviations from plan

- (none yet)

## ADRs touched

- ADR-0003 self-hosted embeddings — accepted
- ADR-0004 incremental git diff — accepted
- ADR-0005 ack-fast background sync — accepted
- ADR-0011 index is disposable — proposed

## Outcome

_(fill in at close)_
