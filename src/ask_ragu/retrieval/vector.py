"""Vector search (SPEC §9 step 2): cosine kNN over chunk embeddings, exact (no ANN index).

bge vectors are normalized, so cosine (<=>) and inner product rank alike; <=> is the metric the
model is trained for and stays right if a model without normalization is ever swapped in.
"""

from uuid import UUID

import psycopg

from ask_ragu.settings import settings

# Exact scan: every chunk is compared. Ordering by the score alias computes the distance once per
# row; repeating `embedding <=> q` in ORDER BY computed it twice (p50 37 -> 20 ms on the laptop).
# An HNSW index needs `ORDER BY embedding <=> q` written out, and ignores the id tie-break.
# ponytail: exact kNN, p95 ~27 ms at ~2k chunks (laptop); HNSW if the Micro misses the budget.
SEARCH = """
SELECT id, note_id, 1 - (embedding <=> %(q)s::vector) AS score
FROM chunks
ORDER BY score DESC, id
LIMIT %(k)s
"""


def vector_search(conn: psycopg.Connection, query: list[float]) -> list[tuple[int, UUID, float]]:
    """(chunk_id, note_id, cosine similarity), best first; RETRIEVAL_CANDIDATES at most.

    `query` is embed_query(question): embed once, outside, so callers off the event loop
    (asyncio.to_thread) and the eval harness reuse it.
    """
    return conn.execute(SEARCH, {"q": str(query), "k": settings.retrieval_candidates}).fetchall()
