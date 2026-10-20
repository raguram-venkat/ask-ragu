"""Context assembly (Task 4): expand seeds, best-chunk, score, dedupe, budget, provenance."""

import pytest

from ask_ragu import db
from ask_ragu.retrieval.assemble import assemble_context
from ask_ragu.settings import settings


def vec(x: float, y: float) -> list[float]:
    """A 384-d vector in the plane of the first two axes."""
    return [x, y] + [0.0] * 382


@pytest.fixture
def vault(conn, monkeypatch):
    """Small vault: Q (concept, seed), A (concept, linked), Hub (moc, linked).

    Q has two chunks; A has two chunks; Hub (a MOC) has a chunk that must be excluded.
    Links: Q→Hub and A→Hub (both parent edges to the MOC), so expanding from Q reaches
    A as a sibling through Hub at hop 1, and Hub itself as parent (MOC, traversed through).
    """
    monkeypatch.setattr(settings, "retrieval_relevance_floor", -1.0)
    monkeypatch.setattr(settings, "retrieval_hop_decay_hop1", 0.8)
    monkeypatch.setattr(settings, "retrieval_hop_decay_hop2", 0.6)
    monkeypatch.setattr(settings, "retrieval_rrf_k", 60)
    monkeypatch.setattr(settings, "retrieval_expanded_budget_share", 0.4)
    monkeypatch.setattr(settings, "retrieval_chars_per_token", 4)
    db.migrate(conn)

    notes = {}
    for name, kind in [("Q", "concept"), ("A", "concept"), ("Hub", "moc")]:
        (nid,) = conn.execute(
            "INSERT INTO notes (path, title, note_type, content_hash, meta_hash)"
            " VALUES (%s, %s, %s, '', '') RETURNING id",
            (f"{name}.md", name, kind),
        ).fetchone()
        notes[name] = nid

    conn.execute(
        "INSERT INTO note_links VALUES (%s, %s, %s, 'link')",
        (notes["Q"], "Hub", notes["Hub"]),
    )
    conn.execute(
        "INSERT INTO note_links VALUES (%s, %s, %s, 'link')",
        (notes["A"], "Hub", notes["Hub"]),
    )

    def add_chunk(note_name, order, heading, content, embedding):
        cid = conn.execute(
            "INSERT INTO chunks (note_id, chunk_order, heading_path, content, embedding)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (notes[note_name], order, heading, content, str(embedding)),
        ).fetchone()[0]
        return cid

    cids = {
        "q_good": add_chunk("Q", 0, "Q > Good", "short content here", vec(1, 0)),
        "q_bad": add_chunk("Q", 1, "Q > Bad", "other content there", vec(0, 1)),
        "a_good": add_chunk("A", 0, "A > Good", "linked content here", vec(0.95, 0.3)),
        "a_bad": add_chunk("A", 1, "A > Bad", "unrelated content there", vec(0, 1)),
        "hub": add_chunk("Hub", 0, "Hub > Section", "hub content here", vec(0.5, 0.5)),
    }
    return {"conn": conn, "notes": notes, "cids": cids}


QUERY = vec(1, 0)  # closest to q_good (cos=1.0) and a_good (cos≈0.95)


def test_seeds_and_expanded_both_present(vault):
    conn = vault["conn"]
    nid = vault["notes"]
    cids = vault["cids"]
    seeds = [(cids["q_good"], nid["Q"], 0.03)]  # seed: Q's good chunk

    ctx = assemble_context(conn, seeds, QUERY, token_budget=500)

    chunk_ids = [c.chunk_id for c in ctx]
    assert cids["q_good"] in chunk_ids  # seed chunk included
    assert cids["a_good"] in chunk_ids  # expanded note's best chunk included

    by_id = {c.chunk_id: c for c in ctx}
    assert by_id[cids["q_good"]].source == "seed"
    assert by_id[cids["q_good"]].provenance == "direct"
    assert by_id[cids["a_good"]].source == "expanded"
    assert "Q" in by_id[cids["a_good"]].provenance  # reached from seed Q


def test_moc_chunks_excluded(vault):
    conn = vault["conn"]
    nid = vault["notes"]
    cids = vault["cids"]
    seeds = [(cids["q_good"], nid["Q"], 0.03)]

    ctx = assemble_context(conn, seeds, QUERY, token_budget=500)
    assert cids["hub"] not in [c.chunk_id for c in ctx]  # MOC chunk never context


def test_dedup_seed_and_expanded(vault):
    """A chunk that's both a seed and an expanded best-match stays seed (labeled direct)."""
    conn = vault["conn"]
    nid = vault["notes"]
    cids = vault["cids"]
    # Seed: Q's good chunk. Its RRF score should win over the expanded score.
    seeds = [(cids["q_good"], nid["Q"], 0.03)]
    ctx = assemble_context(conn, seeds, QUERY, token_budget=500)
    by_id = {c.chunk_id: c for c in ctx}
    # q_good appears only once, as seed
    assert cids["q_good"] in by_id
    assert by_id[cids["q_good"]].source == "seed"


def test_token_budget_respected(vault):
    conn = vault["conn"]
    nid = vault["notes"]
    cids = vault["cids"]
    seeds = [(cids["q_good"], nid["Q"], 0.03)]

    # Budget of 5 chars ≈ 1 token — seeds pack first until budget fills.
    ctx = assemble_context(conn, seeds, QUERY, token_budget=10)
    total_chars = sum(len(c.content) for c in ctx)
    assert total_chars / 4 <= 10  # tokens ≈ chars/4, stays within budget


def test_expanded_capped_at_40_percent(vault):
    """Expanded (non-seed) chunks can't consume more than 40% of the token budget."""
    conn = vault["conn"]
    nid = vault["notes"]
    cids = vault["cids"]
    seeds = [(cids["q_good"], nid["Q"], 0.03)]

    budget = 500
    ctx = assemble_context(conn, seeds, QUERY, token_budget=budget)

    expanded_chunks = [c for c in ctx if c.source == "expanded"]
    expanded_tokens = sum(len(c.content) for c in expanded_chunks) / 4
    assert expanded_tokens <= int(budget * 0.4)


def test_empty_seeds_returns_empty(vault):
    assert assemble_context(vault["conn"], [], QUERY, token_budget=500) == []


def test_expanded_score_formula(vault, monkeypatch):
    """Expanded score = cosine × hop_decay × note_type_prior."""
    conn = vault["conn"]
    nid = vault["notes"]
    cids = vault["cids"]
    seeds = [(cids["q_good"], nid["Q"], 0.03)]

    ctx = assemble_context(conn, seeds, QUERY, token_budget=500)
    expanded = [c for c in ctx if c.source == "expanded"]
    # a_good: cos ≈ 0.95 (vec(0.95,0.3) vs vec(1,0)), hop 1, concept prior 1.0
    # score ≈ 0.95 × 0.8 × 1.0 = ~0.76
    assert len(expanded) == 1
    assert expanded[0].score == pytest.approx(0.76, abs=0.01)
