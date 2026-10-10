"""Wikilink resolution (SPEC §7, §8 step 3): note_links.raw_target -> target_note_id.

Runs over every link after each sync, not just the changed notes': a new note can fix an old
dangling link, and a rename outside Obsidian can break links in notes that didn't change.
A self-link resolves to its own note; traversal never steps to a note it has already seen,
so it adds no edge.
"""

import logging
import unicodedata
from collections import defaultdict

import psycopg

log = logging.getLogger(__name__)


def key(name: str) -> str:
    """Case-insensitive like Obsidian; NFC so a macOS (NFD) filename matches typed text."""
    return unicodedata.normalize("NFC", name.strip()).lower().removesuffix(".md")


def aliases(frontmatter: dict) -> list[str]:
    value = frontmatter.get("aliases")  # list, or a single string
    return [str(a) for a in (value if isinstance(value, list) else [value]) if a]


def resolver(notes: list[tuple]):
    """notes: (id, path, frontmatter) rows. Returns resolve(raw_target) -> note id or None.

    Order: path or name match ([[Note]], [[Folder/Note]], [[Note.md]]), then frontmatter alias.
    Several matches: the one nearest the vault root, then alphabetical path (deterministic),
    plus a warning.
    """
    by_name, by_alias = defaultdict(list), defaultdict(list)
    for note_id, path, frontmatter in notes:
        k = key(path)
        by_name[k.rsplit("/", 1)[-1]].append((k, path, note_id))
        for alias in aliases(frontmatter):
            by_alias[key(alias)].append((path, note_id))

    def resolve(raw: str):
        k = key(raw)
        name = k.rsplit("/", 1)[-1]
        hits = [(p, i) for pk, p, i in by_name[name] if pk == k or pk.endswith("/" + k)]
        hits = sorted(hits or by_alias[k], key=lambda h: (h[0].count("/"), h[0]))
        if len(hits) > 1:
            log.warning("[[%s]] matches %d notes; using %s", raw, len(hits), hits[0][0])
        return hits[0][1] if hits else None

    return resolve


def resolve_links(conn: psycopg.Connection) -> tuple[int, int]:
    """Point every link at its note, or NULL (dangling). Returns (resolved, dangling)."""
    resolve = resolver(conn.execute("SELECT id, path, frontmatter FROM notes").fetchall())
    raws = [raw for (raw,) in conn.execute("SELECT DISTINCT raw_target FROM note_links")]
    conn.execute(
        "UPDATE note_links l SET target_note_id = r.target"
        " FROM unnest(%s::text[], %s::uuid[]) AS r(raw, target)"
        " WHERE l.raw_target = r.raw AND l.target_note_id IS DISTINCT FROM r.target",
        (raws, [resolve(raw) for raw in raws]),
    )
    resolved, dangling = conn.execute(
        "SELECT count(target_note_id), count(*) - count(target_note_id) FROM note_links"
    ).fetchone()
    log.info("links: %d resolved, %d dangling", resolved, dangling)
    return resolved, dangling
