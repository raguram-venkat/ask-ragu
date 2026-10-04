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

From Task 1 profiling (real vault, `scripts/profile_vault.py`):

- Title = filename stem: the vault has no H1 headings at all (only H2/H3).
- Frontmatter keys seen: `type`, `created`, `status`, `domain`, `tags` on almost every note; `moc-kind`, `concept-kind`, `source-type`, `author`, `purpose` on some. No `aliases` key anywhere. Store it all in `frontmatter jsonb`; no extra columns needed.
- 19 notes have no frontmatter (all in one Concepts subfolder), so `note_type` must come from the folder (as D-006 says), not from `type:`. Where both exist they always agree.
- `04 Fleeting/` currently holds no notes; keep `fleeting` as a valid type anyway.
- 19 filenames repeat across folders, so `path` is unique but `title` is not: no unique index on title.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
