# Task 2 — Tag & MOC hub semantics

Status: todo
Est: 75m
Spec: SPEC.md §7 · D-002, ADR-0010

What: Define how tags and MOCs connect notes without materializing N² edges.

Approach: Tags and MOC notes are hubs: note → hub → note is one structural hop. Tags weighted by rarity (IDF), tags above the Sprint 2 cutoff ignored. MOC notes are traversed through but their chunks never returned as context.

Read first:

- SPEC §7, ADR-0010
- Your Sprint 2 Task 1 findings

Watch out for:

- A 50-link MOC materialized pairwise = 1,225 rows — don't.
- Folders are note types here, not topics (D-002).
- Fleeting and meta notes: traversable, lower prior at ranking (Sprint 4).

Done when: Short design note written here; hub-mediated neighbours correct on fixtures.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
