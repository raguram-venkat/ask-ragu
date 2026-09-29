# Task 2 — Local compose stack + migrations

Status: todo
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

- 

Decisions made here:

- 

Gotchas:

- 
