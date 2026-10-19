"""Reciprocal Rank Fusion of lexical and vector rankings (SPEC §9 step 2, ADR-0008).

RRF fuses rankings across incomparable score scales (ts_rank_cd vs cosine) by rank
position alone: score = Σ 1/(60 + rank). The relevance floor on the best vector
similarity refuses early when the vault doesn't cover the question.

References:
  Cormack, Clarke & Büttcher (2009), "Reciprocal Rank Fusion outperforms Condorcet
  and individual Rank-Biased Search Machines" — k=60 is their standard constant.
"""

from uuid import UUID

from ask_ragu.settings import settings

# Cormack et al. (2009): the standard k. Ranks beats raw-score mixing because
# ts_rank_cd and cosine live on incomparable scales (ADR-0008).
RRF_K = 60
# Seed chunks taken to graph expansion (SPEC §9 step 2: k≈8).
TOP_K = 8


def reciprocal_rank_fusion(
    lexical_results: list[tuple[int, UUID, float]],
    vector_results: list[tuple[int, UUID, float]],
) -> list[tuple[int, UUID, float]]:
    """Fuse two ranked lists via RRF. Returns (chunk_id, note_id, score), best first, ≤ TOP_K.

    Relevance floor: if the best vector similarity falls below
    `settings.retrieval_relevance_floor`, the vault doesn't cover the question — return []
    instead of fusing noise. Tuned on eval v0 (D-003); the default 0.3 is a placeholder.
    Lexical surface matches alone aren't enough: they produce noise on shared words
    without semantic relevance.
    """
    # Early refusal: the best vector match is the closest semantic neighbour available.
    # If even it can't clear the floor, the question is unanswerable from this vault.
    if vector_results and vector_results[0][2] < settings.retrieval_relevance_floor:
        return []

    scores: dict[int, float] = {}
    notes: dict[int, UUID] = {}

    for rank, (chunk_id, note_id, _) in enumerate(lexical_results):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (RRF_K + rank)
        notes[chunk_id] = note_id

    for rank, (chunk_id, note_id, _) in enumerate(vector_results):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (RRF_K + rank)
        notes[chunk_id] = note_id

    # Ties broke by chunk_id (deterministic), same convention as lexical_search and vector_search.
    return sorted(
        ((cid, notes[cid], s) for cid, s in scores.items()),
        key=lambda r: (-r[2], r[0]),
    )[:TOP_K]
