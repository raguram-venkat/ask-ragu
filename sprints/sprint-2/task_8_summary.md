# Task 8 — Incremental sync & reconciliation

Status: todo
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

- 

Decisions made here:

- Files on disk move forward with the commits: fetch → diff `<last_commit>..origin/<branch>` → `git reset --hard origin/<branch>` → index the diffed paths from disk → advance last_commit last. `git fetch` alone only updates `.git/`, and the indexer reads files from disk. Hard reset is safe: the sync is the clone's only writer, and it also lands force-pushes. A crash between reset and last_commit means the next run re-diffs from the old commit, which is harmless (idempotent).
- The VM's clone lives in a named volume (`vault:/vault`), not in the container's filesystem, so it survives rebuilds and deploys (SPEC §11).
- Open: first clone. An empty volume needs a one-time `git clone` (via the deploy key), e.g. at startup when `/vault/.git` is missing. Owned by this task or the deploy task, to be decided.
- Laptop: `compose.override.yml` mounts the vault read-only, so fetch/reset can't write there. The local sync must skip fetch/reset (or test against a writable scratch clone).

Gotchas:

- 
