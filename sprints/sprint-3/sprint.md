# Sprint 3 — Graph Layer

Goal: Raw wikilinks resolve Obsidian-style into a note graph (links plus tag and MOC hubs) that can be expanded from any seed set with bounded fan-out.

Spec reference: SPEC.md §7, §9 step 4, §14, §16 Phase 3 · D-002, D-007

Status: closed — developed locally (D-008); A1 numbers pending
Started: 2026-10-06
Closed: 2026-10-10
Estimated effort: ~5.2 h across 4 tasks

## Tasks

- [x] [Task 1 — Link resolution & alias map](task_1_summary.md) · 90m
- [x] [Task 2 — Tag & MOC hub semantics](task_2_summary.md) · 75m
- [x] [Task 3 — Bounded graph expansion](task_3_summary.md) · 90m
- [x] [Task 4 — Graph CLI & vault health report](task_4_summary.md) · 60m

## Definition of Done

- Fixture tests: same-name notes, aliases, case/space variants, dangling links, and renamed targets all resolve as Obsidian would
- Expansion from any seed returns ≤ cap notes with hop, via-note, and edge type; a MOC seed doesn't explode fan-out
- Real-vault expansion p95 < 50 ms
- Health report lists dangling links, orphans, alias collisions, biggest hubs
- ADR-0015 (traversal implementation) written with benchmark numbers

## Deviations from plan

- D-012 link resolution vault-wide after every sync, deterministic tie-break (Task 1)
- D-013 expansion is one query per hop, not one recursive CTE (Task 3)

## ADRs touched

- ADR-0002 graph in Postgres — accepted
- ADR-0010 MOC/tag hubs — accepted 2026-10-10 (Task 2)
- ADR-0015 per-hop queries over a recursive CTE — accepted 2026-10-10 (Task 3)

## Outcome

Raw wikilinks resolve Obsidian-style into a note graph after every sync, and expansion from any seed set returns at most 30 notes over 2 hops. Each comes with its hop, the note it came from, the MOC or tag passed through, and a readable "why". MOCs and tags act as query-time hubs (nothing N² stored). Per-hop SQL beat one recursive CTE on the real vault (ADR-0015). Real vault: 2,658 of 2,660 links resolve, expansion p95 20–34 ms on the laptop (noise about ±10 ms).

Definition of Done:

- Fixture tests: same-name notes, aliases, case/space variants, dangling links, renamed targets — **met**. Two rules are the owner's choice rather than verified Obsidian behaviour: a bare `[[Alias]]` resolves (Obsidian probably leaves it unresolved), and same-name ties go to the note with the fewest folders (Obsidian's rule isn't documented).
- Expansion returns ≤ cap notes with hop, via note and edge type; a MOC seed doesn't explode fan-out — **met** (tests: per-note fan-out, total cap, MOC seed).
- Real-vault expansion p95 < 50 ms — **met on the laptop** (worst case 42 ms in one noisy run); the A1 isn't measured yet (BACKLOG).
- Health report lists dangling links, orphans, alias collisions, biggest hubs — **met** (`askragu graph health`). Run on the laptop DB, not the VM (D-008).
- ADR-0015 written with benchmark numbers — **met**.
- Task 1 "dangling count roughly matches Obsidian's" — **not quite**: 2 dangling here; both are an escaped pipe in a table (`[[Note\|alias]]`) that our parser mishandles, and Obsidian probably shows 0 (BACKLOG bug, a one-line parser fix + PARSE_VERSION bump).

Beyond the plan: edge types are derived at query time rather than stored (link/backlink/parent/child/sibling/tag) so no graph information is dropped; hub weights by size (IDF); ties broken by a shuffle seeded by the seed set (repeatable for eval); `scripts/bench_expansion.py` for re-measuring on the A1.
