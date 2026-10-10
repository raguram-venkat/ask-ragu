"""Bounded graph expansion from seed notes (SPEC §9 step 4, D-007, ADR-0015).

One query per hop over hubs.EDGES. Between hops, Python keeps the shortest hop per note,
removes notes already reached from the next hop's candidates, and applies the total cap.
A recursive CTE can do none of that in its recursive term (ADR-0015).

Order of preference, used for the per-note fan-out cap and the total cap: direct edges
(link, backlink, parent, child), then siblings through a MOC, then tag-mates (the fallback,
ADR-0010); within a class, higher weight first. Remaining ties (e.g. 5 slots for 40 equally
weighted MOC siblings) are a shuffle seeded by the seed set: a different question's seeds pick
different siblings, the same seeds always pick the same ones, so eval runs are repeatable.
"""

import hashlib
from dataclasses import dataclass
from uuid import UUID

import psycopg

from ask_ragu.graph.hubs import EDGES
from ask_ragu.settings import settings

CLASS = "CASE edge_type WHEN 'sibling' THEN 1 WHEN 'tag' THEN 2 ELSE 0 END"

# One hop: best path per (src, dst) pair, then at most fanout per src, then best path per dst.
HOP = f"""
SELECT DISTINCT ON (dst) dst, src, edge_type, via_note, via_tag, weight, is_moc
FROM (
    SELECT *, row_number() OVER (
        PARTITION BY src ORDER BY cls, weight DESC, md5(dst::text || %(salt)s)
    ) AS rank
    FROM (
        SELECT DISTINCT ON (e.src, e.dst) e.*, {CLASS} AS cls, n.note_type = 'moc' AS is_moc
        FROM ({EDGES}) e JOIN notes n ON n.id = e.dst
        WHERE e.src = ANY(%(frontier)s) AND NOT e.dst = ANY(%(seen)s)
        ORDER BY e.src, e.dst, cls, weight DESC
    ) pairs
) ranked
WHERE rank <= %(fanout)s
ORDER BY dst, cls, weight DESC, md5(src::text || %(salt)s)
"""

PREFERENCE = {"sibling": 1, "tag": 2}  # same order as CLASS; anything else is 0


# ponytail: a seeded shuffle, not relevance; ranking ties by the question is Sprint 4 (BACKLOG).
def shuffled(note_id: UUID, salt: str) -> str:
    """Tie-break key, the same as md5(id::text || salt) in HOP."""
    return hashlib.md5(f"{note_id}{salt}".encode()).hexdigest()


@dataclass(frozen=True)
class Reached:
    note_id: UUID
    hop: int
    from_note: UUID  # the seed or earlier-hop note it was reached from
    edge_type: str  # link, backlink, parent, child, sibling, tag (hubs.py)
    via_note: UUID | None  # the MOC passed through (sibling)
    via_tag: str | None  # the shared tag (tag)
    weight: float
    is_moc: bool  # passed through, never context: doesn't count toward the total cap


def expand(conn: psycopg.Connection, seeds: list[UUID]) -> list[Reached]:
    """Notes up to GRAPH_MAX_HOPS from the seeds, best first; seeds themselves not included."""
    seen, frontier, reached = set(seeds), list(seeds), []
    salt = ",".join(sorted(map(str, seeds)))  # seed order doesn't matter
    budget = settings.graph_total_cap
    for hop in range(1, settings.graph_max_hops + 1):
        if not frontier or budget == 0:
            break
        rows = conn.execute(
            HOP,
            {
                "frontier": frontier,
                "seen": list(seen),
                "fanout": settings.graph_fanout_cap,
                "max_tag_share": settings.graph_tag_hub_max_share,
                "salt": salt,
            },
        ).fetchall()
        step = sorted(
            (Reached(dst, hop, *rest) for dst, *rest in rows),
            key=lambda r: (PREFERENCE.get(r.edge_type, 0), -r.weight, shuffled(r.note_id, salt)),
        )
        frontier = []
        for r in step:
            if not r.is_moc:
                if budget == 0:
                    continue
                budget -= 1
            reached.append(r)
            frontier.append(r.note_id)
        seen.update(frontier)
    return reached
