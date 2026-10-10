# Task 3 — Bounded graph expansion

Status: done
Est: 90m
Spec: SPEC.md §9 step 4 · D-007

What: Given seed note ids, return neighbours up to 2 hops as (note_id, hop, via_note, edge_type), bounded per hop and in total.

Approach: Two candidates: (a) recursive CTE with a total cap, pruned afterwards; (b) explicit hop-1 and hop-2 queries with LATERAL … LIMIT, pruning between hops. Benchmark both on the real vault; record the choice as ADR-0015.

Read first:

- Postgres: WITH RECURSIVE (incl. the CYCLE clause)
- Postgres: LATERAL subqueries

Watch out for:

- Postgres rejects ORDER BY/LIMIT inside a recursive term — per-hop beam pruning can't live inside one recursive CTE. That's the real trade-off.
- Cycles (A ↔ B) and duplicate paths: keep the shortest hop per note.
- Traverse both link directions — backlinks are context too.

Done when: Fixture neighbourhoods match expected; EXPLAIN ANALYZE numbers recorded; ADR-0015 written.

---

Filled in while working

Files touched:

- `src/ask_ragu/graph/expand.py` — `expand(conn, seeds) -> list[Reached]` (note_id, hop, from_note, edge_type, via_note, via_tag, weight, is_moc); `HOP` query
- `tests/test_expand.py` — tie shuffle repeatable per seed set; shortest hop through a cycle, backlinks, MOC pass-through, MOC → MOC as a real hop, tag fallback filling the last fan-out slot, MOC-seed fan-out cap, total cap with MOCs free, 1 hop, several seeds
- `tests/conftest.py` — `make_graph` fixture (shared by test_hubs and test_expand)
- `scripts/bench_expansion.py`, `scripts/README.md` — per-hop vs recursive CTE on the real index
- `src/ask_ragu/settings.py`, `.env.example` — `GRAPH_MAX_HOPS=2`, `GRAPH_FANOUT_CAP=10`, `GRAPH_TOTAL_CAP=30`
- `adr/0015-…`, `DEVIATIONS.md` D-013, `SPEC.md` §6, §9, §13, §16, `BACKLOG.md` (2 lines)

Decisions made here:

- Per-hop queries over one recursive CTE (ADR-0015), on both speed and behaviour. Laptop p95: 31 ms for 1 seed, 20 ms for 8 seeds, 31 ms for 3 MOC seeds. The recursive CTE took 220 ms for 8 seeds.
- Order, for both the per-note fan-out cap and the total cap: direct edges, then siblings, then tag-mates. Within a class, higher weight first.
- Remaining ties: a shuffle seeded by the seed set (md5 of note id + sorted seed ids), the owner's call in review (2026-10-10) instead of note-id order, which picked the same siblings every time. Same seeds give the same picks, so eval runs stay repeatable; different seeds give different picks. Real vault: from each of the biggest MOC's 41 members, every sibling gets picked at least once, the most popular 10 times.
- One row per reached note, its best path. The other paths are still available from `neighbours()`, so nothing is lost (ADR-0010).
- MOCs are returned (provenance: "part of X") but don't count toward the total cap, because they're never context (ADR-0010). They do take per-note fan-out slots, and they're expanded at the next hop (for the parent MOC).
- The total cap is applied hop by hop, best first, and the loop stops when it's spent. So every returned note's `from_note` is a seed or another returned note, and the provenance chain never breaks.
- Starting caps: fan-out 10 (a median note has 4 direct + 18 sibling + 16 tag neighbours, so 10 keeps its direct ones and some siblings) and total 30 (SPEC §9's example). Sprint 4 tunes both with the eval.

Gotchas:

- Postgres JIT starts compiling the recursive CTE (its cost estimate is high) and adds about 80 ms. The per-hop queries never trigger it (same timings with `jit=off`), so the default stays.
- Restricting each hop to the seeds' neighbourhood gave identical rows but no speed-up (planning plus fixed CTE cost dominate at 748 notes), so the simpler EDGES stays.
- With 8 seeds, hop 1 already fills the total cap (8 × 10 candidates ≥ 30), so hop 2 never runs and 8 seeds come out faster than 1.
- The shuffle still knows nothing about relevance: which 5 of a MOC's 40 members a note keeps is a coin flip per question. Sprint 4 should rank by similarity to the question first (BACKLOG). Learning edge weights from feedback is a post-v1 idea (BACKLOG).
