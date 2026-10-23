"""Task 5: retrieval eval harness — metrics, variant selection, ablation output."""

import csv

import pytest

from ask_ragu import db
from ask_ragu.retrieval.eval_harness import (
    VARIANTS,
    EvalResult,
    evaluate,
    format_ablation,
    format_per_question,
    hit_at,
    reciprocal_rank,
    retrieve_variant,
    save_csv,
)
from ask_ragu.settings import settings

# --- Pure metric functions (no DB) ---------------------------------------------


def test_hit_at_finds_gold_in_top_k():
    assert hit_at(["a", "b", "c"], ["c"], 3) == 1
    assert hit_at(["a", "b", "c"], ["c"], 2) == 0  # c is at rank 3
    assert hit_at(["a", "b", "c"], ["d"], 3) == 0  # no gold in context


def test_hit_at_unanswerable_correct_refusal():
    assert hit_at([], [], 5) == 1  # empty context, unanswered: correct
    assert hit_at(["noise"], [], 5) == 0  # non-empty, unanswered: noise


def test_mrr_rank_of_first_gold():
    assert reciprocal_rank(["a", "b", "c"], ["c"]) == 1.0 / 3
    assert reciprocal_rank(["c", "a", "b"], ["c"]) == 1.0
    assert reciprocal_rank(["a", "b"], ["c"]) == 0.0


def test_mrr_unanswerable():
    assert reciprocal_rank([], []) == 1.0  # correct refusal
    assert reciprocal_rank(["noise"], []) == 0.0  # failed refusal


# --- Variant behavior with a small vault ----------------------------------------


def vec(x: float, y: float) -> list[float]:
    return [x, y] + [0.0] * 382


@pytest.fixture
def vault(conn, monkeypatch):
    """Q links to A (via no hub); A links to Q. Each has a chunk with a known embedding.

    Query vec(1, 0) is closest to Q's chunk (cos=1.0), A's chunk cos≈0.95, B's cos≈0.71.
    """
    monkeypatch.setattr(settings, "retrieval_relevance_floor", -1.0)  # disable floor for tests
    monkeypatch.setattr(settings, "retrieval_rrf_k", 60)
    monkeypatch.setattr(settings, "retrieval_seed_top_k", 8)
    monkeypatch.setattr(settings, "retrieval_candidates", 50)
    db.migrate(conn)

    notes = {}
    for name, kind in [("Q", "concept"), ("A", "concept"), ("B", "concept")]:
        (nid,) = conn.execute(
            "INSERT INTO notes (path, title, note_type, content_hash, meta_hash)"
            " VALUES (%s, %s, %s, '', '') RETURNING id",
            (f"{name}.md", name, kind),
        ).fetchone()
        notes[name] = nid

    # Q -> A link
    conn.execute("INSERT INTO note_links VALUES (%s, 'A', %s, 'link')", (notes["Q"], notes["A"]))

    def add_chunk(note_name, order, content, embedding):
        cid = conn.execute(
            "INSERT INTO chunks (note_id, chunk_order, heading_path, content, embedding)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (notes[note_name], order, f"{note_name} H", content, str(embedding)),
        ).fetchone()[0]
        return cid

    cids = {
        "q": add_chunk("Q", 0, "q content", vec(1, 0)),
        "a": add_chunk("A", 0, "a content", vec(0.95, 0.3)),
        "b": add_chunk("B", 0, "b content", vec(0.7, 0.7)),
    }
    return {"conn": conn, "notes": notes, "cids": cids}


QUERY = vec(1, 0)  # closest to q (cos=1), then a (cos≈0.95), then b (cos≈0.71)


def test_lexical_variant_returns_seed_chunks(vault):
    conn = vault["conn"]
    # lexical_search returns by ts_rank_cd, not cosine. We need text matching.
    # Instead of relying on lexical quality, verify the variant path produces chunks.
    from ask_ragu.retrieval.lexical import lexical_search

    lexical = lexical_search(conn, "q content")
    assert lexical  # "q content" matches the Q chunk's tsv
    ctx = retrieve_variant(conn, "q content", QUERY, "lexical", token_budget=100_000)
    assert all(c.source == "seed" for c in ctx)
    assert all(c.provenance == "direct" for c in ctx)


def test_vector_variant_applies_relevance_floor(vault, monkeypatch):
    conn = vault["conn"]
    # vec(0, 1) is orthogonal to Q's chunk (cos 0), ~0.30 to A, ~0.71 to B. Floor at 0.8 -> refusal.
    query_orth = vec(0, 1)
    monkeypatch.setattr(settings, "retrieval_relevance_floor", 0.8)
    ctx = retrieve_variant(conn, "any question", query_orth, "vector", token_budget=100_000)
    assert ctx == []

    # Floor below the best cosine (0.71) -> proceeds.
    monkeypatch.setattr(settings, "retrieval_relevance_floor", 0.3)
    ctx = retrieve_variant(conn, "any question", query_orth, "vector", token_budget=100_000)
    assert len(ctx) > 0


