# ADR-0022: Dev agents on open-weight models see public-repo content only

Status: proposed — resolve before sprint-4/task_7's bake-off
Date: 2026-10-13
Sprint: sprint-4 (task_7)

## Context

From 2026-10-13 development moves from Claude Code to an open-source agent harness driving hosted open-weight models (the laptop can't run a coding model: 7 GB RAM, no GPU). A coding agent sends every file and command output it reads to its model provider, and free open-model endpoints often log or train on prompts, differently per endpoint.

## Decision

Each dev provider/endpoint is classed `vault-safe` (documented no training and no retention beyond abuse monitoring, source and date recorded in sprint-4/task_7) or `public-only`. With a `public-only` provider the agent never reads `.env`, `eval/*.private.*`, the vault clone or note content from the DB, and never runs a command whose output includes vault text (labelled in `scripts/README.md` and AGENTS.md); the owner runs those and passes back aggregates only. Aggregate-only commands (tests, `bench_expansion.py`, `scan_vault_leaks.py`, latency numbers) are allowed.

## Alternatives considered

- Trust any free provider — the vault becomes training data, the same harm ADR-0009 prevents for the app.
- No real-vault work by agents at all — too strict: index builds, latency and eval aggregates need the real index, and they're safe when the output is numbers only.
- Self-host the dev model — impossible on the laptop.

## Consequences

- The owner runs the vault-printing commands personally (`askragu graph neighbors`, `profile_vault.py`, ad-hoc searches, eval per-question output).
- The pre-commit/pre-push title scan prints file:line and counts, never titles (`scripts/scan_vault_leaks.py`).
- A vault-safe provider, once verified, lifts the restriction for that provider only; re-verify when its terms change.
