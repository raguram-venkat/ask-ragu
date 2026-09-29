# Sprint 6 — Evaluation, Hardening & Demo

Goal: Measured end-to-end quality, every known edge case tested, a security and ops pass, CI on every push, and a README + demo script that tell the story in 5 minutes.

Spec reference: SPEC.md §12, §14, §15, §16 Phase 6

Status: planned
Started: 
Closed: 
Estimated effort: ~7.5 h across 6 tasks

## Tasks

- [ ] [Task 1 — End-to-end eval](task_1_summary.md) · 75m
- [ ] [Task 2 — Edge-case test sweep](task_2_summary.md) · 90m
- [ ] [Task 3 — Security pass](task_3_summary.md) · 75m
- [ ] [Task 4 — Observability & rebuild drill](task_4_summary.md) · 75m
- [ ] [Task 5 — CI](task_5_summary.md) · 60m
- [ ] [Task 6 — README, demo script & final INDEX pass](task_6_summary.md) · 75m

## Definition of Done

- Generation rubric results and final retrieval ablation recorded (aggregates in README)
- Every SPEC §14 item and every D-entry has a test or a documented manual check
- External port scan shows only 80/443; secret scan clean over full git history; containers run as non-root
- Rebuild drill: empty volume → full reindex → working /chat, with the time recorded
- CI green on main; demo script rehearsed end to end once

## Deviations from plan

- (none yet)

## ADRs touched

- All proposed ADRs resolved: accepted or superseded
- ADR-0011 index is disposable — confirmed by the rebuild drill

## Outcome

_(fill in at close)_
