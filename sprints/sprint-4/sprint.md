# Sprint 4 — Retrieval

Goal: A question returns a ranked, provenance-tagged context — lexical + vector seeds fused with RRF, expanded through the graph, best chunk per note, packed to a token budget — with an ablation table proving each stage earns its place.

Spec reference: SPEC.md §9, §12, §16 Phase 4 · D-006, D-007

Status: in progress
Started: 2026-10-10
Closed: 
Estimated effort: ~6.5 h across 6 tasks

## Tasks

- [x] [Task 1 — Lexical search](task_1_summary.md) · 60m
- [x] [Task 2 — Vector search](task_2_summary.md) · 45m
- [x] [Task 3 — RRF fusion + relevance floor](task_3_summary.md) · 60m
- [x] [Task 4 — Expansion, scoring & context assembly](task_4_summary.md) · 90m
- [x] [Task 5 — Retrieval eval harness + ablation](task_5_summary.md) · 90m
- [ ] [Task 6 — /search debug endpoint](task_6_summary.md) · 45m
- [ ] [Task 7 — Dev agent on open-weight models](task_7_summary.md) · 2.5h — added 2026-10-13 (tooling, ADR-0022)

## Definition of Done

- One command prints hit@k and MRR for lexical / vector / hybrid / hybrid+graph on eval v0
- Every returned chunk carries note title, heading_path, how it was reached (direct, or via note X and edge type), and score parts
- The unanswerable eval questions return an empty context (relevance floor), not noise
- p95 retrieval latency on the Micro recorded (target < 300 ms, LLM excluded; needs sprint-1/task_6 done, D-014 — if the Micro misses the target, a D-entry records the measured number and the new target)

## Deviations from plan

- D-014 — host is the E2.1.Micro (latency DoD and Task 6 measured there)
- D-015 — no local model (Sprint 5 impact only)

## ADRs touched

- ADR-0001 Postgres over OpenSearch — accepted
- ADR-0008 RRF + hop decay — accepted
- ADR-0019 lexical query from OR-ed lexemes — accepted (Task 1)
- ADR-0020 Micro host, ADR-0021 hosted open-weight inference — proposed 2026-10-13 (D-014, D-015)
- ADR-0022 dev agents see public-repo content only — proposed (Task 7)

## Outcome

_(fill in at close)_
