# ADR-0015: Graph expansion as one query per hop, not one recursive CTE

Status: accepted
Date: 2026-10-10
Sprint: sprint-3 (task_3)

## Context

Expansion (SPEC §9 step 4) must be bounded per note per hop and in total (D-007). It must also keep the shortest hop per note, prefer direct edges over MOC siblings over tag-mates (ADR-0010), and stay under 50 ms p95. Postgres rejects ORDER BY/LIMIT at the top of a recursive term. The only per-row limit available there is a LATERAL subquery, and a recursive term can't see which notes earlier hops have already reached.

## Decision

`graph/expand.py` runs one SQL query per hop over `hubs.EDGES`. Each query takes the best path per (from, to) pair, keeps at most `GRAPH_FANOUT_CAP` neighbours per frontier note, then the best path per reached note, with already-reached notes excluded before ranking. Equal candidates are ordered by a shuffle seeded by the seed set (repeatable). Python applies `GRAPH_TOTAL_CAP` between hops (MOCs don't count) and stops early once it is spent.

Benchmark (`scripts/bench_expansion.py`, laptop, 748 notes, 2 hops, fan-out 10, total 30, 200 random seed sets each):

| Seeds | Per-hop p50 / p95 | Recursive CTE p50 / p95 | Same notes (Jaccard) |
|---|---|---|---|
| 1 note | 23 / 31 ms | 25 / 35 ms | 0.86 |
| 8 notes | 13 / 20 ms | 187 / 220 ms (102 / 122 with JIT off) | 0.75 |
| 3 MOCs | 25 / 34 ms | 41 / 51 ms | 0.99 |

EXPLAIN ANALYZE, 8 seeds: a per-hop query plans in 2 ms and runs in 11 ms. The recursive CTE runs in 188 ms, 82 ms of it JIT compilation.

## Alternatives considered

- **One recursive CTE with `LATERAL … LIMIT` per walked row,** pruned afterwards: one round trip and no Python loop. But it must materialize the whole edge set first (31k rows, mostly sibling and tag pairs, 26 ms to build), and every walked row scans that set without an index. A note reached by k paths is expanded k times, and hop-2 slots go to notes hop 1 already has. The result is 5–10× slower with many seeds, and it reaches different notes.
- **Per-hop queries restricted to the seeds' neighbourhood** (only links touching the seeds or the MOCs next to them): identical rows (checked on 300 seed sets), but no faster (11 vs 12 ms p50). Planning and the fixed CTE cost dominate at this size.

## Consequences

- Depth is a loop bound (`GRAPH_MAX_HOPS`), so 1-hop and 2-hop are both one setting for the Sprint 4 ablation.
- With 8 seeds, hop 1 usually fills the total cap, so hop 2 never runs (that's why 8 seeds is faster than 1).
- About half of each hop is rebuilding the deduplicated `links` CTE over every link. If the A1 or a bigger vault breaks 50 ms, store the resolved, deduplicated links with MOC flags at resolve time (O(links) rows, not hub pairs).
- Laptop noise between identical runs is about ±10 ms at p95 (1 seed: 31–42 ms over four runs, after the tie shuffle was added, which costs nothing measurable). Real-vault p95 on the A1 isn't measured yet (D-008).
