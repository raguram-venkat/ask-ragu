# ADR-0017: Index freshness — settings hash + code versions, one index per schema

Status: accepted
Date: 2026-10-06
Sprint: sprint-2 (task_8)

## Context

Git diffs only see vault changes. A change to an index setting in `.env` (D-010) or to the parser/chunker code changes what *should* be in the DB for the same commit, yet an incremental sync does nothing, and a full index skipped unchanged rows before rewriting their links/tags. Separately, Sprint 4's ablation needs several index configurations side by side.

## Decision

`index_state.settings_hash` covers two groups defined once in `full.py`: EMBED (`EMBED_VERSION`, chunk/model settings; also inside every note's `content_hash`) and PARSE (`PARSE_VERSION`, folder→type, exclusions, stripped fences). Any difference → full index; EMBED re-embeds, PARSE rewrites only rows whose output changed (a per-note `meta_hash` over links + tags makes link/tag-only changes visible). Versions are integers bumped by hand, enforced by a golden test that pins the parser/chunker output on sample notes per version, and also stored as readable `index_state` columns. Configurations coexist as separate Postgres schemas (one index each), never as versioned rows.

## Alternatives considered

- Manual `askragu index --full` after a change — silent staleness the day someone forgets; never run by hand once deployed.
- The app's git SHA as the code version — every README commit would force a full re-index.
- Versions as their own comparison, outside the hash — two mechanisms that can disagree; the hash already decides, the columns only explain.
- Versioned rows (a version column on chunks/notes/links/tags) so configs coexist and can be picked per query — every key and query gains a filter, incremental sync must maintain all versions, `vector(384)` can't hold another model's dimension anyway; schemas give coexistence for free.

## Consequences

- No manual re-index step for settings or code changes; the log names the reason (model / code version / `.env`).
- Forgetting a version bump fails `tests/test_index_versions.py` with the exact bump to make; a refactor with identical output needs no bump.
- Adding `EMBED_VERSION` changed every `content_hash` once (one full re-embed, ~2 min on the laptop).
- Sprint 4 experiments: create a schema, `SET search_path`, migrate, full index with env overrides, evaluate.
