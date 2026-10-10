"""One-hop edges with MOC and tag hubs (Sprint 3 Task 2, ADR-0010) on a hand-built graph.

Parent (moc) <-- Hub (moc) --> A, B        A --> Hub (`## Part of`), A --> C, A --> A (self)
tags: x on A, B, D · y on C · common on all 6 notes (over the cutoff)
"""

import pytest

from ask_ragu import db
from ask_ragu.graph.hubs import neighbours
from ask_ragu.settings import settings

NOTES = dict(A="concept", B="concept", C="concept", D="source", Hub="moc", Parent="moc")
LINKS = [("Hub", "A"), ("Hub", "B"), ("Hub", "Parent"), ("A", "Hub"), ("A", "C"), ("A", "A")]
TAGS = [("A", "x"), ("B", "x"), ("D", "x"), ("C", "y")] + [(n, "common") for n in NOTES]


@pytest.fixture
def graph(conn, monkeypatch):
    monkeypatch.setattr(settings, "graph_tag_hub_max_share", 0.6)  # x: 3/6 kept, common: 6/6 not
    db.migrate(conn)
    ids = {
        name: conn.execute(
            "INSERT INTO notes (path, title, note_type, content_hash, meta_hash)"
            " VALUES (%s, %s, %s, '', '') RETURNING id",
            (f"{name}.md", name, kind),
        ).fetchone()[0]
        for name, kind in NOTES.items()
    }
    for src, dst in LINKS:
        conn.execute(
            "INSERT INTO note_links VALUES (%s, %s, %s, 'link')", (ids[src], dst, ids[dst])
        )
    conn.execute("INSERT INTO note_links VALUES (%s, 'C', %s, 'embed')", (ids["A"], ids["C"]))
    conn.execute("INSERT INTO note_links VALUES (%s, 'Gone', NULL, 'link')", (ids["A"],))
    for name, tag in TAGS:
        conn.execute("INSERT INTO note_tags VALUES (%s, %s)", (ids[name], tag))
    names = {v: k for k, v in ids.items()}

    def edges(name):
        """{(dst, edge_type, via): weight} out of one note, by name."""
        return {
            (names[dst], kind, names.get(via_note) or via_tag): round(w, 3)
            for _, dst, kind, via_note, via_tag, w in neighbours(conn, [ids[name]])
        }

    return edges


def test_concept_reaches_links_its_moc_siblings_and_tag_mates(graph):
    # ln(6/2)/ln(6) for Hub's 2 members; ln(6/3)/ln(6) for tag x's 3 notes
    assert graph("A") == {
        ("C", "link", None): 1.0,  # [[C]] + ![[C]]: one edge; the self-link and dangling: none
        ("Hub", "parent", None): 1.0,  # A links Hub, and Hub lists A: still one membership
        ("B", "sibling", "Hub"): 0.613,  # through the MOC in one hop
        ("B", "tag", "x"): 0.387,  # the same note by another path: both kept
        ("D", "tag", "x"): 0.387,
    }  # not Parent (MOC -> MOC is a real hop), not tag "common" (over the cutoff)


def test_moc_reaches_members_and_other_mocs_but_no_siblings(graph):
    assert graph("Hub") == {
        ("A", "child", None): 1.0,
        ("B", "child", None): 1.0,  # B never links back: listing it is membership enough
        ("Parent", "link", None): 1.0,
    }
    assert graph("Parent") == {("Hub", "backlink", None): 1.0}


def test_backlinks_and_lonely_tags(graph):
    assert graph("C") == {("A", "backlink", None): 1.0}  # tag y is on C alone: no tag edge
