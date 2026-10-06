"""Full index (SPEC §8): every note at one vault commit -> notes, chunks, note_links, note_tags.

Notes are read from git objects at that commit (never the working tree), so the result depends
only on the commit + settings — the same thing incremental sync (sync.py) reaches by diffs.
Idempotent: a second run over the same commit writes nothing and embeds nothing.
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
from ask_ragu.index.parse import ParsedNote, is_indexable, parse_note
from ask_ragu.settings import settings

log = logging.getLogger(__name__)

# Returns the id only if the row was inserted or actually changed, so unchanged notes are skipped.
UPSERT_NOTE = """
INSERT INTO notes (path, title, note_type, frontmatter, content_hash, meta_hash)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (path) DO UPDATE SET
    title = EXCLUDED.title, note_type = EXCLUDED.note_type, frontmatter = EXCLUDED.frontmatter,
    content_hash = EXCLUDED.content_hash, meta_hash = EXCLUDED.meta_hash, updated_at = now()
WHERE (notes.title, notes.note_type, notes.frontmatter, notes.content_hash, notes.meta_hash)
    IS DISTINCT FROM (EXCLUDED.title, EXCLUDED.note_type, EXCLUDED.frontmatter,
                      EXCLUDED.content_hash, EXCLUDED.meta_hash)
RETURNING id
"""

UPSERT_STATE = """
INSERT INTO index_state
    (last_commit, settings_hash, embedding_model, embedding_dim, embed_version, parse_version)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (singleton) DO UPDATE SET
    last_commit = EXCLUDED.last_commit, settings_hash = EXCLUDED.settings_hash,
    embedding_model = EXCLUDED.embedding_model, embedding_dim = EXCLUDED.embedding_dim,
    embed_version = EXCLUDED.embed_version, parse_version = EXCLUDED.parse_version,
    updated_at = now()
"""


@dataclass
class Stats:
    mode: str = "full"  # full | incremental | noop
    notes: int = 0  # notes looked at (full: all indexable; incremental: changed ones)
    written: int = 0  # note rows inserted or changed
    embedded: int = 0  # notes re-chunked and re-embedded
    chunks: int = 0  # chunks embedded
    renamed: int = 0  # path updated in place, id kept (incremental only)
    deleted: int = 0  # notes removed because their file is gone


def git_cmd(vault: Path, *args: str) -> list[str]:
    # safe.directory: the mounted vault is owned by a different user than the container's.
    return ["git", "-c", f"safe.directory={vault}", "-C", str(vault), *args]


def git(vault: Path, *args: str) -> str:
    return subprocess.run(git_cmd(vault, *args), check=True, capture_output=True, text=True).stdout


def read_blobs(vault: Path, commit: str, paths: list[str]) -> dict[str, str]:
    """File contents at `commit`, all through one `git cat-file --batch` process."""
    if not paths:
        return {}
    request = "".join(f"{commit}:{p}\n" for p in paths).encode()
    out = subprocess.run(
        git_cmd(vault, "cat-file", "--batch"), input=request, check=True, capture_output=True
    ).stdout
    blobs, pos = {}, 0
    for path in paths:  # each answer: "<sha> blob <size>\n<content>\n", in request order
        header_end = out.index(b"\n", pos)
        size = int(out[pos:header_end].split()[2])
        blobs[path] = out[header_end + 1 : header_end + 1 + size].decode("utf-8", "replace")
        pos = header_end + 1 + size + 1
    return blobs


# Code versions (ADR-0017). Bump when a code change alters what gets written for the same commit +
# settings; tests/test_index_versions.py fails until you do. Never reuse or decrease a number.
EMBED_VERSION = 1  # chunker, passage_text: anything that changes chunks or the embedded text
PARSE_VERSION = 1  # parser: cleaned body, links, tags, note_type, frontmatter

# The settings that shape the index, defined once (D-010). Anything in .env that changes what
# gets written for the same commit belongs in one of the two groups; pure runtime knobs
# (EMBEDDING_BATCH_SIZE, EMBEDDING_CACHE_DIR, EMBEDDING_QUERY_PREFIX, webhook/vault location
# settings) don't. Sets and dicts are sorted so the hash doesn't depend on .env ordering.


def embed_settings() -> list:
    """EMBED group: what chunks and vectors depend on. Part of every note's content_hash."""
    s = settings
    # Changing this list's shape changes every content_hash -> full re-embed (once).
    # EMBEDDING_DIM is not here: it's fixed by the model, and a wrong value fails loudly at load.
    return [EMBED_VERSION, s.chunk_max_chars, s.chunk_merge_below_chars, s.chunk_overlap_chars,
            s.stub_min_chars, s.embedding_model, s.embedding_model_file, s.embedding_pooling,
            sorted(s.chunk_metadata_headings)]  # fmt: skip


