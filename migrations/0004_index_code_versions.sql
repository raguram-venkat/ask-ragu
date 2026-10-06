-- Code versions and per-note link/tag hash (ADR-0017).
-- notes.meta_hash: hash of a note's extracted links + tags. Compared on upsert, so a parser change
-- that alters only links/tags still rewrites them. NULL on existing rows -> rewritten once.
ALTER TABLE notes ADD COLUMN meta_hash text;
-- Which code built the index (readable; the comparison itself happens through settings_hash).
ALTER TABLE index_state ADD COLUMN embed_version int, ADD COLUMN parse_version int;
