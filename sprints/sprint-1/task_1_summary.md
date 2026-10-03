# Task 1 — Repo skeleton & tooling

Status: done
Est: 60m
Spec: SPEC.md §6

What: Python package `askragu` with a FastAPI app and three stub routers (health, webhook, chat), managed with uv, linted with ruff, tested with pytest.

Approach: src layout with empty homes for later sprints (`api/ index/ graph/ retrieval/ llm/`); settings via pydantic-settings from env; pre-commit runs ruff and gitleaks.

Read first:

- uv docs: `uv init --package`, lockfile
- FastAPI: Bigger Applications (APIRouter)
- pydantic-settings

Watch out for:

- This repo will be public: no vault content, ever. Fixtures will be synthetic (Sprint 2).
- `.env` in .gitignore from the first commit; ship `.env.example` with every key and empty values.
- Pin the Python version (`.python-version`) so laptop (x64) and VM (arm64) match.

Done when: `uv run pytest` passes a health test, `uv run ruff check` is clean, pre-commit hooks run on commit.

---

Filled in while working

Files touched:

- pyproject.toml, uv.lock, .gitignore, .env.example, .pre-commit-config.yaml
- src/ask_ragu/{main,settings}.py, src/ask_ragu/api/{health,webhook,chat}.py
- empty packages: src/ask_ragu/{index,graph,retrieval,llm}/
- tests/test_health.py

Decisions made here:

- Package stays `ask_ragu` (what `uv init --package` generated), not `askragu`.
- Stub /webhook and /chat return 501 until their sprints; /healthz returns `{"status": "ok"}` (DB check lands in Task 2).
- Settings: only DATABASE_URL for now, with a localhost default; `env_ignore_empty` so blank `.env.example` values fall back to defaults. Keys get added when the code that reads them lands.
- Ruff rules E, F, I, B, UP; ruff-format enforced in pre-commit.
- Dropped the `ask-ragu` console script from uv's template; the app runs via uvicorn (`ask_ragu.main:app`).

Gotchas:

- The original .gitignore had no trailing newline, so appending lines turned `.env` into `.env.venv/` and `.env` got staged. Check with `git check-ignore -v .env`.
- Starlette's TestClient warns that `httpx` is deprecated, so the dev dependency is `httpx2`.
