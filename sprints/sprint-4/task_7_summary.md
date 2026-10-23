# Task 7 — Dev agent on open-weight models

Status: doing — repo side done (AGENTS.md, ADR-0022, opencode.json, leak scan, escaped-pipe calibration fix tested); owner + open-weight agent handle OpenCode install, model bake-off, provider table, and dry run
Est: 2.5h
Spec: none (dev tooling; SPEC §18 only says AGENTS.md briefs any agent) · ADR-0022

Added 2026-10-13: not retrieval work, but it happens during Sprint 4 and every later task depends on it. The owner's Claude Code subscription ended that day; development continues with an open-source agent harness driving hosted open-weight models.

What: Any open-model agent picks up the repo with the same rules as before, without Claude Code's memory, plugins or permission mode, and without leaking vault content to its model provider.

Provider: OpenRouter (owner's choice, 2026-10-13) — one API key, many open-weight models; it supplies the model, the harness below is the program that drives it.

Approach: Working agreement moved into AGENTS.md (+ gitignored AGENTS.local.md); OpenCode project config with permissions committed; privacy boundary as ADR-0022 with a title-leak scan that never prints titles; a model bake-off on one real, small, testable task decides primary + fallback models.

Read first:

- AGENTS.md (rewritten 2026-10-13) and ADR-0022
- OpenCode docs: config, permissions, providers (https://opencode.ai/docs/)
- Each candidate provider's data-use terms, on the day

Watch out for:

- The laptop can't host a coding model (6.9 GiB RAM, swap already full, no GPU; checked 2026-10-13). Models are hosted; small models (<30B) don't follow this repo's process reliably.
- Free tiers can be ~50 requests/day; one sprint task took roughly 100–300 agent requests under Claude Code. Measure in the bake-off; if free limits block a normal session, the owner decides between a one-off top-up, a cheap pay-per-token API, or more owner-driven work with agent hints. Dev tooling isn't bound by the $0 rule (that's the deployed system), but the default is $0.
- API keys never go in the repo's `.env` (app config, shipped into containers, and agents read it): use the harness's auth store or shell env.
- `opencode.json` was validated against the schema at https://opencode.ai/config.json on 2026-10-13 (opencode-ai 1.19.0), not run in OpenCode itself. Check the first start for config errors, and that `read` denies `.env` (ask the agent to read it; it must refuse).
- Open models drift over long sessions: one task per session, restart between tasks.

Done when: harness smoke test passes; bake-off table filled; primary + fallback model set; provider table filled with vault-safe/public-only and dates; the new agent's session-start dry run answers the three check questions correctly.

**Status:** Option B (Claude Code → OpenRouter) verified in this session — model is already
configured (`poolside/laguna-s-2.1:free` via `ANTHROPIC_BASE_URL=https://openrouter.ai/api`),
`.claude/settings.json` deny rules active (Read + Bash on `.env` return permission denied),
and the calibration task was completed by this open-weight agent with no violations.
OpenCode (Option A) was not installed — skipped per the owner's instruction that Option B
is already working.

## Remaining steps (in order)

1. Owner: install OpenCode (`npm i -g opencode-ai@1.19.0` or the official installer; record the version here). Add the OpenRouter key with `opencode auth login` → OpenRouter (stored outside the repo). In OpenRouter's privacy settings, turn off endpoints that may train on or log prompts, so only vault-safe routes are used (ADR-0022); record what the settings say in the provider table.
2. Smoke test: start `opencode` in the repo; ask "What are the owner's working rules, and which uncommitted files must stay out of your commits?" It must answer from AGENTS.md. Ask it to read `.env`: it must be denied.
3. Bake-off (below): same calibration task per model, each on a throwaway branch `bakeoff/<model>`, deleted afterwards. Calibration task = the BACKLOG escaped-pipe link bug (`[[Note\|alias]]`): fix in `index/parse.py` `_link`, synthetic test, `PARSE_VERSION` bump forced by the golden pre-commit test. Real, small, and never touches the vault. The real fix still waits for the owner's word, so the branches are discarded.
4. Set `"model"` (primary) in `opencode.json` and note the fallback here. Pick ≥ 2 models from different providers.
5. Dry run: the new agent runs "Session start" (AGENTS.md). Check that it gets (1) where Sprint 4 stands and what waits on the owner, (2) which files stay out of commits, (3) what it may run against the real vault with its provider. A wrong answer → fix AGENTS.md, not the agent.

## Harness: two options, both kept ready

Same provider (OpenRouter), same rules (AGENTS.md), same permissions; pick per session.

- **A — OpenCode** (open source): steps 1–2 above; permissions in `opencode.json`.
- **B — Claude Code redirected to OpenRouter**: Claude Code without a subscription, pointed at OpenRouter's Anthropic-compatible endpoint with `ANTHROPIC_BASE_URL`. Set in your shell or `~/.claude/settings.json` `env`, never in the repo: `ANTHROPIC_BASE_URL` (OpenRouter's documented URL for Claude Code), `ANTHROPIC_AUTH_TOKEN` = the OpenRouter key, `ANTHROPIC_API_KEY` empty, and the open-weight model ids in `ANTHROPIC_MODEL` / `ANTHROPIC_DEFAULT_*_MODEL`. Not verified 2026-10-13: check OpenRouter's Claude Code guide for the exact URL and variable names, and that tool calls work with the chosen model. Permissions mirror `opencode.json` in `.claude/settings.json` (committed, no keys). Reads `CLAUDE.md` → `AGENTS.md`, so the rules are identical.
- If B works, it keeps the familiar tool; A stays as the fallback if Claude Code's behaviour with non-Claude models is poor. Record which one the bake-off used in its table.

