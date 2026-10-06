"""`conn` needs the compose Postgres at TEST_DATABASE_URL in .env; tests using it skip otherwise."""

import psycopg
import pytest
from dotenv import dotenv_values


@pytest.fixture
def conn():
    url = dotenv_values(".env").get("TEST_DATABASE_URL")
    try:
        c = psycopg.connect(url, autocommit=True, connect_timeout=3)
    except (psycopg.OperationalError, TypeError):
        pytest.skip("no Postgres at TEST_DATABASE_URL")
    c.execute("CREATE SCHEMA IF NOT EXISTS migrate_test")
    c.execute("SET search_path TO migrate_test, public")  # public: where the vector type lives
    yield c
    c.execute("DROP SCHEMA migrate_test CASCADE")
    c.close()
