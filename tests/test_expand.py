"""Bounded expansion (Sprint 3 Task 3) on a hand-built graph.

Top (moc) <-- Hub (moc) --> S, M1..M5        S --> Hub (`## Part of`)
S --> L1 --> L2 --> S (a cycle)    X --> S    tag t on S, T1, T2
"""

import pytest

from ask_ragu.graph.expand import expand
from ask_ragu.settings import settings

MEMBERS = {f"M{i}" for i in range(1, 6)}
TAGGED = {"T1", "T2"}
NOTES = dict(S="concept", L1="concept", L2="concept", X="concept", T1="concept", T2="source")
NOTES |= dict(Hub="moc", Top="moc") | {m: "concept" for m in MEMBERS}
LINKS = [("S", "Hub"), ("Hub", "S"), ("Hub", "Top"), ("S", "L1"), ("L1", "L2"), ("L2", "S")]
LINKS += [("X", "S")] + [("Hub", m) for m in sorted(MEMBERS)]
TAGS = [("S", "t"), ("T1", "t"), ("T2", "t")]


@pytest.fixture
def run(conn, make_graph, monkeypatch):
    ids = make_graph(NOTES, LINKS, TAGS)
    names = {v: k for k, v in ids.items()}

    def run(*seeds, hops=2, fanout=10, total=30):
        """{name: (hop, from, edge_type, via)} reached from the seeds."""
        for name, value in {
            "graph_max_hops": hops,
            "graph_fanout_cap": fanout,
            "graph_total_cap": total,
            "graph_tag_hub_max_share": 0.5,
        }.items():
            monkeypatch.setattr(settings, name, value)
        return {
            names[r.note_id]: (r.hop, names[r.from_note], r.edge_type, names.get(r.via_note))
            for r in expand(conn, [ids[s] for s in seeds])
        }

    return run


def test_two_hops_shortest_first_direct_then_siblings_then_tags(run):
    got = run("S")
    hop1 = {n: v for n, v in got.items() if v[0] == 1}
    hop2 = {n: v for n, v in got.items() if v[0] == 2}
    # S has 4 direct + 5 sibling + 2 tag neighbours; fan-out 10 leaves one slot for a tag-mate.
    (tag1,) = hop1.keys() & TAGGED
    (tag2,) = TAGGED - {tag1}
    assert hop1 == {
        "L1": (1, "S", "link", None),
        "L2": (1, "S", "backlink", None),  # the cycle: hop 1 by backlink, never hop 2 via L1
        "X": (1, "S", "backlink", None),
        "Hub": (1, "S", "parent", None),
        **{m: (1, "S", "sibling", "Hub") for m in MEMBERS},  # through the MOC in one hop
        tag1: (1, "S", "tag", None),
    }
    assert hop2 == {
        "Top": (2, "Hub", "link", None),  # MOC -> MOC is an ordinary hop, not passed through
        tag2: (2, tag1, "tag", None),  # cut at hop 1, reached at hop 2
    }
    assert "S" not in got  # seeds aren't returned


def test_moc_seed_fan_out_is_capped(run):
    got = run("Hub", fanout=3, hops=1)
    assert len(got) == 3  # of Hub's 7 neighbours (S, M1..M5, Top)


def test_total_cap_counts_notes_not_mocs(run):
    got = run("S", total=4)
    # Best first: L1, L2, X (direct), Hub (direct but a MOC: free), then one sibling.
    assert got.keys() - MEMBERS == {"L1", "L2", "X", "Hub"}
    assert len(got.keys() & MEMBERS) == 1
    assert all(v[0] == 1 for v in got.values())  # the budget ran out at hop 1


def test_one_hop_and_several_seeds(run):
    got = run("S", "L1", hops=1)
    assert "L1" not in got  # a seed is never a result, even when another seed links to it
    # L2 is a backlink of S and a link of L1, equally good: either is fine, one row only.
    assert got["L2"] in {(1, "S", "backlink", None), (1, "L1", "link", None)}
    assert all(v[0] == 1 for v in got.values())


def test_ties_are_shuffled_per_seed_set_but_repeatable(run):
    # Hub has 7 equally good neighbours for 3 slots: which 3 depends on the seed set only.
    first = run("Hub", fanout=3, hops=1)
    assert run("Hub", fanout=3, hops=1) == first
    assert run("S", "L1", hops=1) == run("L1", "S", hops=1)  # seed order doesn't matter
