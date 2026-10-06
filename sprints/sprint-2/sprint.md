# Sprint 2 — Webhook & Incremental Indexing

Goal: A push to the vault repo is HMAC-verified, acknowledged within GitHub's 10 s window, and incrementally indexed (parse → chunk → embed → upsert) in a background task.

Spec reference: SPEC.md §7, §8, §12, §16 Phase 2 · D-001, D-003, D-006, D-008

Status: closed — developed locally (D-008); live GitHub → VM checks wait for the A1
Started: 2026-10-04
Closed: 2026-10-06
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
- [x] [Task 9 — Eval set v0](task_9_summary.md) · 60m

## Definition of Done

- Editing, renaming, and deleting a note in a local clone, then syncing, is reflected in Postgres; a rename keeps the note's id. The live GitHub → VM check waits for Sprint 1 Tasks 4–6 (D-008)
- Locally signed requests: wrong signature → 401, repeated delivery id → no-op, ping → 200; force-push → full reindex instead of a crash
- Fixture-vault tests cover every exclusion, cleaning, link-syntax, and chunking rule
- Incremental sync ends in exactly the same DB state as a full index
- Eval set v0 (private) has ≥ 15 questions with gold notes

## Deviations from plan

- D-008 — developed locally; live webhook delivery verified once the A1 is up
- D-010 — index settings and indexing-code versions in a settings hash (automatic full index); the VM clone is reset to the indexed commit
- D-011 — syncs serialized across processes by a per-schema Postgres advisory lock
- Synthetic fixture vault deferred (owner agreed): parser/chunker rules are covered by inline-string unit tests, sync by throwaway git repos → BACKLOG

## ADRs touched

- ADR-0003 self-hosted embeddings — accepted
- ADR-0004 incremental git diff — accepted (amended by D-010)
- ADR-0005 ack-fast background sync — accepted
- ADR-0011 index is disposable — proposed
- ADR-0016 int8 bge-small, batch 1 — accepted (new)
- ADR-0017 index freshness: settings hash + code versions; one index per schema — accepted (new)
- ADR-0018 one sync at a time per index: advisory lock — accepted (new)

## Outcome

A signed push (or app startup, or `askragu index`) syncs the vault into Postgres incrementally — rename-aware, re-embedding only changed notes, full index whenever a diff can't be trusted — and incremental sync was proven equal to a full index both in tests and by replaying the real vault's 8 commits. Real vault: 748 notes → 1,965 chunks (int8 bge-small, ~25 chunks/s on the laptop), 2,660 links, 84 tags.

Definition of Done:

- Edit / rename / delete reflected in Postgres, rename keeps the id — **met** (tests on origin + clone; real-vault replay incl. a 201-rename commit). Live GitHub → VM waits for the A1 (D-008).
- Signed requests: wrong signature 401, repeated delivery no-op, ping 200; force-push → full index — **met** (tests + live stack).
- Fixture-vault tests cover every exclusion, cleaning, link-syntax and chunking rule — **met in substance, not in form**: every rule has unit tests (inline strings; throwaway git repos for sync), but the shared synthetic fixture vault was deferred (owner agreed) → BACKLOG.
- Incremental sync ends in the same DB state as a full index — **met** (snapshot comparison after every step in tests; real 8-commit replay identical on notes, chunks, links, tags).
- Eval set v0 (private) ≥ 15 questions with gold notes — **met as drafts**: 18 questions (7 verified hops, 2 unanswerable) pass the checker; the owner rewrites them before Sprint 4 (D-003).

Beyond the plan: settings hash + code versions with a golden test and pre-commit hook (ADR-0017), cross-process sync lock (ADR-0018), `/index/status`, "Part of" metadata headings out of heading paths, int8 model choice (ADR-0016), arm64 image smoke-tested under QEMU.
