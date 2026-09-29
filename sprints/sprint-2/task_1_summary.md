# Task 1 — Vault profiling (data before design)

Status: todo
Est: 60m
Spec: SPEC.md §7, §8

What: A throwaway script reporting the vault's real shape: notes per folder, size distribution, headings per note, links and embeds per note, frontmatter keys, callouts, code-block languages, largest notes.

Approach: Run on the laptop against the local vault; record the numbers below. They set the chunk max size, the stub threshold, and the tag cutoff — no guessing.

Read first:

- Obsidian help: Internal links, Properties

Watch out for:

- Notion-imported topics were flattened into big single files — expect a long tail of huge notes; count how many have no headings.
- Old attachment paths from before the migration still point at the vault root — confirms embeds must be skipped, not resolved.
- Count `[[...]]` inside code blocks separately; those must never become links.

Done when: Findings table below filled; chunk max, stub min, and tag cutoff chosen from it.

## Findings

| Metric | Value |
|---|---|
| Notes per folder | |
| Median / p95 / max note size | |
| Notes with no headings | |
| Links per note (median / max) | |
| Distinct tags / most common tag share | |
| Chosen: chunk max · stub min · tag cutoff | |

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
