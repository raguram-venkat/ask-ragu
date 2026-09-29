# Task 3 — Bounded graph expansion

Status: todo
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

- 

Decisions made here:

- 

Gotchas:

- 
