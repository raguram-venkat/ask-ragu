# Task 4 — Heading-aware chunker + fixture vault

Status: todo
Est: 90m
Spec: SPEC.md §8, §14

What: Split cleaned bodies into chunks along heading boundaries with `heading_path` ("Note > H2 > H3"), max-size splitting and a stub filter — plus the synthetic fixture vault every test uses.

Approach: Walk headings as a stack; oversize sections split on paragraph boundaries with a small overlap; heading-less notes fall back to paragraph windows; merge sections too small to stand alone into a neighbour; skip whole notes under the stub threshold (Task 1 found dropping small sections loses 17% of them).

Read first:

- markdown-it-py token stream (reliable headings and fences vs regex)

Watch out for:

- Headings inside code fences aren't headings.
- Embed `title + heading_path + text`, not bare text — a chunk titled "Pros and cons" means nothing alone.
- Fixture vault is synthetic (public repo), ~15 notes: aliases, same name in two folders, a MOC, a template file, callouts, a huge heading-less note, dangling links, links inside code.

Done when: Chunker tests pass; every chunk ≤ max size; no empty chunks.

From Task 1 profiling (real vault, `scripts/profile_vault.py`):

- Chosen: chunk max 1,500 chars; stub min = note body under 100 chars (note level, SPEC §14).
- Section body sizes: median 381, p95 1,388, max 4,949 chars. Only 94 of 2,483 sections exceed 1,500, so splitting is the rare path.
- Small sections are common: 428 under 80 chars, 77 completely empty (heading directly followed by a subheading). **Merge small sections into a neighbour instead of dropping them**, and fold empty parents into `heading_path`.
- Headings are only H2 and H3 (no H1; title is the filename), so `heading_path` is at most "Title > H2 > H3".
- 747 notes have nothing before the first heading; 29 do (preamble text that needs its own chunk or must be merged into the first section).
- 25 notes have no headings; only one is big (~7.7k chars), so the paragraph-window fallback is rare but real.
- Fixture vault: include a Markdown image `![](Attachments/x.png)` and a note with no frontmatter. Drop "huge heading-less note" down to ~8k chars; that's the real worst case.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
