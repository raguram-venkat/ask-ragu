# Task 1 — Vault profiling (data before design)

Status: done
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

Measured with `scripts/profile_vault.py` (method and the reason for each stat: `scripts/README.md`). Sizes in characters.

| Metric | Value |
|---|---|
| Notes per folder | 776 indexable: concept 682 · moc 71 · source 18 · meta 5 · fleeting 0 |
| Median / p95 / max note size | 1,470 / 4,099 / 9,429 chars (no note over 10k) |
| Section body (under a heading) | median 381 · p95 1,388 · max 4,949; 94 of 2,483 over 1,500; 428 under 80; 77 empty |
| Notes with no headings | 25 (3%); largest is 7.7k chars, the only big heading-less note |
| Links per note (median / max) | 2 / 79 (p95 11; 2,776 total) |
| Distinct tags / most common tag share | 85 / 5.4% — every note has exactly one tag, equal to its `domain` key |
| Chosen: chunk max · stub min · tag cutoff | 1,500 chars · note body < 100 chars · 10% of notes |

---

Filled in while working

Files touched:

- `scripts/profile_vault.py` — read-only, stdlib-only profiler
- `scripts/README.md` — how each stat is measured and what it decides
- `sprints/sprint-2/task_2_summary.md`, `task_3_summary.md`, `task_4_summary.md` — "From Task 1 profiling" sections

Decisions made here:

- Chunk max 1,500 chars (~375 tokens at ~4 chars/token): leaves headroom under bge-small's 512-token limit once `title + heading_path` is prepended, and for code-heavy text. Only 94 sections (4%) need splitting.
- Stub min applies to whole notes, as SPEC §14 says, not to chunks: a note whose body after the frontmatter is under 100 chars is not embedded. Today that drops 1 note.
- Small sections are merged, not dropped: 428 sections (17%) have under 80 chars of body, and dropping them would lose real content. Task 4's approach was changed from "drop chunks under the stub threshold" to merging small sections into a neighbour.
- Tag cutoff 10%: the largest tag covers 5.4% of notes, so nothing is excluded today; the cutoff only guards against a future generic tag. SPEC §7's ">20%" was an example, so this isn't a deviation.

Gotchas:

- Two of the "Watch out for" items didn't match the real vault: there are no huge Notion-flattened notes, and images use Markdown `![](Attachments/...)` syntax, not `![[...]]` and not root paths.
- First pass counted the empty text before the first heading (747 notes) as tiny sections, which made "a third of sections are heading-only" look true. It's 77. Fixed by measuring the preamble separately.
- Parser and chunker facts for later tasks are written into Tasks 2–4 under "From Task 1 profiling".
