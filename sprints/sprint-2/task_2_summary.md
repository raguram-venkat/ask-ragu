# Task 2 — Schema v1

Status: done
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

- `migrations/0002_schema_v1.sql` — notes, chunks, note_links, note_tags, index_state
- `tests/test_migrate.py` — fixture search path now includes `public` (where the `vector` type lives); new test: applies once, tsv matches, delete cascades

Decisions made here:

- `note_type` is `text` + `CHECK`, not a Postgres `ENUM`: adding a value to an enum needs `ALTER TYPE` and can't be removed later; a CHECK is just replaced.
- `tsv` covers `heading_path` (weight A) and `content` (weight B), so a query word that appears in a heading or title ranks higher. Generated `STORED`, so it can't drift from the content.
- `embedding` is `NOT NULL`: the pipeline embeds before upserting (SPEC §8 steps 5–6), so a chunk without a vector is a bug.
- `note_links.target_note_id` uses `ON DELETE SET NULL`: deleting a target note turns links to it into dangling links (still recorded) rather than deleting the other note's links. Primary key `(source, raw_target, link_kind)`, so the parser deduplicates repeated links in a note.
- `link_kind` is `link` (`[[X]]`) or `embed` (`![[X]]`, a note embed); image embeds are never stored.
- `index_state` has exactly one row, enforced by `CHECK (singleton)` on a boolean primary key. The indexer inserts it on the first full index (Task 6).
- No GIN/HNSW indexes yet: with ~3k chunks a sequential scan takes milliseconds. Revisit with Sprint 4 latency numbers.

Gotchas:

- `title` is not unique (19 duplicate names in the real vault), so no unique index on it.
- Tests run in a throwaway `migrate_test` schema; `CREATE EXTENSION IF NOT EXISTS vector` is a no-op there because extensions are per database, installed in `public`.
