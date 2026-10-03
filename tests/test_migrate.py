"""Needs the compose Postgres reachable at TEST_DATABASE_URL in .env; skipped otherwise."""

import psycopg
import pytest
from dotenv import dotenv_values

from ask_ragu import db


@pytest.fixture
def conn():
    url = dotenv_values(".env").get("TEST_DATABASE_URL")
    try:
        c = psycopg.connect(url, autocommit=True, connect_timeout=3)
    except (psycopg.OperationalError, TypeError):
        pytest.skip("no Postgres at TEST_DATABASE_URL")
    c.execute("CREATE SCHEMA IF NOT EXISTS migrate_test")
    c.execute("SET search_path TO migrate_test")
    yield c
    c.execute("DROP SCHEMA migrate_test CASCADE")
    c.close()


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
