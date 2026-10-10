# Task 2 — Tag & MOC hub semantics

Status: done
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

- `src/ask_ragu/graph/hubs.py` — `EDGES` (one SQL text, every one-hop edge incl. hubs; takes `%(max_tag_share)s`) and `neighbours(conn, note_ids)`
- `tests/test_hubs.py` — a hand-built 6-note graph: link/backlink, parent/child, sibling via MOC, tag fallback with IDF weights, cutoff, self-link, dangling, link + embed deduplicated, MOC → MOC not passed through
- `src/ask_ragu/settings.py`, `.env.example` — `GRAPH_TAG_HUB_MAX_SHARE=0.10`
- `adr/0010-…` — accepted, with the decisions below; `BACKLOG.md` — typed parent edge closed

Design note (ADR-0010, settled with the owner):

- **Nothing is materialized.** A hub is a stepping stone computed at query time from `note_links`, `notes.note_type` and `note_tags`. Storing hub pairs would be N² rows, and storing parent/child would repeat `note_type`.
- **Edge types,** from the source's point of view:
  - `link` / `backlink`: neither note is a MOC, or both are.
  - `parent` / `child`: a MOC and one of its members.
  - `sibling` (`via_note` = the MOC): two members of the same MOC.
  - `tag` (`via_tag`): two notes sharing a tag.
- **Membership** = a link either way between a MOC and a non-MOC note.
- **A MOC is passed through:** note → MOC → sibling is one hop. MOC → MOC is an ordinary link, so parent-MOC chains don't cascade.
- **Tag hubs are a fallback:** Task 3 fills only the slots that links and MOCs leave. Tags on more than `GRAPH_TAG_HUB_MAX_SHARE` of notes connect nothing.
- **Weights:** 1 for direct edges. Hub edges get ln(N / hub size) / ln(N), so a smaller MOC or tag says more. The same formula covers MOCs and tags.
- **Nothing is lost:** every path is a row (one note can be a link, a sibling via two MOCs and a tag-mate at once). Picking the best path per note, and capping, is Task 3.

Decisions made here:

- One SQL text in Python rather than a view or SQL function: the tag cutoff comes from `.env`, and it can't be hard-coded in a migration. Task 3 can embed the same text in either traversal it benchmarks.
- MOCs keep their tag edges (each MOC carries its domain tag), since dropping them would lose information. Task 3 decides whether a MOC reached by tag is worth a slot.

Gotchas:

- Real vault, edges out of a non-MOC note (p50 / p95 / max): siblings 18 / 41 / 62, tag-mates 16 / 41 / 41, distinct neighbours 19 / 42 / 73. Out of a MOC: children 10 / 32 / 42. Hub fan-out dominates, so the per-hop caps in Task 3 are what keep a hop small.
- One hop takes 11 ms p50 / 15 ms p95 (one note or 8 seeds, laptop). About 8 ms of that is the `links` CTE deduplicating all ~2.7k links on every call. Two hops done this way come to roughly 30 ms, under the 50 ms target but without much margin on the A1. First lead for Task 3: filter `links` and `member` by the frontier before deduplicating.
