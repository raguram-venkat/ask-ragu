# AGENTS.md — ask-ragu

Briefing for any engineer or AI agent picking up this repo.

## Read in this order

1. INDEX.md — status and where everything lives.
2. SPEC.md — living source of truth. Lines marked `[D-00N]` were amended; history in DEVIATIONS.md.
3. The current sprint's `sprint.md`, then the previous sprint's `handoff.md`.

## Rules

- A change to what SPEC.md says → `D-` entry in DEVIATIONS.md + amend SPEC.md with the `[D-00N]` marker, same commit.
- A decision with a real rejected alternative → new ADR in `adr/` (see `adr/_templates/README.md`).
- Noticed but not doing now (idea, debt, bug) → one line in BACKLOG.md.
- Task files: fill "Files touched / Decisions / Gotchas" while working, not afterwards.
- Don't edit `_templates/` unless deliberately changing the convention for everyone.
- The code repo is public: no vault content, eval questions, keys, or hostnames in git. Tests use the synthetic fixture vault.
- The owner is learning: prefer hints, review, and small examples over writing large code blocks, unless asked.

## Stack

Python 3.12 · uv · FastAPI · psycopg 3 + raw SQL · Postgres 17 + pgvector · fastembed (bge-small-en-v1.5, 384-d) · llama.cpp server · Caddy · Docker Compose · Oracle Cloud A1 (arm64, 2 OCPU / 12 GB)

## Two repos, don't confuse them

- This repo (ask-ragu): code + docs, public.
- The vault repo (Knowledge base): private, read-only to this system via deploy key.
