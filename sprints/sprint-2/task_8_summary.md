# Task 8 — Incremental sync & reconciliation

Status: done
Est: 90m
Spec: SPEC.md §8 · ADR-0004

What: Sync = `git fetch` + `git diff --name-status --find-renames -z <last_commit>..origin/<branch>`, applying adds, modifies, deletes, and renames; startup runs one sync.

Approach: Renames update notes.path in place (id kept); deletes cascade; modifies re-embed only if the hash changed; then advance last_commit. /index/status shows last commit, last run, counts, errors.

Read first:

- git diff --name-status, --find-renames, -z
- git merge-base --is-ancestor

Watch out for:

- Force-push: last_commit missing or not an ancestor → full index.
- Empty index_state → full index.
- Rename + edit in one commit shows as `R0xx` — still a rename.
- Spaces and unicode in paths: parse `-z` output, never split lines.

Done when: Scripted scenario on a scratch repo (add, edit, rename, delete, force-push) ends with DB == full-index result.

---

Filled in while working

Files touched:

- `src/ask_ragu/index/sync.py` — `target_commit`, `changes` (parses `git diff -z`), `sync`, the shared `runner`
- `src/ask_ragu/index/full.py` — reads notes **at a commit** via one `git cat-file --batch` (`read_blobs`) instead of the working tree; `index_note`/`index_paths`/`record_state` shared with sync; `Stats` gains `mode` and `renamed`
- `src/ask_ragu/index/runner.py` — `running` + `last` (outcome of the last run) for status
- `src/ask_ragu/api/status.py`, `main.py` — `GET /index/status`; startup triggers one sync (reconciliation)
- `src/ask_ragu/api/webhook.py` — uses the shared runner (the Task 7 full-index placeholder is gone)
- `src/ask_ragu/cli.py` — `askragu index` = incremental, `--full` = full
- `tests/test_sync.py` — origin + clone scenario, DB compared with a fresh full index after every step; `tests/test_webhook.py` — runner outcome, `/index/status`
- `src/ask_ragu/settings.py`, `.env.example` — `VAULT_REF`, `VAULT_FETCH`
- D-010 follow-up: `migrations/0003_index_settings_hash.sql` (nullable `index_state.settings_hash`); `full.py` — `embed_settings()` / `parse_settings()` / `settings_hash()`, `content_hash` built from the EMBED group, `record_state` writes the hash; `sync.py` — `sync(conn, vault, full=False)` single entry point, `_full_index_reason`, `_update_working_tree`; `cli.py` — `--full` goes through `sync`; `status.py` — `settings_current`; `tests/test_sync.py` — 21 new cases; `.env.example` comments; `SPEC.md` §7/§8, `DEVIATIONS.md` (D-010), `adr/0004…` (amended line), `INDEX.md`

- Round 3 (code versions + lock): `migrations/0004_index_code_versions.sql` (`notes.meta_hash`, `index_state.embed_version/parse_version`); `full.py` — `EMBED_VERSION`/`PARSE_VERSION` in the hash groups, `meta_hash` in the upsert; `sync.py` — `sync_lock` (advisory lock), full-index reason names model / code version / `.env`; `status.py` — `code_versions`; `tests/test_index_versions.py` (golden fingerprints); `tests/test_sync.py` — lock + version cases; `tests/conftest.py` — `connect` fixture for extra connections; `.pre-commit-config.yaml` — golden-test hook; `adr/0017…`, `adr/0018…`, `DEVIATIONS.md` (D-010 extended, D-011), `SPEC.md` §6/§7/§8/§13, `INDEX.md`, `BACKLOG.md`, `sprints/sprint-4/task_5_summary.md`

Decisions made here:

