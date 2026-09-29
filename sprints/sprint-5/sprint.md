# Sprint 5 — Generation, Inference Chain & UI

Goal: /chat answers from retrieved context through a config-ordered provider chain (hosted free tiers → local llama.cpp) with validated citations, shown in a minimal web UI.

Spec reference: SPEC.md §10, §15, §16 Phase 5 · D-004, D-005

Status: planned
Started: 
Closed: 
Estimated effort: ~7.0 h across 5 tasks

## Tasks

- [ ] [Task 1 — Provider contract & fallback chain](task_1_summary.md) · 90m
- [ ] [Task 2 — OpenAI-compatible adapter + hosted providers](task_2_summary.md) · 75m
- [ ] [Task 3 — Local llama.cpp provider + model bake-off](task_3_summary.md) · 90m
- [ ] [Task 4 — Grounded prompt + citation validation](task_4_summary.md) · 75m
- [ ] [Task 5 — /chat + minimal web UI](task_5_summary.md) · 90m

## Definition of Done

- Disabling providers one at a time (config edit, no restart) still yields answers from the next; logs say why each was skipped
- Every citation shown maps to a note actually in the context; invalid ones are stripped or flagged
- Unanswerable question → explicit "not in your notes" with no LLM call when below the floor
- UI over HTTPS, behind auth, shows answer, citations with provenance, and the provider used

## Deviations from plan

- (none yet)

## ADRs touched

- ADR-0006 provider chain — accepted
- ADR-0009 exclude training free tiers — proposed, resolve before Task 2

## Outcome

_(fill in at close)_
