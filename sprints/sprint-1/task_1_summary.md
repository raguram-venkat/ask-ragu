# Task 1 — Repo skeleton & tooling

Status: todo
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

- 

Decisions made here:

- 

Gotchas:

- 
