# Task 2 — Schema v1

Status: todo
Est: 60m
Spec: SPEC.md §7 · D-002, D-006

What: Migration 0002 creating notes, chunks, note_links, note_tags, and index_state.

Approach: notes(uuid id, unique path, title, note_type, frontmatter jsonb, content_hash); chunks(note fk ON DELETE CASCADE, heading_path, content, embedding vector(384), generated tsvector, chunk_order); note_links(source, raw_target, nullable target, link_kind); index_state(last_commit, embedding_model, embedding_dim).

Read first:

- Postgres: generated columns, foreign keys with cascade
- pgvector: vector column type

Watch out for:

- Keep raw link text so Sprint 3 can re-resolve every run — never store only a resolved id.
- note_type from folder: 00 Meta → meta, 01 MOCs → moc, 02 Concepts → concept, 03 Sources → source, 04 Fleeting → fleeting (D-006).
- Vector dimension is baked into the column: a model change = migration + full re-embed; index_state makes the mismatch detectable at startup.

Done when: Applies on a fresh DB, no-op on re-run; deleting a note cascades to its chunks, links, and tags.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
