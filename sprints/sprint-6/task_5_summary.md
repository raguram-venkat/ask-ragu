# Task 5 — CI

Status: todo
Est: 60m
Spec: SPEC.md §3

What: GitHub Actions on the code repo: uv sync, ruff, pytest with a Postgres+pgvector service container.

Approach: Tests use only the fixture vault and fake providers; cache uv downloads.

Read first:

- GitHub Actions: service containers
- astral-sh/setup-uv

Watch out for:

- Runner is amd64 — fine for tests; arm64 image builds are a BACKLOG item.
- No secrets needed for CI — if a test needs one, the test is wrong.

Done when: Green badge on main; branch protection blocks merging on red.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
