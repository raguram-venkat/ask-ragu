"""One-hop graph edges, MOC and tag hubs included (Sprint 3 Task 2, ADR-0010).

Nothing here is stored: hub pairs (siblings under a MOC, notes sharing a tag) would be N² rows,
and every label can be worked out from links + note_type + tags at query time. EDGES returns
every path, not one per neighbour (a note can be a link, a sibling via two MOCs and a tag-mate
at once); choosing between them is the expansion's job (Task 3).

edge_type, from src's point of view:
  link / backlink  src links to dst / dst links to src (neither is a MOC, or both are)
  parent / child   dst is a MOC that src belongs to / src is a MOC, dst a member of it
  sibling          src and dst belong to the MOC via_note (a MOC is passed through: one hop)
  tag              src and dst share via_tag (a fallback: Task 3 fills leftover slots with it)
Membership = a link either way between a MOC and a non-MOC note (580 of 587 concept -> MOC
links sit under `## Part of`). MOC -> MOC is link/backlink, never passed through.

weight: 1 for direct edges; for hub edges ln(N / hub size) / ln(N), so a hub shared by fewer
notes says more (IDF, in (0, 1)).
"""

import psycopg

from ask_ragu.settings import settings

# Parameters: %(max_tag_share)s. Filter it as a subquery: SELECT ... FROM (EDGES) e WHERE ...
EDGES = """
WITH links AS (  -- resolved; [[X]] + ![[X]] are one edge; self-links aren't edges
    SELECT DISTINCT l.source_note_id AS a, l.target_note_id AS b,
           s.note_type = 'moc' AS a_moc, t.note_type = 'moc' AS b_moc
    FROM note_links l
    JOIN notes s ON s.id = l.source_note_id
    JOIN notes t ON t.id = l.target_note_id
    WHERE l.target_note_id <> l.source_note_id
),
member AS (  -- x belongs to MOC m
    SELECT a AS x, b AS m FROM links WHERE b_moc AND NOT a_moc
    UNION
    SELECT b, a FROM links WHERE a_moc AND NOT b_moc
),
n AS (SELECT count(*)::float AS n FROM notes),
moc_w AS (
    SELECT m, ln(n / count(*)) / ln(n) AS w FROM member, n GROUP BY m, n
),
tag_w AS (  -- tags on more than max_tag_share of notes are too generic to connect anything
    SELECT tag, ln(n / count(*)) / ln(n) AS w FROM note_tags, n
    GROUP BY tag, n HAVING count(*) <= %(max_tag_share)s * n
)
SELECT a AS src, b AS dst, 'link' AS edge_type, NULL::uuid AS via_note, NULL AS via_tag,
       1.0::float AS weight
FROM links WHERE a_moc = b_moc
UNION ALL
SELECT b, a, 'backlink', NULL, NULL, 1.0 FROM links WHERE a_moc = b_moc
UNION ALL
SELECT x, m, 'parent', NULL, NULL, 1.0 FROM member
UNION ALL
SELECT m, x, 'child', NULL, NULL, 1.0 FROM member
UNION ALL
SELECT p.x, q.x, 'sibling', p.m, NULL, w
FROM member p JOIN member q ON q.m = p.m AND q.x <> p.x JOIN moc_w ON moc_w.m = p.m
UNION ALL
SELECT p.note_id, q.note_id, 'tag', NULL, p.tag, w
FROM note_tags p JOIN note_tags q ON q.tag = p.tag AND q.note_id <> p.note_id
JOIN tag_w ON tag_w.tag = p.tag
"""


def neighbours(conn: psycopg.Connection, note_ids: list) -> list[tuple]:
    """Every one-hop edge out of these notes: (src, dst, edge_type, via_note, via_tag, weight)."""
    return conn.execute(
        f"SELECT * FROM ({EDGES}) e WHERE src = ANY(%(ids)s)",
        {"ids": note_ids, "max_tag_share": settings.graph_tag_hub_max_share},
    ).fetchall()
