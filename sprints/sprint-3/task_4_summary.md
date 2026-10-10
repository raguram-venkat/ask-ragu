# Task 4 — Graph CLI & vault health report

Status: done
Est: 60m
Spec: SPEC.md §14

What: `askragu graph neighbors "<note>"` and `askragu graph health` (dangling links, orphans, alias collisions, biggest hubs).

Approach: Thin CLI over Tasks 1-3; plain-text tables.

Read first:

- Typer or argparse — whichever you already know

Watch out for:

- This is your Sprint 4 debugging tool — make "why was this note reached?" readable.
- Anything surprising in the health output goes to BACKLOG.md, not a rabbit hole.

Done when: Both commands work against the VM DB; health output reviewed.

---

Filled in while working

Files touched:

- `src/ask_ragu/graph/report.py` — `neighbors_report(conn, note)`, `health_report(conn, top)`, plain-text `table()`
- `src/ask_ragu/cli.py` — `askragu graph neighbors "<note>"`, `askragu graph health [--top N]`
- `src/ask_ragu/graph/resolve.py` — `aliases()` made public (shared with the health report)
- `tests/test_report.py` — both reports on a hand-built graph: dangling, orphans, same name, alias claimed twice, alias shadowed by a name, MOC size, tag over the cutoff, "why" texts, unknown note
- `BACKLOG.md` — 2 findings from the real-vault output

Decisions made here:

- The reports are functions returning text from a connection, and the CLI only prints them. That makes them testable on the fixture schema, and Sprint 4's `/search` debug endpoint can reuse them.
- `neighbors` takes the note as you'd link it: it goes through Task 1's resolver (name, path, alias, case-insensitive), and the header shows which path was picked.
- The "why" column reads from the earlier note's side: "linked from X", "links to X", "MOC of X", "listed in X", "shares MOC M with X", "shares #tag with X". Weight is shown only for hub edges.
- MOC sizes in `health` come from the same `child` edges expansion uses (hubs.EDGES), so the report can't disagree with traversal. Tag rows say whether the tag is still a hub under `GRAPH_TAG_HUB_MAX_SHARE`.
- Orphans are notes with no links in or out, self-links ignored. Tags don't count.
- No `--hops`/`--fanout` flags: the CLI uses `.env` like the app. Add them if Sprint 4 debugging needs to compare settings quickly.

Gotchas:

- Real vault (laptop DB; the VM DB waits for the A1, D-008): 2 dangling, 2 orphans (both meta notes), 0 name/alias collisions. The biggest MOC has 42 members and the biggest tag 5.6% of notes, so all tags are hubs.
- Both dangling links are an escaped pipe in a Markdown table (`[[Note\|alias]]`), which Obsidian resolves: a parser bug (BACKLOG). Obsidian's unresolved count is probably 0.
- In real neighbour output, the seed's parent MOC is expanded at hop 2 and brings back siblings the fan-out cut at hop 1 (BACKLOG, Sprint 4).
- Output contains titles and paths: terminal only, never in git or task files.
