# ADR-0010: MOC and tag hubs over folder-sibling edges

Status: proposed
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

The vault's folders (00 Meta, 01 MOCs, 02 Concepts, 03 Sources, 04 Fleeting) encode note type, not topic. Topic structure lives in MOCs and tags. (D-002)

## Decision

Drop folder_sibling edges. Treat MOC notes and tags as hubs: note → hub → note counts as one structural hop; tags weighted by rarity, very common tags ignored; MOC chunks not returned as context.

## Alternatives considered

- Folder-sibling edges — would link every Concept note to every other Concept note.
- Materialized pairwise edges for MOC/tag co-membership — N² rows per hub.

## Consequences

- Folder becomes `note_type`, used as a ranking prior instead.
- Hub fan-out must be capped per hop (D-007).
