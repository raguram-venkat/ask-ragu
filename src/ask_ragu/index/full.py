"""Full index (SPEC §8): every committed note in the vault -> notes, chunks, note_links, note_tags.

Idempotent: a second run over the same commit writes nothing and embeds nothing.
Embedding happens outside the transaction; each note is then written in its own transaction.
"""

import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from ask_ragu.index.chunk import chunk_note
from ask_ragu.index.embed import embed_passages, passage_text
from ask_ragu.index.parse import ParsedNote, parse_note
from ask_ragu.settings import settings

log = logging.getLogger(__name__)

# Returns the id only if the row was inserted or actually changed, so unchanged notes are skipped.
UPSERT_NOTE = """
INSERT INTO notes (path, title, note_type, frontmatter, content_hash)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (path) DO UPDATE SET
    title = EXCLUDED.title, note_type = EXCLUDED.note_type, frontmatter = EXCLUDED.frontmatter,
    content_hash = EXCLUDED.content_hash, updated_at = now()
WHERE (notes.title, notes.note_type, notes.frontmatter, notes.content_hash) IS DISTINCT FROM
    (EXCLUDED.title, EXCLUDED.note_type, EXCLUDED.frontmatter, EXCLUDED.content_hash)
RETURNING id
"""

UPSERT_STATE = """
INSERT INTO index_state (last_commit, embedding_model, embedding_dim) VALUES (%s, %s, %s)
ON CONFLICT (singleton) DO UPDATE SET
    last_commit = EXCLUDED.last_commit, embedding_model = EXCLUDED.embedding_model,
    embedding_dim = EXCLUDED.embedding_dim, updated_at = now()
"""


@dataclass
class Stats:
    notes: int = 0  # indexable notes at this commit
    written: int = 0  # note rows inserted or changed
    embedded: int = 0  # notes re-chunked and re-embedded
    chunks: int = 0  # chunks embedded
    deleted: int = 0  # notes in the DB whose file is gone


def git(vault: Path, *args: str) -> str:
    # safe.directory: the mounted vault is owned by a different user than the container's.
    cmd = ["git", "-c", f"safe.directory={vault}", "-C", str(vault), *args]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def content_hash(note: ParsedNote) -> str:
    """Everything the chunks and vectors depend on; a change to any of it re-embeds the note."""
    s = settings
    key = [note.title, note.body, s.chunk_max_chars, s.chunk_merge_below_chars,
           s.chunk_overlap_chars, s.stub_min_chars, s.embedding_model, s.embedding_model_file,
           s.embedding_pooling]  # fmt: skip
    return hashlib.sha256(json.dumps(key).encode()).hexdigest()


def index_full(conn: psycopg.Connection, vault: Path) -> Stats:
    commit = git(vault, "rev-parse", "HEAD").strip()
    if git(vault, "--no-optional-locks", "status", "--porcelain"):
        log.warning("vault has uncommitted changes; indexing the working tree as %s", commit)
    # -z: NUL-separated and unquoted; without it git escapes non-ASCII paths ("Caf\303\251.md").
    paths = [p for p in git(vault, "ls-files", "-z").split("\0") if p]
    old_hashes = dict(conn.execute("SELECT path, content_hash FROM notes").fetchall())

    stats, seen = Stats(), []
    for path in paths:
        note = parse_note(path, (vault / path).read_text(encoding="utf-8", errors="replace"))
        if note is None:
            continue
        stats.notes += 1
        seen.append(path)
        h = content_hash(note)
        chunks = None  # None = keep the existing chunks
        if old_hashes.get(path) != h:
            chunks = chunk_note(note.title, note.body)
            texts = [passage_text(c.heading_path, c.content) for c in chunks]
            vectors = embed_passages(texts) if texts else []

        with conn.transaction():
            row = conn.execute(
                UPSERT_NOTE, (path, note.title, note.note_type, Jsonb(note.frontmatter), h)
            ).fetchone()
            if row is None:  # nothing about this note changed
                continue
            (note_id,) = row
            stats.written += 1
            with conn.cursor() as cur:
                if chunks is not None:
                    cur.execute("DELETE FROM chunks WHERE note_id = %s", (note_id,))
                    cur.executemany(
                        "INSERT INTO chunks"
                        " (note_id, chunk_order, heading_path, content, embedding)"
                        " VALUES (%s, %s, %s, %s, %s)",
                        [(note_id, i, c.heading_path, c.content, str(v))
                         for i, (c, v) in enumerate(zip(chunks, vectors, strict=True))],
                    )  # fmt: skip
                    stats.embedded += 1
                    stats.chunks += len(chunks)
                # Links and tags come from frontmatter + body, so they only change with the row.
                cur.execute("DELETE FROM note_links WHERE source_note_id = %s", (note_id,))
                cur.executemany(
                    "INSERT INTO note_links (source_note_id, raw_target, link_kind)"
                    " VALUES (%s, %s, %s)",
                    [(note_id, target, kind) for target, kind in note.links],
                )
                cur.execute("DELETE FROM note_tags WHERE note_id = %s", (note_id,))
                cur.executemany(
                    "INSERT INTO note_tags (note_id, tag) VALUES (%s, %s)",
                    [(note_id, tag) for tag in note.tags],
                )
        if stats.notes % 100 == 0:
            log.info("indexed %d notes (%d embedded)", stats.notes, stats.embedded)

    with conn.transaction():  # last: a crash before this leaves last_commit at the old commit
        cur = conn.execute("DELETE FROM notes WHERE NOT (path = ANY(%s))", (seen,))
        stats.deleted = cur.rowcount
        conn.execute(UPSERT_STATE, (commit, settings.embedding_model, settings.embedding_dim))
    log.info("full index at %s: %s", commit[:12], stats)
    return stats
