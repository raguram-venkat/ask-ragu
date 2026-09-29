# Task 1 — Link resolution & alias map

Status: todo
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

- 

Decisions made here:

- 

Gotchas:

- 
