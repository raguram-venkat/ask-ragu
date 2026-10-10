"""Graph CLI reports (Sprint 3 Task 4) on a hand-built graph.

Hub (moc) --> A, B    A --> C    A --> "Gone" (dangling)    Lone: no links    tags: x on A, B, C
"""

import pytest
from psycopg.types.json import Jsonb

from ask_ragu.graph.report import health_report, neighbors_report
from ask_ragu.settings import settings

NOTES = dict(A="concept", B="concept", C="concept", Lone="concept", Hub="moc")
LINKS = [("Hub", "A"), ("Hub", "B"), ("A", "C")]
TAGS = [("A", "x"), ("B", "x"), ("C", "x")]


@pytest.fixture
def ids(conn, make_graph, monkeypatch):
    monkeypatch.setattr(settings, "graph_tag_hub_max_share", 0.4)  # x: 3 of 6 notes = too common
    for name, value in {"graph_max_hops": 2, "graph_fanout_cap": 10, "graph_total_cap": 30}.items():
        monkeypatch.setattr(settings, name, value)
    ids = make_graph(NOTES, LINKS, TAGS)
    conn.execute("INSERT INTO note_links VALUES (%s, 'Gone', NULL, 'link')", (ids["A"],))
    # A second "A" in a subfolder; aliases claimed twice and one shadowed by a real name.
    conn.execute(
        "INSERT INTO notes (path, title, note_type, frontmatter, content_hash)"
        " VALUES ('Sub/A.md', 'A', 'concept', %s, '')",
        (Jsonb({"aliases": ["Both", "lone"]}),),
    )
    conn.execute(
        "UPDATE notes SET frontmatter = %s WHERE id = %s", (Jsonb({"aliases": "both"}), ids["B"])
    )
    return ids


def test_health_lists_dangling_orphans_collisions_and_hubs(conn, ids):
    out = health_report(conn)
    assert "Dangling links: 1\n" in out and "A.md     Gone" in out
    assert "Orphans (no links in or out): 2" in out  # Lone and Sub/A.md
    assert "Name and alias collisions: 3" in out
    assert "a     same name                 A.md, Sub/A.md" in out
    assert "both  alias of several          B.md, Sub/A.md" in out
    assert "lone  alias shadowed by a name  Sub/A.md" in out
    assert "Hub.md  2" in out  # members
    assert "#x   3      50.0%  no (too common)" in out


def test_neighbors_says_why(conn, ids):
    out = neighbors_report(conn, "a")  # resolved like a link: case-insensitive, root note wins
    assert out.startswith("Expansion from A.md: ")
    assert "Hub  [moc]" in out and "MOC of A" in out
    assert "shares MOC Hub with A" in out  # B
    assert "linked from A" in out  # C
    assert neighbors_report(conn, "Nope") == "No note matches [[Nope]]."