- The indexer never reads the working tree: content comes from git objects at the target commit (`git cat-file --batch`, one process for all files). Full and incremental index therefore see exactly the same input, and the read-only laptop mount works. (Replaces Task 6's working-tree read and its "uncommitted changes" warning.) The index never depends on the working tree, but on the VM the files on disk are kept in step anyway — see the D-010 follow-up below.
- Which commit: `VAULT_REF` after an optional `git fetch` (`VAULT_FETCH`). Laptop: `HEAD`, no fetch (the mount is read-only and it's your working clone). VM: `VAULT_FETCH=true`, `VAULT_REF=origin/main`. Not `origin/HEAD`: only clones made with `git clone` have it (your laptop clone doesn't).
- Full-index fallback when: no `index_state`; the index settings in `.env` changed (`settings_hash`, D-010 follow-up below — replaces the earlier `embedding_model` comparison); `last_commit` is not an ancestor of the target (`git merge-base --is-ancestor`, which also fails when the commit is gone after a force-push); or the incremental diff itself fails (the index is disposable, ADR-0011, so a full index repairs it instead of failing on the same diff at every retry). Changing an index setting in `.env` (chunking, model, folder types, exclusions, …) needs no manual step: the next sync sees a different `settings_hash` and runs a full index by itself. `askragu index --full` remains for forcing one.
- Diff handling: renames → `UPDATE notes SET path` (id kept) then re-index the new path (title/body may have changed with it); rename into or out of an excluded folder = delete or add; deletes cascade; adds/modifies go through the same `index_note` as the full index, so unchanged content isn't re-embedded. Renames + deletes in one transaction; `last_commit` advances last.
- Startup reconciliation = `runner.trigger()` in the lifespan: non-blocking, so the app is up while it catches up.

- D-010 follow-up 1 — settings hash. Index settings live in `.env`, so changing one produces no git diff: an incremental sync did nothing and the DB silently kept chunks built with the old settings (only a model change was caught). Now `index_state.settings_hash` records them and any difference forces a full index. The settings are defined once, in two groups in `full.py`:
  - EMBED (`embed_settings()`): chunk max/merge/overlap, stub min, metadata headings, embedding model/file/pooling — what chunks and vectors depend on. `content_hash` = title + body + EMBED, value unchanged from before (a test pins the old formula), so the upgrade re-embeds nothing.
  - PARSE (`parse_settings()`): `VAULT_FOLDER_TYPES`, `VAULT_DEFAULT_NOTE_TYPE`, `VAULT_EXCLUDED_DIRS`, `VAULT_STRIPPED_FENCES` — they change rows, not vectors. A PARSE-only change is a full index that rewrites the affected rows and embeds nothing (stripped fences reach `content_hash` through the body, so only notes whose body actually changes re-embed).
  - `settings_hash` = EMBED + PARSE. Sets/dicts are sorted, so `.env` ordering doesn't matter. Left out: runtime knobs that don't change output (`EMBEDDING_BATCH_SIZE`, `EMBEDDING_CACHE_DIR`, `EMBEDDING_QUERY_PREFIX` — query side only), webhook settings, and `VAULT_PATH`/`VAULT_REF`/`VAULT_FETCH` (they choose the input; a different repo or ref shows up as "not an ancestor" → full index anyway). A test asserts each setting lands in exactly the right group.
  - `EMBEDDING_DIM` is deliberately not in EMBED: it's fixed by the model (changing the model already changes the hash), and a wrong value fails loudly at model load. Adding it would have changed every `content_hash` and re-embedded the vault on upgrade for no gain.
  - `embedding_model`/`embedding_dim` columns stay (status, logs). The full-index log line names the reason, and the model change when that's the part that changed.
  - NULL `settings_hash` (an index from before 0003) counts as a mismatch: one full index after upgrading, embedding nothing.
- D-010 follow-up 2 — working tree. The indexer still reads git objects, but on the VM the clone's files would otherwise stay at the commit it was cloned at, so anything reading files there sees stale notes. After every successful sync — full, incremental and noop (so a fresh or lagging clone catches up) — and after `record_state`, the clone is `git reset --hard <commit just indexed>`. Constraints:
  - Only when `VAULT_FETCH=true`, i.e. the clone belongs to the system. Never on the laptop (`VAULT_FETCH=false`): `/vault` is your Obsidian working clone, mounted read-only.
  - Skipped with a warning if tracked files have local edits (`git status --porcelain --untracked-files=no`): someone is using that clone by hand, and a reset would wipe their work. Untracked files are never touched (no `git clean`).
  - A failed reset logs a warning and does not fail the sync: the index is already correct.
  - One entry point: `askragu index --full` now goes through `sync(full=True)`, so the reset happens in exactly one place for every path (CLI, webhook, startup).

- Round 3 decisions (owner + agent, 2026-10-06), so none of this bites later:
  - Serialization: every sync, from any process, runs under one Postgres advisory lock for its whole run (fetch → diff → index → state → working tree); a second sync waits, then reads the newest target itself (usually a noop). No queue of individual requests: a sync always goes to the newest commit, so the in-process runner's dirty flag (one follow-up run) already covers any number of pushes. Lock is session-level (a sync is many transactions), keyed by schema, no timeout (a crashed holder's connection closes and Postgres frees it). ADR-0018, D-011.
  - Ablation / coexisting configs: one index per Postgres schema, settings passed as env overrides; rows are never versioned. Recorded in Sprint 4 Task 5. ADR-0017.
  - Code versions: integers `EMBED_VERSION` / `PARSE_VERSION` in `full.py`, starting at 1 (NULL in `index_state` = built before versions existed). They live **inside** the hash groups (the one mechanism that triggers re-indexing) and are **also** stored as readable `index_state` columns (`/index/status` → `code_versions`), next to `embedding_model`. Not the app's git SHA (every README commit would re-index). Bump rule: EMBED for anything that changes chunks or the embedded text (chunker, `passage_text`) → re-embed all; PARSE for anything that changes body/links/tags/type/frontmatter → full index rewriting only changed rows. ADR-0017.
  - Forgetting a bump is caught: `tests/test_index_versions.py` pins the parser's and chunker's output on sample notes per version and fails with the exact bump to make; a refactor with identical output passes untouched. Verified by simulating a `passage_text` change.
  - `notes.meta_hash` (links + tags) is compared on upsert, so a parser change that only alters links/tags rewrites them; before, a full index skipped such rows. NULL on existing rows → rewritten once.
  - How a running system notices a code change: it can't change inside a process (modules load once at start), so new code means a rebuild + restart, and the startup reconciliation sync compares `settings_hash()` (now with the new version) against `index_state` before any push arrives. Every later sync (webhook, CLI) compares again. The golden test guards the step before that: a pre-commit hook (`.pre-commit-config.yaml`, `index-code-versions`) runs it whenever `parse/chunk/embed/full.py` change, so an output-changing commit can't land without its bump (until CI exists, Sprint 6). Verified: a simulated `passage_text` change fails the hook with the bump to make.
  - Dropped: the "content_hash value unchanged" test from round 2 — adding `EMBED_VERSION` changes it by design (one re-embed).

