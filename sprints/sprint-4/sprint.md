# Sprint 4 — Retrieval

Goal: A question returns a ranked, provenance-tagged context — lexical + vector seeds fused with RRF, expanded through the graph, best chunk per note, packed to a token budget — with an ablation table proving each stage earns its place.

Spec reference: SPEC.md §9, §12, §16 Phase 4 · D-006, D-007

Status: planned
Started: 
Closed: 
Estimated effort: ~6.5 h across 6 tasks

## Tasks

- [ ] [Task 1 — Lexical search](task_1_summary.md) · 60m
- [ ] [Task 2 — Vector search](task_2_summary.md) · 45m
- [ ] [Task 3 — RRF fusion + relevance floor](task_3_summary.md) · 60m
- [ ] [Task 4 — Expansion, scoring & context assembly](task_4_summary.md) · 90m
- [ ] [Task 5 — Retrieval eval harness + ablation](task_5_summary.md) · 90m
- [ ] [Task 6 — /search debug endpoint](task_6_summary.md) · 45m

## Definition of Done

- One command prints hit@k and MRR for lexical / vector / hybrid / hybrid+graph on eval v0
- Every returned chunk carries note title, heading_path, how it was reached (direct, or via note X and edge type), and score parts
- The unanswerable eval questions return an empty context (relevance floor), not noise
- p95 retrieval latency on the VM recorded (target < 300 ms, LLM excluded)

## Deviations from plan

- (none yet)

## ADRs touched

- ADR-0001 Postgres over OpenSearch — accepted
- ADR-0008 RRF + hop decay — accepted

## Outcome

_(fill in at close)_
