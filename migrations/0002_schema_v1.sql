-- Schema v1 (SPEC §7). Everything here is derived from the vault: rebuild, don't back up (ADR-0011).

CREATE TABLE notes (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),  -- survives renames (only path changes)
    path         text NOT NULL UNIQUE,                         -- vault-relative, e.g. "02 Concepts/X.md"
    title        text NOT NULL,                                -- filename stem; not unique (same name in two folders)
    note_type    text NOT NULL CHECK (note_type IN ('meta', 'moc', 'concept', 'source', 'fleeting')),  -- from folder (D-006)
    frontmatter  jsonb NOT NULL DEFAULT '{}',
    content_hash text NOT NULL,                                -- unchanged hash = skip re-embedding
    updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_id      uuid NOT NULL REFERENCES notes ON DELETE CASCADE,
    chunk_order  int NOT NULL,
    heading_path text NOT NULL,                                -- "Title > H2 > H3"
    content      text NOT NULL,
    embedding    vector(384) NOT NULL,                         -- bge-small-en-v1.5; a model change = migration + re-embed
    -- Heading words rank above body words. Generated, so it can never drift from content.
    tsv          tsvector GENERATED ALWAYS AS (
                     setweight(to_tsvector('english', heading_path), 'A') ||
                     setweight(to_tsvector('english', content), 'B')
                 ) STORED,
    UNIQUE (note_id, chunk_order)
);
-- ponytail: no GIN (tsv) / HNSW (embedding) index; ~3k chunks scan in ms. Add when Sprint 4 latency says so.

CREATE TABLE note_links (
    source_note_id uuid NOT NULL REFERENCES notes ON DELETE CASCADE,
    raw_target     text NOT NULL,                              -- link text before resolution; re-resolved every run
    target_note_id uuid REFERENCES notes ON DELETE SET NULL,   -- NULL = dangling; target deleted -> becomes dangling
    link_kind      text NOT NULL CHECK (link_kind IN ('link', 'embed')),  -- [[X]] vs ![[X]] (note embed)
    PRIMARY KEY (source_note_id, raw_target, link_kind)
);
CREATE INDEX note_links_target_idx ON note_links (target_note_id);  -- backlinks: edges are walked both ways

CREATE TABLE note_tags (
    note_id uuid NOT NULL REFERENCES notes ON DELETE CASCADE,
    tag     text NOT NULL,
    PRIMARY KEY (note_id, tag)
);
CREATE INDEX note_tags_tag_idx ON note_tags (tag);              -- tag hub -> its notes

-- Exactly one row: the CHECK on a boolean primary key makes a second row impossible.
CREATE TABLE index_state (
    singleton       boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    last_commit     text,                                      -- NULL until the first full index
    embedding_model text NOT NULL,
    embedding_dim   int NOT NULL,
    updated_at      timestamptz NOT NULL DEFAULT now()
);