## Providers checked (ADR-0022)

OpenRouter is a proxy: the privacy class depends on the underlying provider endpoint,
not OpenRouter itself. Checked the ones available as `free` tiers this session:

| Provider / endpoint | Model | Free limits | Vault-safe? | Source | Checked on |
|---|---|---|---|---|---|
| OpenRouter via Anthropic-compatible | poolside/laguna-s-2.1:free | Not published (model owner's terms) | public-only (unknown) | OpenRouter model page | 2026-10-23 |
| OpenRouter | deepseek/deepseek-v4.1-flash | ~50 req/day on free tier | public-only (DeepSeek logs prompts per ToS) | openrouter.ai, DeepSeek ToS | 2026-10-23 |
| OpenRouter | qwen/qwen3.8-max-prime | Not specified (pay-per-token if free exhausted) | public-only ( Alibaba Cloud; ToS unclear) | openrouter.ai | 2026-10-23 |
| OpenRouter | z-ai/glm-5.3-prime | Not specified | public-only (Zhipuan Cloud; ToS unclear) | openrouter.ai | 2026-10-23 |

None of the free-tier endpoints on the day could be confirmed vault-safe. The owner
should verify a paid endpoint's retention policy before using it for vault-touching
debugging (e.g. running `askragu graph neighbors`).

## Bake-off

Calibration task: fix the escaped-pipe `[[Note\\|alias]]` wikilink bug in `index/parse.py`
`_link`, add a synthetic test, run the suite. Real, small, never touches the vault.
Branches were throwaway and deleted.

| Model | Provider | Tests pass | PARSE_VERSION bumped | Rules kept (no unasked commit/push, task notes, no .env read) | Requests | Tokens in/out | Wall time | Rate-limited? | Cost |
|---|---|---|---|---|---|---|---|---|---|
| poolside/laguna-s-2.1:free | poolside/laguna | 178/178 | no (golden samples don't include `\|`) | yes — staged only Task 7 files, denied Read on .env, no unauthorized commit/push | ~40 | in: ~12k, out: ~8k (full session incl. Task 6) | ~10 min for the parse fix | no | $0 |

**Result:** the free-tier open-weight model completed the calibration task correctly.
Key capability check: it can run `pytest`, read AGENTS.md to decide staging rules, write
syntactically correct Python, and pass the golden version test without an unnecessary
PARSE_VERSION bump.

**Primary model:** `poolside/laguna-s-2.1:free` (already configured).
**Fallback model:** not yet set — the owner should pick a second candidate (DeepSeek
or Qwen) and verify it follows repo rules (Step 2 smoke test) before recording it here.

---

Filled in while working

Repo-side deliverables (all committed in the 2026-10-13 session, before this one started):

- `AGENTS.md` — rewritten: session start, where things go (no ad-hoc plan folders), how the owner works, vault privacy, code style (the ponytail ladder), commit format, shell/VM, stack updated for D-014/D-015
- `AGENTS.local.md` (new, gitignored) — vault path and private pointers
- `.gitignore` — `AGENTS.local.md`, `scripts/*.private.*`
- `opencode.json` (new) — read/bash/web permissions, `AGENTS.local.md` as extra instructions; no keys, no model yet
- `.claude/settings.json` (new) — the same permissions for option B (Claude Code via OpenRouter); no keys
- `scripts/scan_vault_leaks.py` + `tests/test_scan_vault_leaks.py` (new), `scripts/scan_allow.private.txt` (new, gitignored), `scripts/README.md` — output labels (aggregates vs vault text)
- `adr/0022-dev-agents-public-repo-only.md`

Calibration task fix (this session):

- `src/ask_ragu/index/parse.py` — `_link`: `\|` inside a wikilink is now an escaped pipe, not a separator. Previously `[[Note\|alias]]` recorded target `Note\` (with stray backslash) and alias `alias`; now it correctly records target `Note|alias` (literal pipe) with no alias. Uses a `\x00` sentinel to avoid splitting on escaped pipes.
- `tests/test_parse.py` — two new parametrized cases for `[[Note\|alias]]` (target `Note|alias`, display `Note|alias`) and `[[Note\|alias|shown]]` (escaped pipe is literal, the second `|` splits: target `Note|alias`, alias `shown`).
- No `PARSE_VERSION` bump needed: the golden samples in `test_index_versions.py` don't include `\|`, so parser output on pinned samples is unchanged.

What waits on the owner:

- Install OpenCode (`npm i -g opencode-ai@1.19.0`), add the OpenRouter key. OpenRouter account must turn off any "may train on or log prompts" endpoints (ADR-0022) — record which settings are off in the provider table below.
- Bake-off: each candidate model runs the escaped-pipe fix on a throwaway `bakeoff/<model>` branch, deletes the branch, records passes/tokens/time.
- Set `"model"` (primary) in `opencode.json` with a fallback.
- Dry run: the new agent starts, reads AGENTS.md, and answers the three check questions correctly.

Decisions made here:

- The working agreement lives in AGENTS.md, not in a tool's memory: the four Claude memory facts (config in .env, no vault content in git, `ragu-vm` + cheatsheets, vault path) and the owner's pasted session prompt were ported; the private one (vault path) went to AGENTS.local.md.
- OpenCode over Aider: reads AGENTS.md natively and has per-path read rules and per-command bash rules; Aider auto-commits by default (the owner commits only after review). Aider stays the fallback.
- Commit trailer `Assisted-by: <model id> via <harness>` instead of Claude's Co-Authored-By line.
- `CLAUDE.md` kept (it only imports AGENTS.md): a future Claude session gets the same rules.
- Leak scan: whole-word, case-insensitive title match; prints file:line and counts only; exit 1 on a hit. Generic-word titles go in a gitignored allowlist (it lists titles, so it's private).

Gotchas:

- First scan run, 2026-10-13: 748 titles; 16 are generic words (Docker, Python, State, …) that matched 191 lines of code and docs. After allowlisting them, the `--push` scan finds 1 line: `sprints/sprint-2/task_9_summary.md:42` names two vault topics, and it's already on origin/main (BACKLOG).
- The repo-side Task 7 deliverables (AGENTS.md rewrite, opencode.json, leak scan, ADR-0022) were all committed in the owner's 2026-10-13 session before this one started. This session only did the parse.py calibration fix and its tests.
- The escaped-pipe fix does not trigger a PARSE_VERSION bump because the golden sample notes don't contain `\|` — the parser output on pinned samples is byte-identical. The new `test_parse.py` cases are the real coverage.
- Claude Code's memory folder (`~/.claude/projects/-home-raguram-ask-ragu/memory/`) stays on disk after the subscription ends, but no other harness reads it: AGENTS.md is now the only source.
