"""Reciprocal Rank Fusion of lexical and vector rankings (SPEC §9 step 2, ADR-0008).

RRF fuses rankings across incomparable score scales (ts_rank_cd vs cosine) by rank
position alone: score = Σ 1/(k + rank). The relevance floor on the best vector
similarity refuses early when the vault doesn't cover the question.

k and the seed count are config (ADR-0023): RETRIEVAL_RRF_K=60 (Cormack et al.
2009 standard), RETRIEVAL_SEED_TOP_K=8.

References:
  Cormack, Clarke & Büttcher (2009), "Reciprocal Rank Fusion outperforms Condorcet
  and individual Rank-Biased Search Machines" — k=60 is their standard constant.
"""

from uuid import UUID

from ask_ragu.settings import settings

# Cormack et al. (2009): the standard k. Ranks beats raw-score mixing because
# ts_rank_cd and cosine live on incomparable scales (ADR-0008).
# RRF_K and TOP_K come from settings (ADR-0023: retrieval meta-variables are config).


def reciprocal_rank_fusion(
    lexical_results: list[tuple[int, UUID, float]],
    vector_results: list[tuple[int, UUID, float]],
) -> list[tuple[int, UUID, float]]:
    """Fuse two ranked lists via RRF. Returns (chunk_id, note_id, score), best first,
    capped at retrieval_seed_top_k.

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

    k = settings.retrieval_rrf_k
    for rank, (chunk_id, note_id, _) in enumerate(lexical_results):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank)
        notes[chunk_id] = note_id

    for rank, (chunk_id, note_id, _) in enumerate(vector_results):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank)
        notes[chunk_id] = note_id

    # Ties broke by chunk_id (deterministic), same convention as lexical_search and vector_search.
    return sorted(
        ((cid, notes[cid], s) for cid, s in scores.items()),
        key=lambda r: (-r[2], r[0]),
    )[: settings.retrieval_seed_top_k]
