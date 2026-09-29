# Sprint 3 — Graph Layer

Goal: Raw wikilinks resolve Obsidian-style into a note graph (links plus tag and MOC hubs) that can be expanded from any seed set with bounded fan-out.

Spec reference: SPEC.md §7, §9 step 4, §14, §16 Phase 3 · D-002, D-007

Status: planned
Started: 
Closed: 
Estimated effort: ~5.2 h across 4 tasks

## Tasks

- [ ] [Task 1 — Link resolution & alias map](task_1_summary.md) · 90m
- [ ] [Task 2 — Tag & MOC hub semantics](task_2_summary.md) · 75m
- [ ] [Task 3 — Bounded graph expansion](task_3_summary.md) · 90m
- [ ] [Task 4 — Graph CLI & vault health report](task_4_summary.md) · 60m

## Definition of Done

- Fixture tests: same-name notes, aliases, case/space variants, dangling links, and renamed targets all resolve as Obsidian would
- Expansion from any seed returns ≤ cap notes with hop, via-note, and edge type; a MOC seed doesn't explode fan-out
- Real-vault expansion p95 < 50 ms
- Health report lists dangling links, orphans, alias collisions, biggest hubs
- ADR-0015 (traversal implementation) written with benchmark numbers

## Deviations from plan

- (none yet)

## ADRs touched

- ADR-0002 graph in Postgres — accepted
- ADR-0010 MOC/tag hubs — proposed, resolve before Task 2
- ADR-0015 traversal implementation — to write in Task 3

## Outcome

_(fill in at close)_
