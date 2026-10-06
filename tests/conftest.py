"""`conn` needs the compose Postgres at TEST_DATABASE_URL in .env; tests using it skip otherwise."""

import psycopg
import pytest
from dotenv import dotenv_values

SCHEMA = "migrate_test"


def _connect(schema: str) -> psycopg.Connection:
    url = dotenv_values(".env").get("TEST_DATABASE_URL")
    try:
        c = psycopg.connect(url, autocommit=True, connect_timeout=3)
    except (psycopg.OperationalError, TypeError):
        pytest.skip("no Postgres at TEST_DATABASE_URL")
    c.execute(f"SET search_path TO {schema}, public")  # public: where the vector type lives
    return c


@pytest.fixture
def conn():
    c = _connect(SCHEMA)
    c.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    yield c
    c.execute(f"DROP SCHEMA {SCHEMA} CASCADE")
    c.close()


@pytest.fixture
def connect():
    """Open more connections (another "process"), by default on the same test schema."""
    opened = []

    def make(schema: str = SCHEMA) -> psycopg.Connection:
        opened.append(_connect(schema))
        return opened[-1]

    yield make
    for c in opened:
        c.close()
