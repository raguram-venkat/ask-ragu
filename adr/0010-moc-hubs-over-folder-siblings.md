# ADR-0010: MOC and tag hubs over folder-sibling edges

Status: accepted (2026-10-10, sprint-3/task_2)
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

The vault's folders (00 Meta, 01 MOCs, 02 Concepts, 03 Sources, 04 Fleeting) encode note type, not topic. Topic structure lives in MOCs and tags. (D-002)

## Decision

Drop folder_sibling edges. Treat MOC notes and tags as hubs: note → hub → note counts as one structural hop; tags weighted by rarity, very common tags ignored; MOC chunks not returned as context.

Settled with the owner in sprint-3/task_2: a MOC is passed through (sibling = 1 hop); MOC → MOC is an ordinary hop, so MOC chains can't snowball. Tag hubs are a fallback that fills only the slots links and MOCs leave. Edge types (link, backlink, parent, child, sibling, tag) are derived at query time from links + note_type + tags, never stored: hub pairs would be N² rows, and parent/child would repeat note_type. Nothing the graph holds is dropped; every path is returned and the expansion chooses.

## Alternatives considered

- Folder-sibling edges — would link every Concept note to every other Concept note.
- Materialized pairwise edges for MOC/tag co-membership — N² rows per hub.
- MOC as an ordinary node (sibling = 2 hops) — a MOC would use up a hop-1 slot while its chunks are never returned.
- Tag hubs equal to MOC hubs — a tag is the note's domain (one per note, up to 42 notes), weaker evidence than a MOC listing.
- A stored typed `parent` edge from `## Part of` — 580 of 587 concept → MOC links are already under `## Part of`, so note_type tells parent apart; storing it needs a parser change and a full index.

## Consequences

- Folder becomes `note_type`, used as a ranking prior instead.
- Hub fan-out must be capped per hop (D-007). Real vault: a non-MOC note has p50 18 / max 62 siblings and p50 16 / max 41 tag-mates.
- `GRAPH_TAG_HUB_MAX_SHARE` in .env (query time, never re-indexes).
