"""Benchmark for ADR-0015: per-hop queries (graph/expand.py) vs one recursive CTE.

    uv run python scripts/bench_expansion.py [DATABASE_URL]

DATABASE_URL defaults to TEST_DATABASE_URL in .env: on the laptop that's the compose Postgres,
whose default schema holds the real index. Reads only; prints aggregate numbers, never titles.
Caps and depth come from .env (GRAPH_*), like the app.
"""

import random
import statistics
import sys
import time

import psycopg
from dotenv import dotenv_values

from ask_ragu.graph.expand import CLASS, HOP, PREFERENCE, expand
from ask_ragu.graph.hubs import EDGES
from ask_ragu.settings import settings

# (a) One recursive CTE. Postgres allows LIMIT only inside a LATERAL subquery here, per walked
# row: no ranking across the frontier, no "already reached" set, so a note reached by k paths is
# expanded k times and hop-2 slots can go to notes already reached at hop 1. Pruned afterwards.
RECURSIVE = f"""
WITH RECURSIVE e AS (
    SELECT DISTINCT ON (src, dst) *, {CLASS} AS cls FROM ({EDGES}) x
    ORDER BY src, dst, cls, weight DESC
),
walk(note_id, hop, src, edge_type, via_note, via_tag, weight, cls) AS (
    SELECT id, 0, NULL::uuid, NULL, NULL::uuid, NULL, 1.0::float, 0
    FROM unnest(%(seeds)s::uuid[]) AS id
  UNION ALL
    SELECT x.dst, w.hop + 1, x.src, x.edge_type, x.via_note, x.via_tag, x.weight, x.cls
    FROM walk w CROSS JOIN LATERAL (
        SELECT * FROM e WHERE e.src = w.note_id AND NOT e.dst = ANY(%(seeds)s)
        ORDER BY cls, weight DESC, dst LIMIT %(fanout)s
    ) x
    WHERE w.hop < %(max_hops)s
)
SELECT DISTINCT ON (note_id) note_id, hop, edge_type, weight, n.note_type = 'moc'
FROM walk JOIN notes n ON n.id = note_id
WHERE hop > 0
ORDER BY note_id, hop, cls, weight DESC
"""


def recursive(conn, seeds):
    rows = conn.execute(
        RECURSIVE,
        {
            "seeds": seeds,
            "fanout": settings.graph_fanout_cap,
            "max_hops": settings.graph_max_hops,
            "max_tag_share": settings.graph_tag_hub_max_share,
        },
    ).fetchall()
    # Same total cap as expand(): best first, MOCs free.
    rows.sort(key=lambda r: (r[1], PREFERENCE.get(r[2], 0), -r[3], str(r[0])))
    kept, budget = [], settings.graph_total_cap
    for note_id, _, _, _, is_moc in rows:
        if not is_moc:
            if budget == 0:
                continue
            budget -= 1
        kept.append(note_id)
    return kept


def per_hop(conn, seeds):
    return [r.note_id for r in expand(conn, seeds)]


def ms(fn, conn, seeds):
    start = time.perf_counter()
    out = fn(conn, seeds)
    return (time.perf_counter() - start) * 1000, set(out)


def pct(xs, p):
    return sorted(xs)[min(len(xs) - 1, int(len(xs) * p))]


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else dotenv_values(".env")["TEST_DATABASE_URL"]
    conn = psycopg.connect(url, autocommit=True)
    ids = [r[0] for r in conn.execute("SELECT id FROM notes")]
    mocs = [r[0] for r in conn.execute("SELECT id FROM notes WHERE note_type = 'moc'")]
    print(
        f"{len(ids)} notes; hops {settings.graph_max_hops}, fan-out {settings.graph_fanout_cap},"
        f" total {settings.graph_total_cap}"
    )
    cases = {
        "1 seed": lambda: random.sample(ids, 1),
        "8 seeds": lambda: random.sample(ids, 8),
        "3 MOC seeds": lambda: random.sample(mocs, 3),
    }
    for label, pick in cases.items():
        random.seed(1)
        seed_sets = [pick() for _ in range(200)]
        for fn in (per_hop, recursive):  # warm-up: psycopg prepares after 5 runs
            for seeds in seed_sets[:10]:
                fn(conn, seeds)
        times = {fn.__name__: [] for fn in (per_hop, recursive)}
        overlap, sizes = [], []
        for seeds in seed_sets:
            t_a, a = ms(per_hop, conn, seeds)
            t_b, b = ms(recursive, conn, seeds)
            times["per_hop"].append(t_a)
            times["recursive"].append(t_b)
            overlap.append(len(a & b) / len(a | b) if a | b else 1.0)
            sizes.append(len(a))
        print(f"\n{label} ({len(seed_sets)} random sets), notes returned p50 {pct(sizes, 0.5)}")
        for name, ts in times.items():
            print(f"  {name:9}  p50 {pct(ts, 0.5):5.1f} ms   p95 {pct(ts, 0.95):5.1f} ms")
        print(f"  same notes (Jaccard) mean {statistics.mean(overlap):.2f}")

    random.seed(1)
    seeds = random.sample(ids, 8)
    print("\nEXPLAIN ANALYZE, 8 seeds:")
    hop1 = {
        "frontier": seeds,
        "seen": seeds,
        "fanout": settings.graph_fanout_cap,
        "max_tag_share": settings.graph_tag_hub_max_share,
    }
    for name, sql, params in [
        ("per_hop (hop 1 only)", HOP, hop1),
        (
            "recursive",
            RECURSIVE,
            {
                "seeds": seeds,
                "fanout": settings.graph_fanout_cap,
                "max_hops": settings.graph_max_hops,
                "max_tag_share": settings.graph_tag_hub_max_share,
            },
        ),
    ]:
        plan = [r[0] for r in conn.execute(f"EXPLAIN ANALYZE {sql}", params)]
        print(f"  {name}: " + ", ".join(line for line in plan if line.endswith(" ms")))


if __name__ == "__main__":
    main()
