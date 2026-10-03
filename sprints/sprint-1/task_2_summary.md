# Task 2 — Local compose stack + migrations

Status: done
Est: 90m
Spec: SPEC.md §6, §7

What: docker-compose.yml with postgres (pgvector image) and app, named volumes, healthchecks, and a tiny migration runner applying `migrations/0001_extensions.sql` at startup.

Approach: App `depends_on` postgres with `condition: service_healthy`; runner applies numbered .sql files in order, each in a transaction, recorded in `schema_migrations`; /healthz runs `SELECT 1` and checks the `vector` extension.

Read first:

- pgvector README (Docker, CREATE EXTENSION)
- Compose: healthcheck, depends_on conditions, named volumes

Watch out for:

- Pin an exact pgvector tag (e.g. `0.8.x-pg17`) and confirm arm64 is in its manifest: `docker manifest inspect pgvector/pgvector:<tag>`.
- No `ports:` on postgres in the base compose file; local psql access goes in `compose.override.yml` (not deployed).
- Runner must skip already-applied versions — restarts happen constantly.

Done when: `docker compose up` → both healthy; `curl localhost:8000/healthz` shows db ok + vector ok; a restart applies nothing twice.

---

Filled in while working

Files touched:

- compose.yml, compose.override.yml, Dockerfile, .dockerignore, .env.example
- migrations/0001_extensions.sql
- src/ask_ragu/db.py (connect + migrate), src/ask_ragu/main.py (lifespan runs migrations), src/ask_ragu/api/health.py, src/ask_ragu/settings.py
- tests/test_health.py, tests/test_migrate.py

Decisions made here:

- Image pinned to `pgvector/pgvector:0.8.6-pg17` (amd64 + arm64 in manifest).
- Base file is `compose.yml`, not `docker-compose.yml`: Compose only auto-merges `compose.override.yml` into a base with the same stem.
- Postgres and app ports are published only in compose.override.yml, bound to 127.0.0.1. On the VM, Caddy (Task 4) will be the only way in.
- Connections are autocommit; the runner opens an explicit `conn.transaction()` per file, and the version is recorded in the same transaction as the SQL.
- /healthz returns 503 with `db`/`vector` fields on failure, so the compose healthcheck and outside monitoring both see it.
- Migration tests use a real Postgres in a throwaway schema and skip when none is reachable. The health test fakes a DB-down case.
- All config lives only in .env: compose passes it to both containers with `env_file`, settings.py declares the keys with no defaults (a missing key fails at startup), and nothing is hardcoded in compose or code.
- DATABASE_URL uses the compose host `postgres`. Host-side pytest uses TEST_DATABASE_URL (`localhost`, via the override's port), because the host and the container reach the DB at different addresses.

Gotchas:

- On a non-autocommit psycopg connection, the first SELECT opens an implicit transaction, which turns every later `conn.transaction()` into a savepoint that never commits, so migrations would silently vanish. Fixed with `autocommit=True`.
- pydantic-settings rejects unknown keys from env_file by default. The shared .env has POSTGRES_*, so `extra="ignore"`.
