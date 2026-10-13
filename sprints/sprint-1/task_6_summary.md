# Task 6 — Deploy workflow

Status: todo — re-targeted 2026-10-13 to the Micro (D-014, ADR-0020)
Est: 90m
Spec: SPEC.md §11 · D-014

What: One command ships a code change from the laptop to the Micro and restarts the stack; compose sets restart policies and memory limits sized from measurements; first full index and latency numbers recorded.

Approach: Build the app image on the laptop (x86_64, same as the Micro), ship it with `docker save … | gzip | ssh ragu-vm 'gunzip | docker load'`, then `docker compose up -d` there. Memory limits and Postgres settings come from `.env` (compose interpolates `${VAR}` from `.env`).

Read first:

- Compose: `mem_limit`, restart policies, variable interpolation
- Postgres docs: Resource Consumption (shared_buffers, work_mem, maintenance_work_mem, max_connections)
- task_3's measured table; ADR-0011 (index is disposable)

Steps:

1. `.env` / `.env.example` keys (config-in-.env rule): `APP_MEM_LIMIT`, `POSTGRES_MEM_LIMIT`, `CADDY_MEM_LIMIT`; `PG_SHARED_BUFFERS`, `PG_MAX_CONNECTIONS`, `PG_WORK_MEM`, `PG_MAINTENANCE_WORK_MEM`. Starting guesses for the Micro, not measurements: 450m / 250m / 64m; 64MB / 20 / 4MB / 32MB. The laptop `.env` may keep larger values. Postgres flags go in compose as `command: ["postgres", "-c", "shared_buffers=${PG_SHARED_BUFFERS}", …]`.
2. `compose.override.yml` is laptop-only (ports, vault mount): the Micro runs `compose.yml` alone, or a Micro-only override that is never committed with secrets.
3. Ship: `docker compose build app` on the laptop → save/load over SSH → `ssh ragu-vm 'cd ask-ragu && git pull && docker compose up -d'`. Wrap it in one command (Makefile target or a short script; the smallest thing that works).
4. First full index (after task_5's clone): `docker compose exec app askragu index --full` on the Micro, with `docker stats` and `free -m` in a second session. Record wall time, app peak RSS, swap peak. If it takes > 60 min or gets OOM-killed: build the index on the laptop, `pg_dump -Fc` → `scp` → `pg_restore` on the Micro (same migrations, same settings hash, so the next sync stays incremental — verify with a no-op `askragu index`).
5. Measure, then set limits: idle and during 20 queries (the synthetic sample questions), RSS per container. Each `*_MEM_LIMIT` = measured peak + 30%; the sum + OS must fit in 1 GB, with swap only for spikes.
6. Latency (feeds Sprint 4's DoD): query embedding p50/p95 and retrieval p95; re-run `scripts/bench_expansion.py` there (aggregates only).
7. `sudo reboot`: everything comes back on its own, the A1 runner too.

Watch out for:

- Building on the Micro (1 GB) is slow and can OOM on `uv sync`: build on the laptop.
- If the Micro can't hold the stack, fallbacks in this order, each decided with the owner and logged: (1) stop the A1 runner; (2) laptop builds the full index, the Micro only syncs incrementally; (3) lower `RETRIEVAL_CANDIDATES` / `GRAPH_TOTAL_CAP` only if latency, not RAM, is the problem (changes eval results: re-run the ablation); (4) managed free Postgres — breaks SPEC §4 (all note text off-host), needs its own D-entry and the owner's explicit sign-off.
- Queries during a full index will be slow (one fractional OCPU); syncs are already serialized (ADR-0018).

Done when: one command takes a laptop change to the running Micro stack; the stack survives a reboot; this table is filled:

| Measure | Value |
|---|---|
| Idle RSS: postgres / app / caddy / runner / OS | |
| Full index: wall time, app peak RSS, swap peak (or "laptop-built, restored") | |
| Query embedding p50 / p95 | |
| Retrieval p95, LLM excluded | |
| Final `*_MEM_LIMIT` values | |
| Survives reboot | |

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