def parse_settings() -> list:
    """PARSE group: what changes rows but not vectors (note_type, which files are notes).

    VAULT_STRIPPED_FENCES also changes the cleaned body, so it reaches content_hash that way.
    """
    s = settings
    return [PARSE_VERSION, sorted(s.vault_folder_types.items()), s.vault_default_note_type,
            sorted(s.vault_excluded_dirs), sorted(s.vault_stripped_fences)]  # fmt: skip


def _sha(value) -> str:
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def settings_hash() -> str:
    """Stored in index_state; a different value at sync time forces a full index."""
    return _sha([embed_settings(), parse_settings()])


def content_hash(note: ParsedNote) -> str:
    """Title + body + EMBED group; a change to any of it re-embeds the note."""
    return _sha([note.title, note.body, *embed_settings()])


def meta_hash(note: ParsedNote) -> str:
    """Links + tags as extracted; a change rewrites them without re-embedding."""
    return _sha([note.links, note.tags])


def index_note(conn: psycopg.Connection, note: ParsedNote, old_hash: str | None, stats: Stats):
    """Upsert one note; re-chunk and re-embed only if its content_hash changed."""
    h = content_hash(note)
    chunks = None  # None = keep the existing chunks
    if old_hash != h:
        chunks = chunk_note(note.title, note.body)
        texts = [passage_text(c.heading_path, c.content) for c in chunks]
        vectors = embed_passages(texts) if texts else []  # outside the transaction: it's slow

    with conn.transaction():
        row = conn.execute(
            UPSERT_NOTE,
            (note.path, note.title, note.note_type, Jsonb(note.frontmatter), h, meta_hash(note)),
        ).fetchone()
        if row is None:  # nothing about this note changed
            return
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


def index_paths(conn: psycopg.Connection, vault: Path, commit: str, paths: list[str], stats: Stats):
    """Parse and index these paths as they are at `commit` (excluded paths are skipped)."""
    paths = [p for p in paths if is_indexable(p)]
    old_hashes = dict(conn.execute("SELECT path, content_hash FROM notes").fetchall())
    for path, text in read_blobs(vault, commit, paths).items():
        stats.notes += 1
        index_note(conn, parse_note(path, text), old_hashes.get(path), stats)
        if stats.notes % 100 == 0:
            log.info("indexed %d notes (%d embedded)", stats.notes, stats.embedded)


def record_state(conn: psycopg.Connection, commit: str) -> None:
    # Model, dim and versions are informational (status, logs); settings_hash is what sync compares.
    conn.execute(
        UPSERT_STATE,
        (commit, settings_hash(), settings.embedding_model, settings.embedding_dim,
         EMBED_VERSION, PARSE_VERSION),
    )  # fmt: skip


def index_full(conn: psycopg.Connection, vault: Path, commit: str = "HEAD") -> Stats:
    commit = git(vault, "rev-parse", f"{commit}^{{commit}}").strip()
    # -z: NUL-separated and unquoted; without it git escapes non-ASCII paths ("Caf\303\251.md").
    tree = git(vault, "ls-tree", "-r", "-z", "--name-only", commit).split("\0")
    paths = [p for p in tree if p and is_indexable(p)]
    stats = Stats()
    index_paths(conn, vault, commit, paths, stats)

    with conn.transaction():  # last: a crash before this leaves last_commit at the old commit
        stats.deleted = conn.execute(
            "DELETE FROM notes WHERE NOT (path = ANY(%s))", (paths,)
        ).rowcount
        record_state(conn, commit)
    log.info("full index at %s: %s", commit[:12], stats)
    return stats
