-- Lexical search (Sprint 4 Task 1): GIN index for `tsv @@ query`. Real vault, ~2k chunks:
-- OR-ed question queries p50 21 -> 12 ms. Replaces the "no GIN index" ponytail note in 0002.
CREATE INDEX chunks_tsv_idx ON chunks USING gin (tsv);
