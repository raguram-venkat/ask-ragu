"""Plain-text graph reports for the CLI (Sprint 3 Task 4): one note's expansion, vault health.

Output contains note titles: it's for your terminal, never for git.
"""

from collections import defaultdict

import psycopg

from ask_ragu.graph.expand import expand
from ask_ragu.graph.hubs import EDGES
from ask_ragu.graph.resolve import aliases, key, resolver
from ask_ragu.settings import settings

# Why a note was reached, read from the earlier note's side (edge types: hubs.py).
WHY = {
    "link": "linked from {src}",
    "backlink": "links to {src}",
    "parent": "MOC of {src}",
    "child": "listed in {src}",
    "sibling": "shares MOC {via} with {src}",
    "tag": "shares #{via} with {src}",
}


def table(header: list[str], rows: list[list]) -> str:
    rows = [[str(c) for c in r] for r in rows]
    widths = [max(len(str(h)), *(len(r[i]) for r in rows)) for i, h in enumerate(header)]

    def line(cells):
        return "  ".join(c.ljust(w) for c, w in zip(cells, widths, strict=True)).rstrip()

    return "\n".join([line(header), line(["-" * w for w in widths]), *map(line, rows)])


def neighbors_report(conn: psycopg.Connection, note: str) -> str:
    """Expand from one note, given as you'd link it (name, path or alias), and say why each
    neighbour is there."""
    notes = conn.execute("SELECT id, path, frontmatter FROM notes").fetchall()
    seed = resolver(notes)(note)
    if seed is None:
        return f"No note matches [[{note}]]."
    title = dict(conn.execute("SELECT id, title FROM notes").fetchall())
    path = {i: p for i, p, _ in notes}
    reached = expand(conn, [seed])
    rows = [
        [
            r.hop,
            title[r.note_id] + ("  [moc]" if r.is_moc else ""),
            WHY[r.edge_type].format(src=title[r.from_note], via=title.get(r.via_note, r.via_tag)),
            "" if r.weight == 1 else f"{r.weight:.2f}",
        ]
        for r in reached
    ]
    mocs = sum(r.is_moc for r in reached)
    head = (
        f"Expansion from {path[seed]}: {len(reached) - mocs} notes + {mocs} MOCs"
        f" (hops {settings.graph_max_hops}, fan-out {settings.graph_fanout_cap},"
        f" total {settings.graph_total_cap})"
    )
    return head + ("\n\n" + table(["hop", "note", "why", "weight"], rows) if rows else "")


def health_report(conn: psycopg.Connection, top: int = 10) -> str:
    notes = conn.execute("SELECT id, path, title, frontmatter FROM notes").fetchall()
    sections = []

    dangling = conn.execute(
        "SELECT n.path, l.raw_target FROM note_links l JOIN notes n ON n.id = l.source_note_id"
        " WHERE l.target_note_id IS NULL ORDER BY 1, 2"
    ).fetchall()
    sections.append((f"Dangling links: {len(dangling)}", ["in note", "links to"], dangling))

    orphans = conn.execute(
        "SELECT path FROM notes n WHERE NOT EXISTS (SELECT 1 FROM note_links l"
        " WHERE n.id IN (l.source_note_id, l.target_note_id)"
        " AND l.target_note_id <> l.source_note_id) ORDER BY 1"
    ).fetchall()
    sections.append((f"Orphans (no links in or out): {len(orphans)}", ["note"], orphans))

    # Names and aliases that more than one note answers to: the resolver picks one (Task 1).
    by_name, by_alias = defaultdict(list), defaultdict(list)
    for _, path, title, frontmatter in notes:
        by_name[key(title)].append(path)
        for a in aliases(frontmatter):
            by_alias[key(a)].append(path)
    clashes = [[n, "same name", p] for n, p in by_name.items() if len(p) > 1]
    clashes += [[a, "alias of several", p] for a, p in by_alias.items() if len(p) > 1]
    clashes += [[a, "alias shadowed by a name", p] for a, p in by_alias.items() if a in by_name]
    clashes = sorted([n, kind, ", ".join(sorted(p))] for n, kind, p in clashes)
    sections.append(
        (f"Name and alias collisions: {len(clashes)}", ["name", "kind", "notes"], clashes)
    )

    mocs = conn.execute(
        f"SELECT n.path, count(*) FROM ({EDGES}) e JOIN notes n ON n.id = e.src"
        " WHERE e.edge_type = 'child' GROUP BY n.path ORDER BY 2 DESC, 1 LIMIT %(top)s",
        {"max_tag_share": settings.graph_tag_hub_max_share, "top": top},
    ).fetchall()
    sections.append((f"Biggest MOCs (top {top})", ["MOC", "members"], mocs))

    total = len(notes) or 1
    cutoff = settings.graph_tag_hub_max_share * total  # same rule as hubs.EDGES
    tags = [
        [f"#{tag}", n, f"{100 * n / total:.1f}%", "yes" if n <= cutoff else "no (too common)"]
        for tag, n in conn.execute(
            "SELECT tag, count(*) FROM note_tags GROUP BY tag ORDER BY 2 DESC, 1 LIMIT %s", (top,)
        )
    ]
    sections.append((f"Biggest tags (top {top})", ["tag", "notes", "share", "hub"], tags))

    return "\n\n".join(
        title + ("\n" + table(header, rows) if rows else "") for title, header, rows in sections
    )
