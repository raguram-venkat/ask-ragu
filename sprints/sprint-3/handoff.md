# Handoff — Sprint 3

Closed 2026-10-10.

System state: Laptop only (D-008). Same compose stack as Sprint 2, no new migration. After every sync (noop included) all links are re-resolved vault-wide (D-012): 2,658 of 2,660 resolve, the 2 dangling are a parser bug (BACKLOG). The graph layer is three modules: `graph/hubs.py` (one-hop edges incl. MOC/tag hubs, computed at query time, ADR-0010), `graph/expand.py` (bounded per-hop expansion, ADR-0015) and `graph/report.py` behind `askragu graph neighbors|health`. Graph settings in `.env`: `GRAPH_TAG_HUB_MAX_SHARE=0.10`, `GRAPH_MAX_HOPS=2`, `GRAPH_FANOUT_CAP=10`, `GRAPH_TOTAL_CAP=30` (query time, never re-index). A1 still not acquired; the retry runner on the Micro keeps trying.

How to resume:

- `docker compose up -d --build`; `docker compose exec app askragu graph health`; `docker compose exec app askragu graph neighbors "<note>"`. Tests: `uv run pytest -q`.
- Re-measure expansion: `uv run python scripts/bench_expansion.py` (laptop; on the A1 once it exists).
- Before Sprint 4 tuning: the owner rewrites the 18 draft eval questions (D-003); building search (Tasks 1–3) doesn't need them, tuning does.

Open risks / unfinished threads:

- Escaped-pipe links in tables (`[[Note\|alias]]`) dangle: parser fix + PARSE_VERSION bump (BACKLOG).
- Expansion knows nothing about the question: ties among equal hub neighbours are a seeded shuffle, and a parent MOC re-expanded at hop 2 brings back cut siblings. Both are Sprint 4 Task 4 (BACKLOG).
- Caps (fan-out 10, total 30) are starting values from vault stats, not tuned (Sprint 4 eval).
- Expansion p95 on the A1 unknown; laptop worst case 42 ms of a 50 ms budget. If it's over, store resolved, deduplicated links at resolve time (ADR-0015).
- Edge-feedback learning (weights from cited notes or thumbs) is a post-v1 idea (BACKLOG).

Relevant ADRs and deviations:

- ADR-0002, 0010 (accepted), 0015 (new) · D-002, D-007, D-012, D-013

Next sprint starts at: Sprint 4, Task 1 — lexical search
