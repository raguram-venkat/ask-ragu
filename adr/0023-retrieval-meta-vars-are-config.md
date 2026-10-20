# ADR-0023: Retrieval meta-variables are config, not code

- Status: accepted
- Date: 2026-10-20
- Tags: config, retrieval, settings

## Context

`fuse.py` and `assemble.py` carried hardcoded module constants that control retrieval
behavior: `RRF_K` (the RRF denominator), `TOP_K` (seeds passed to expansion),
`EXPANDED_BUDGET_SHARE` (max budget share for expanded chunks), and `CHARS_PER_TOKEN`
(the chars-per-token estimate for budget arithmetic). Each is a tunable whose value
is a project decision, not an implementation detail, yet changing any one required a
code edit and a redeploy.

## Decision

Move all retrieval meta-variables into `settings.py` (backed by `.env`), alongside the
existing `RETRIEVAL_*` settings. The constants `RRF_K`, `TOP_K`,
`EXPANDED_BUDGET_SHARE`, and `CHARS_PER_TOKEN` are removed from their modules and read
from `settings.retrieval_rrf_k`, `settings.retrieval_seed_top_k`,
`settings.retrieval_expanded_budget_share`, and `settings.retrieval_chars_per_token`.

SQL query strings, the `NOTE_TYPE_PRIOR` lookup table (a structural decision per
D-006, not a scalar knob), regex patterns, and version constants stay in code.

## Alternatives considered

- **Keep as module constants**: tuning requires a code change and redeploy, and the
  values are invisible to operators who only read `.env`.
- **Separate config file**: adds a second source of truth, another parse path, and no
  benefit over reusing the `.env` → `settings.py` pipeline that already exists.
- **Move only some constants**: partial application creates inconsistency — some
  tunables in `.env`, some in code — without a clear rule for which.

## Consequences

All retrieval meta-variables are in one place (`settings.py` / `.env`), visible to
operators and testable via monkeypatch. Tests pin their own values so `.env` changes
cannot break them. The ADR row is linked from `sprints/sprint-4/task_4_summary.md`.
