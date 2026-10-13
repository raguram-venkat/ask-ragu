# AGENTS.md — ask-ragu

Briefing for any engineer or AI agent picking up this repo. It holds the whole working agreement:
nothing the owner expects lives only in one tool's memory. If `AGENTS.local.md` exists, read it
too (private facts such as the vault path; gitignored, never committed).

## Session start

1. Read INDEX.md, then the current sprint's `sprint.md`, the previous sprint's `handoff.md`, and the task file in progress (Status: doing / in review).
2. Summarise where things stand in 10 lines or fewer, and ask about anything that waits on the owner.
3. Then continue that task, or walk the owner through the task under review. Nothing else.

## Read in this order

1. INDEX.md — status and where everything lives.
2. SPEC.md — living source of truth. Lines marked `[D-00N]` were amended; history in DEVIATIONS.md.
3. The current sprint's `sprint.md`, then the previous sprint's `handoff.md`.

## Where things go

- A change to what SPEC.md says → `D-` entry in DEVIATIONS.md + amend SPEC.md with the `[D-00N]` marker, same commit.
- A decision with a real rejected alternative → new ADR in `adr/` (see `adr/_templates/README.md`). `proposed` until the owner accepts it.
- Work to do → a task file in a sprint. Noticed but not doing now (idea, debt, bug) → one line in BACKLOG.md with the target sprint/task.
- No new ad-hoc folders or plan files: plans become D-entries, ADRs, task files and BACKLOG lines.
- Task files: fill "Files touched / Decisions / Gotchas" while working, not afterwards.
- Don't edit `_templates/` unless deliberately changing the convention for everyone.

## How the owner works

- One task at a time. The owner reviews before anything is committed. Commit only after review, and only that task's files (list them; never `git add -A`). Push only when asked.
- Say when every task of a sprint is done. Don't roll into the next sprint.
- Uncommitted files that aren't part of your task may be the owner's own work in progress: leave them out of your commits, and ask if unsure.
- Config lives only in `.env` + `.env.example`; `settings.py` has no defaults. Every tunable or "one-line change" goes there. Tests pin their own values with `monkeypatch` on `settings`, so editing `.env` can't break them.
- Indexing-code changes that alter output need an `EMBED_VERSION` / `PARSE_VERSION` bump; the pre-commit golden test (`tests/test_index_versions.py`) tells you which.
- Airtight over clever: measure before claiming, test hostile input, delete dead code, and say plainly what is met, caveated, or unmeasured.
- The owner is learning: explain what you did and why; prefer hints, review and small examples over large code blocks, unless asked.
- Never tune retrieval against the draft eval questions (D-003): only the owner's rewritten set.

## Vault privacy (public repo, ADR-0022)

- The code repo is public: no vault content, eval questions, keys, or hostnames in git. Task files hold aggregates or placeholders (`<Note title>`) only — never note titles, tags or topic names. Test fixtures and sample questions use a synthetic theme (coffee).
- Before each commit: `uv run python scripts/scan_vault_leaks.py`. Before any push: `uv run python scripts/scan_vault_leaks.py --push`. Both print file:line only.
- Your model provider sees everything you read. Unless your provider is listed as vault-safe in sprint-4/task_7, never read `.env`, `eval/*.private.*`, `scripts/*.private.*`, or the vault clone (path in `AGENTS.local.md`), and never run commands labelled "vault text" in `scripts/README.md` (e.g. `askragu graph neighbors`, `profile_vault.py`, ad-hoc real-vault searches). Ask the owner to run them and report numbers.

## Code style

Before writing code: does it need to exist? Is it already in this repo? Does the stdlib do it? An installed dependency? Only then the smallest code that works. No unrequested abstractions or scaffolding "for later". Non-trivial logic leaves one runnable test. A deliberate shortcut with a known ceiling gets a `ponytail:` comment naming the ceiling and the upgrade path.

## Commits

Message: `Sprint N Task M: <what>` (see `git log`). Last line: `Assisted-by: <model id> via <harness>`. pre-commit runs ruff, gitleaks and the index-version golden test; never skip it.

## Shell and VM

- SSH to the host with the alias `ragu-vm` (`~/.ssh/config`; never a raw IP or key path in commands or docs). The key has a passphrase: the owner unlocks it.
- The owner keeps command cheatsheets in `cheatsheets/` (gitignored, local): read them before giving shell or VM instructions.
- The vault clone is read-only to this project: never write to it.

## Stack

Python 3.12 · uv · FastAPI · psycopg 3 + raw SQL · Postgres 17 + pgvector · fastembed (int8 bge-small-en-v1.5, 384-d) · hosted LLM APIs serving open-weight models (+ optional llama.cpp in a Hugging Face Space, D-015) · Caddy · Docker Compose · Oracle Cloud Always Free E2.1.Micro (x86_64, 1 GB; D-014)

## Two repos, don't confuse them

- This repo (ask-ragu): code + docs, public.
- The vault repo (Knowledge base): private, read-only to this system via deploy key.