Gotchas:

- Real-vault replay (read-only, scratch schema, fake embedder): full index at the first commit, then `sync` through all 7 later commits → notes, chunks, links, tags **identical** to a full index at HEAD (748 / 1,965 / 2,660 / 744). The last commit modified 758 files but only 28 notes re-embedded (the rest were frontmatter-only edits). Of git's 201 renames in one commit, 31 were notes; the rest were attachments/excluded files.
- git's rename detection needs ≥ 50% similar content: a tiny note with a one-character edit shows up as delete + add (new id). Real notes (~1.5k chars) are fine; the test uses a multi-line note for this reason.
- `git diff --name-status -z` emits `R087\0old\0new` (three fields) for renames and `M\0path` (two) otherwise; parse field by field, never by lines.
- Live stack: startup sync ran (`last_sync` = noop), `askragu index` = noop, `/index/status` reports commit, model, counts, running flag and the last outcome.
- On the VM: the system's clone must be writable (fetch, and the D-010 reset) and reachable with the deploy key (Sprint 1 Task 5), and its `.env` needs `VAULT_FETCH=true`, `VAULT_REF=origin/main`.
- D-010 live check (real vault): migration 0003 applied at startup; startup sync logged "no settings hash recorded (index built before migration 0003)" and ran a full index with **0 written, 0 embedded** — `content_hash` values really are unchanged. A one-off PARSE change (`-e VAULT_FOLDER_TYPES=...` mapping Concepts to `source`) → full index, 662 rows rewritten, 0 embedded, 5.6 s; back to `.env` → the same in reverse; next run → noop.
- Not covered by the settings hash (by design): a change to the parser/chunker *code*. `--full` doesn't fix that either, because unchanged rows are skipped before their links/tags are rewritten. Real rebuild = `TRUNCATE notes, index_state CASCADE` + full index (ADR-0011). → BACKLOG (version constant).
- The working-tree reset runs inside the container as root, so on the VM files it rewrites become root-owned on the host. Decide the clone's owner / container user in Sprint 1 Tasks 5–6. → BACKLOG.
- Real env vars beat `.env`, so `docker compose exec -e NAME=value app askragu index` is a cheap way to try a setting once.
- Round 3 live checks: migration 0004 applied at startup → one full index re-embedding all 748 notes (1,965 chunks), as expected; `/index/status` shows `code_versions {embed: 1, parse: 1}`. Two CLI syncs started 0.5 s apart: the second logged "another sync holds the lock; waiting", then ran as a noop after the first finished.
- The first round-3 log said "index settings changed (.env)" when the real cause was the new code versions — fixed: the reason now lists what changed (model / embed code version / parse code version), falling back to ".env index setting".
- `sync.py` reads the versions as `full.EMBED_VERSION`, not a copied import: a copied constant is a second name that can drift (tests had to patch both).
- The VM file-ownership question (reset runs as root in the container) stays in BACKLOG until Sprint 1 Tasks 5–6, by owner decision.
- Editing `.env` does nothing to a running app: compose passes it in when the container is created. `docker compose up -d` recreates the container, and its startup sync then sees the new settings hash. (`docker compose exec -e …` runs a separate process with the override, for a one-off.)
