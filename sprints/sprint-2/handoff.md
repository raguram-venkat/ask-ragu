# Handoff — Sprint 2

Closed 2026-10-06.

System state: Laptop only (D-008). Compose stack (Postgres 17 + pgvector, app) runs migrations 0001–0004; the app syncs at startup, on `POST /webhook` (HMAC-verified, 202) and via `askragu index [--full]`, all under one per-schema advisory lock. The vault is mounted read-only at `/vault` (`VAULT_REF=HEAD`, `VAULT_FETCH=false`). Index: 748 notes, 1,965 chunks, 2,660 raw links (unresolved: `target_note_id` is NULL until Sprint 3), 84 tags; `/index/status` shows commit, model, code versions, whether settings are current, and the last sync. A1 still not acquired; the retry runner on the Micro keeps trying (Sprint 1 Task 7).

How to resume:

- `docker compose up -d --build`, then `curl localhost:8000/index/status`. Tests: `uv run pytest -q` (DB tests need the compose Postgres; they skip otherwise).
- Before Sprint 4: rewrite the 18 draft eval questions in `eval/questions.private.yaml` in your own words (or replace them), set `origin: owner`, run `uv run python -m ask_ragu.evalset eval/questions.private.yaml /path/to/vault`.
- Changing an index setting: edit `.env`, `docker compose up -d` (recreates the container); the startup sync sees the new settings hash. Changing parser/chunker code: the pre-commit hook tells you which version to bump.
- arm64 checks without ARM hardware: `cheatsheets/arm64-emulation.md`.
- Sprint 3 starts at Task 1 (link resolution). Resolve ADR-0010 (MOC/tag hubs) before Sprint 3 Task 2.

Open risks / unfinished threads:

- Eval questions are drafts until rewritten (D-003: they must be fixed before retrieval tuning).
- Link resolution facts for Sprint 3 (sprint-2 task_1/task_3): 54 links hit a filename that exists in two folders (needs a tie-break), 9 dangling, no `aliases` anywhere; tags are one per note (= `domain`), so tag hubs are disjoint domain clusters.
- `## Part of` links are parent edges (concept → MOC → MOC): a typed parent edge is a Sprint 3 / ADR-0010 idea (BACKLOG).
- Retrieval quirk for Sprint 4: MOC `## Links` lists score as high as definitions (BACKLOG).
- 8 code-heavy chunks exceed 512 tokens and are truncated in the vector (BACKLOG).
- VM: the clone must be writable with the deploy key, `.env` needs `VAULT_FETCH=true`, `VAULT_REF=origin/main`; the working-tree reset runs as root in the container (file ownership, BACKLOG). Embedding throughput on the A1 not measured yet.
- Fixture vault deferred (BACKLOG).

Relevant ADRs and deviations:

- ADR-0003, 0004 (amended), 0005, 0011 (proposed), 0016, 0017, 0018 · D-008, D-010, D-011

Next sprint starts at: Sprint 3, Task 1 — link resolution
