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

- 

Gotchas:

- 
