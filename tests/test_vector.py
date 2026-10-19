"""Vector search (Sprint 4 Task 2): exact cosine kNN over chunk embeddings."""

import pytest

from ask_ragu import db
from ask_ragu.retrieval.vector import vector_search
from ask_ragu.settings import settings


def vec(x: float, y: float) -> list[float]:
    """A 384-d vector in the plane of the first two axes."""
    return [x, y] + [0.0] * 382


CHUNKS = {  # name: embedding; the query is vec(1, 0)
    "same": vec(1, 0),
    "long": vec(5, 0),  # same direction, 5x the length: cosine 1, unlike L2 or inner product
    "near": vec(1, 1),  # 45°: cosine 0.707
    "far": vec(0, 1),  # 90°: cosine 0
    "opposite": vec(-1, 0),  # cosine -1
}


@pytest.fixture
def search(conn, monkeypatch):
    monkeypatch.setattr(settings, "retrieval_candidates", 50)
    db.migrate(conn)
    (note,) = conn.execute(
        "INSERT INTO notes (path, title, note_type, content_hash)"
        " VALUES ('N.md', 'N', 'concept', '') RETURNING id"
    ).fetchone()
    names = {}
    for order, (name, embedding) in enumerate(CHUNKS.items()):
        (cid,) = conn.execute(
            "INSERT INTO chunks (note_id, chunk_order, heading_path, content, embedding)"
            " VALUES (%s, %s, 'H', 'c', %s) RETURNING id",
            (note, order, str(embedding)),
        ).fetchone()
        names[cid] = name

    def search(query):
        return [(names[cid], round(score, 3)) for cid, _, score in vector_search(conn, query)]

    return search


def test_ranked_by_cosine_similarity_ties_by_id(search):
    assert search(vec(1, 0)) == [
        ("same", 1.0),
        ("long", 1.0),
        ("near", 0.707),
        ("far", 0.0),
        ("opposite", -1.0),
    ]


def test_query_length_does_not_matter(search):
    assert search(vec(0.2, 0)) == search(vec(1, 0))


def test_candidates_cap(search, monkeypatch):
    monkeypatch.setattr(settings, "retrieval_candidates", 2)
    assert search(vec(0, 1)) == [("far", 1.0), ("near", 0.707)]