def test_hybrid_uses_rrf(vault, monkeypatch):
    conn = vault["conn"]
    # With floor disabled, hybrid should have at least as many seeds as RRF produces.
    monkeypatch.setattr(settings, "retrieval_relevance_floor", -1.0)
    ctx = retrieve_variant(conn, "q content", QUERY, "hybrid", token_budget=100_000)
    assert all(c.source == "seed" for c in ctx)


def test_hybrid_graph_expands(vault, monkeypatch):
    conn = vault["conn"]
    monkeypatch.setattr(settings, "retrieval_relevance_floor", -1.0)
    monkeypatch.setattr(settings, "retrieval_hop_decay_hop1", 0.8)
    monkeypatch.setattr(settings, "retrieval_hop_decay_hop2", 0.6)
    monkeypatch.setattr(settings, "retrieval_expanded_budget_share", 0.4)
    monkeypatch.setattr(settings, "retrieval_chars_per_token", 4)

    no_graph = retrieve_variant(conn, "q content", QUERY, "hybrid", token_budget=100_000)
    with_graph = retrieve_variant(conn, "q content", QUERY, "hybrid+graph", token_budget=100_000)

    # Without graph: all seeds, no expanded chunks.
    assert all(c.source == "seed" for c in no_graph)
    # With graph: no fewer chunks (expansion adds, never removes seeds).
    assert len(with_graph) >= len(no_graph)


def test_all_four_variants_run(vault, monkeypatch):
    """Smoke test: all four variants produce output without error."""
    monkeypatch.setattr(settings, "retrieval_relevance_floor", -1.0)
    monkeypatch.setattr("ask_ragu.retrieval.eval_harness.embed_query", lambda q: QUERY)

    from ask_ragu.evalset import Question

    questions = [Question(id="t1", kind="single", question="q", gold=[], origin="owner")]
    results = evaluate(vault["conn"], questions, token_budget=100_000)
    assert len(results) == 4  # one per variant
    assert {r.variant for r in results} == set(VARIANTS)


# --- Aggregation and output formatting -------------------------------------------


def _result(variant, qid="q1", kind="single", hits=None, mrr=0.5, ctx=3):
    return EvalResult(
        question_id=qid,
        kind=kind,
        variant=variant,
        hit_at=hits or {5: 1, 10: 1},
        mrr=mrr,
        context_len=ctx,
    )


def test_aggregate_averages_per_variant():
    results = [
        _result("lexical", "q1", hits={5: 1, 10: 1}, mrr=1.0),
        _result("lexical", "q2", hits={5: 0, 10: 1}, mrr=0.0),
        _result("vector", "q1", hits={5: 1, 10: 1}, mrr=0.5),
        _result("vector", "q2", hits={5: 1, 10: 1}, mrr=0.0),
    ]
    from ask_ragu.retrieval.eval_harness import aggregate

    a = aggregate(results)
    assert a["lexical"]["hit@5"] == 0.5
    assert a["lexical"]["hit@10"] == 1.0
    assert a["lexical"]["mrr"] == 0.5
    assert a["vector"]["hit@5"] == 1.0


def test_format_ablation_table():
    results = [
        _result("lexical", hits={5: 1, 10: 1}, mrr=1.0),
        _result("vector", hits={5: 0, 10: 1}, mrr=0.5),
        _result("hybrid", hits={5: 1, 10: 1}, mrr=0.75),
        _result("hybrid+graph", hits={5: 1, 10: 1}, mrr=1.0),
    ]
    table = format_ablation(results)
    assert "| Variant |" in table
    assert "| lexical | 1.000 |" in table
    assert "| hybrid+graph |" in table


def test_format_per_question_lists_each_variant():
    results = [_result(v) for v in VARIANTS]
    table = format_per_question(results)
    assert "| Q ID |" in table
    for v in VARIANTS:
        assert v in table


def test_save_csv(tmp_path):
    results = [
        _result("lexical", "q1", hits={5: 1, 10: 1}, mrr=1.0, ctx=3),
        _result("hybrid+graph", "q1", hits={5: 1, 10: 1}, mrr=0.5, ctx=7),
    ]
    out = tmp_path / "eval.csv"
    save_csv(results, out)
    rows = list(csv.reader(out.read_text().splitlines()))
    assert rows[0] == [
        "date",
        "variant",
        "question_id",
        "kind",
        "hit@5",
        "hit@10",
        "mrr",
        "context_size",
    ]
    assert rows[1][1] == "lexical"
    assert rows[1][2] == "q1"
    assert rows[2][1] == "hybrid+graph"
