-- Hash of the settings that shape the index (D-010). A different hash at sync time -> full index.
-- NULL (every index built before this migration) counts as a mismatch: one full index after the
-- upgrade, which re-embeds nothing because the notes' content_hash values are unchanged.
ALTER TABLE index_state ADD COLUMN settings_hash text;
