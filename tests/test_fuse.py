"""Task 3: RRF fusion + relevance floor (SPEC §9 step 2, ADR-0008)."""

from uuid import uuid4

import pytest

from ask_ragu.retrieval.fuse import TOP_K, reciprocal_rank_fusion
from ask_ragu.settings import settings

NOTE = uuid4()


def _result(ids: list[int], base: float = 1.0):
    """Build a ranked list of (chunk_id, note_id, score) — scores ignored by RRF."""
    return [(i, NOTE, base) for i in ids]


@pytest.fixture
def search_floor_zero(monkeypatch):
    """Disable the relevance floor so RRF math tests aren't refuted by it."""
    monkeypatch.setattr(settings, "retrieval_relevance_floor", -1.0)


def test_rrf_puts_overlap_above_single_list(search_floor_zero):
    # chunk 3 appears in both lists → 1/60 + 1/62; chunk 1 only lexical → 1/60.
    lexical = _result([1, 2, 3])
    vector = _result([3, 4, 5])
    assert reciprocal_rank_fusion(lexical, vector) == [
        (3, NOTE, 1 / 60 + 1 / 62),
        (1, NOTE, 1 / 60),
        (2, NOTE, 1 / 61),
        (4, NOTE, 1 / 61),
        (5, NOTE, 1 / 62),
    ]


def test_rrf_is_rank_based_not_score_based(search_floor_zero):
    # Even though lexical gives chunk 2 a higher raw score than chunk 1,
    # RRF ranks by position: chunk 1 (rank 0) beats chunk 2 (rank 1).
    lexical = [(1, NOTE, 5.0), (2, NOTE, 99.0)]
    vector = _result([3])
    # chunk 1 (rank 0) and chunk 3 (rank 0) both get 1/60; chunk 2 (rank 1) gets 1/61.
    # RRF ignores raw scores: chunk 1's 5.0 beats chunk 2's 99.0 because 1 is ranked first.
    # Ties (1/60) break by chunk id: 1 < 3.
    assert reciprocal_rank_fusion(lexical, vector) == [
        (1, NOTE, 1 / 60),
        (3, NOTE, 1 / 60),
        (2, NOTE, 1 / 61),
    ]


def test_top_k_cap(search_floor_zero):
    # More than TOP_K distinct chunks → trimmed to TOP_K, best first.
    lexical = _result(list(range(1, 15)))
    fused = reciprocal_rank_fusion(lexical, [])
    assert len(fused) == TOP_K
    assert fused[0][0] == 1  # best (rank 0) survives the cap


def test_relevance_floor_refuses_early(monkeypatch):
    # Best vector cosine (0.2) is below floor (0.3) → empty, no RRF.
    monkeypatch.setattr(settings, "retrieval_relevance_floor", 0.3)
    lexical = _result([1, 2])
    vector = [(3, NOTE, 0.2)]  # below floor
    assert reciprocal_rank_fusion(lexical, vector) == []


def test_relevance_floor_passes_when_above(monkeypatch):
    monkeypatch.setattr(settings, "retrieval_relevance_floor", 0.3)
    lexical = _result([1, 2])
    vector = [(3, NOTE, 0.5)]  # above floor → proceeds
    fused = reciprocal_rank_fusion(lexical, vector)
    assert len(fused) > 0


def test_floor_skipped_when_no_vector_results(monkeypatch):
    # No vector results → no floor check; lexical results pass through RRF.
    monkeypatch.setattr(settings, "retrieval_relevance_floor", 0.9)
    lexical = _result([1, 2])
    fused = reciprocal_rank_fusion(lexical, [])
    assert len(fused) == 2
