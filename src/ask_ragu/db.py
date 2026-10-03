from pathlib import Path

import psycopg

from ask_ragu.settings import settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def connect() -> psycopg.Connection:
    # autocommit: transactions are explicit via conn.transaction(), never implicit.
    # ponytail: a connection per call; switch to psycopg_pool when request volume needs it.
    return psycopg.connect(settings.database_url, autocommit=True, connect_timeout=3)


def migrate(conn: psycopg.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply numbered .sql files not yet in schema_migrations, each in its own transaction."""
    with conn.transaction():
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY)")
    applied = {v for (v,) in conn.execute("SELECT version FROM schema_migrations")}

    ran = []
    for path in sorted(migrations_dir.glob("*.sql")):
        if path.stem in applied:
            continue
        with conn.transaction():
            conn.execute(path.read_text())
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
        ran.append(path.stem)
    return ran
