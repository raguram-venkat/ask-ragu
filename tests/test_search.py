"""GET /search debug endpoint (SPEC §6)."""

from contextlib import nullcontext

from fastapi.testclient import TestClient

from ask_ragu import db
from ask_ragu.main import app

client = TestClient(app)


def test_search_returns_stages_and_context(conn, monkeypatch):
    from ask_ragu.index.embed import embed_query

    db.migrate(conn)

    text = "matcha latte recipe"
    emb = embed_query(text)

    nid = conn.execute(
        "INSERT INTO notes (path, title, note_type, content_hash, meta_hash) "
        "VALUES (%s, %s, %s, '', '') RETURNING id",
        ("a.md", "Note A", "concept"),
    ).fetchone()[0]

    # tsv is STORED/GENERATED from heading_path + content, so don't insert it.
    conn.execute(
        "INSERT INTO chunks (note_id, chunk_order, heading_path, content, embedding) "
        "VALUES (%s, %s, %s, %s, %s)",
        (nid, 0, "Note A\n## Ingredients", text, str(emb)),
    )

    # Point /search at the test schema instead of the real DB.
    monkeypatch.setattr(db, "connect", lambda: nullcontext(conn))
    # Avoid the real model load inside the route; the chunk already has a real embedding.
    monkeypatch.setattr("ask_ragu.api.search.embed_query", lambda q: emb)

    r = client.get("/search?q=matcha+latte+recipe")
    assert r.status_code == 200
    body = r.json()
    assert body["question"] == "matcha latte recipe"
    assert body["stages"]["lexical_hits"] >= 1
    assert body["stages"]["vector_hits"] >= 1
    assert body["stages"]["seeds"] >= 1
    assert len(body["context"]) >= 1
    assert body["context"][0]["note_title"] == "Note A"
    assert body["context"][0]["provenance"] == "direct"
    assert body["context"][0]["source"] == "seed"
