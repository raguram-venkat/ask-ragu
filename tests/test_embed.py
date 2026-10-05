"""Loads the real model (downloads ~65 MB into EMBEDDING_CACHE_DIR on the first run)."""

from ask_ragu.index.embed import embed_passages, embed_query, passage_text


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))  # vectors are normalized: dot = cosine


def test_related_passage_scores_higher():
    q = embed_query("how does a hash map handle collisions?")
    related, unrelated = embed_passages(
        [
            passage_text(
                "Hash Map > Collisions", "Chaining keeps colliding keys in a per-bucket list."
            ),
            passage_text("Photosynthesis", "Plants turn light into chemical energy."),
        ]
    )
    assert len(q) == len(related) == 384
    assert abs(dot(q, q) - 1) < 1e-4
    assert dot(q, related) > dot(q, unrelated) + 0.2
