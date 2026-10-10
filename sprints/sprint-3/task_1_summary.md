# Task 1 — Link resolution & alias map

Status: done
Est: 90m
Spec: SPEC.md §7, §14

What: Resolve every note_links.raw_target to a note id using Obsidian's rules, re-run over all links after each index run.

Approach: Lookup from basenames, frontmatter aliases, and path suffixes, case-insensitive; if several notes share a name, use the path the link gives, else Obsidian's shortest-path rule; unresolved stays NULL (dangling).

Read first:

- Obsidian help: Internal links, Aliases

Watch out for:

- Re-resolve globally every run (cheap at this scale): a new note can fix old dangling links; a `git mv` outside Obsidian can break links in unchanged notes.
- Strip `#heading`, `#^block`, `|alias` before matching; keep the heading — it could target a chunk later.
- Two notes claiming one alias: deterministic tie-break plus a warning.
- Self-links aren't edges.

Done when: Fixture assertions pass; the real vault's dangling count roughly matches Obsidian's unresolved-links view.

---

Filled in while working

Files touched:

- `src/ask_ragu/graph/resolve.py` — `resolver(notes)` (pure rules) and `resolve_links(conn)` (one `UPDATE … FROM unnest(...)` over all distinct raw targets)
- `src/ask_ragu/index/sync.py` — `sync()` calls `resolve_links` after every run, noop included, under the sync lock
- `tests/test_resolve.py` — rule cases: same name in two folders, path-qualified links, `.md` suffix, case/space, NFD vs NFC, aliases (list and string), alias collision, alias vs filename, dangling
- `tests/test_sync.py` — DB case: a new note fixes a dangling link, and a rename or delete breaks links in unchanged notes
- `SPEC.md` §8, §14, `DEVIATIONS.md` — D-012

Decisions made here:

- Resolution doesn't depend on the source note (no same-folder or relative-path rule), so each distinct `raw_target` is resolved once (Python, ~2.7k strings) and written in one statement. Only rows whose target changed are updated.
- Order: a name or path-suffix match (`[[Note]]`, `[[Sub/Note]]`, `[[Note.md]]`) wins over an alias. Several matches → fewest folders, then alphabetical path, plus a warning. That's deterministic, so a full index and an incremental sync reach the same result (D-012, replacing SPEC's last-write-wins).
- A path that doesn't exist (`[[Other/Note]]`) stays dangling and doesn't fall back to the name.
- A self-link resolves to its own note rather than NULL, so NULL means dangling and nothing else. It adds no edge in traversal (the note is already at hop 0).
- Resolution isn't a PARSE_VERSION change: it runs on every sync, so a resolver code change applies at the next startup.
- Real vault at the current commit: 2,658 resolved, 2 dangling, 1 self-link (an independent SQL count gives the same numbers).

Gotchas:

- The Sprint 2 handoff numbers are stale: the vault now has 0 duplicate basenames (it had 54 links to them) and 2 dangling links (it had 9). The tie-break rules are tested only on fixtures.
- Obsidian inserts alias links as `[[Real Name|Alias]]` (help: Aliases), so a bare `[[Alias]]` probably shows as unresolved in Obsidian, yet resolves here. The owner kept the alias fallback (review, 2026-10-10).
- The Obsidian help pages don't document the same-name tie-break. The owner chose "fewest folders wins" (the outer note over a nested one) whether or not Obsidian does the same (review, 2026-10-10).
