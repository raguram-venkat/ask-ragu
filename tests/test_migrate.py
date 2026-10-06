import psycopg
import pytest

from ask_ragu import db


def test_applies_in_order_and_only_once(conn, tmp_path):
    (tmp_path / "0001_a.sql").write_text("CREATE TABLE t (n int);")
    (tmp_path / "0002_b.sql").write_text("INSERT INTO t VALUES (1);")

    assert db.migrate(conn, tmp_path) == ["0001_a", "0002_b"]
    assert db.migrate(conn, tmp_path) == []
    assert conn.execute("SELECT count(*) FROM t").fetchone() == (1,)


def test_failed_migration_rolls_back(conn, tmp_path):
    (tmp_path / "0001_bad.sql").write_text("CREATE TABLE t (n int); SELECT nope;")

    with pytest.raises(psycopg.errors.UndefinedColumn):
        db.migrate(conn, tmp_path)
    assert conn.execute("SELECT to_regclass('t')").fetchone() == (None,)
    assert conn.execute("SELECT count(*) FROM schema_migrations").fetchone() == (0,)


def test_schema_v1_applies_and_cascades(conn):
    assert "0002_schema_v1" in db.migrate(conn)
    assert db.migrate(conn) == []

    (note,) = conn.execute(
        "INSERT INTO notes (path, title, note_type, content_hash)"
        " VALUES ('02 Concepts/A.md', 'A', 'concept', 'h') RETURNING id"
    ).fetchone()
    conn.execute(
        "INSERT INTO chunks (note_id, chunk_order, heading_path, content, embedding)"
        " VALUES (%s, 0, 'A > Intro', 'graphs are fun', %s)",
        (note, "[" + ",".join(["0"] * 384) + "]"),
    )
    conn.execute(
        "INSERT INTO note_links (source_note_id, raw_target, link_kind) VALUES (%s, 'B', 'link')",
        (note,),
    )
    conn.execute("INSERT INTO note_tags (note_id, tag) VALUES (%s, 'cs/graphs')", (note,))
    assert conn.execute("SELECT tsv @@ to_tsquery('english', 'graph') FROM chunks").fetchone() == (
        True,
    )

    conn.execute("DELETE FROM notes WHERE id = %s", (note,))
    for table in ("chunks", "note_links", "note_tags"):
        assert conn.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,), table
