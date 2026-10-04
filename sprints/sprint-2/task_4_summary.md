# Task 4 — Heading-aware chunker + fixture vault

Status: done
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

- `src/ask_ragu/index/chunk.py` — `chunk_note(title, body) -> list[Chunk(heading_path, content)]`; list order = `chunk_order`
- `tests/test_chunk.py` — 9 cases: stub, heading path, heading-only parent, heading in code, preamble, merge + shared path, merge cap, paragraph split + overlap, heading-less giant line
- `src/ask_ragu/settings.py`, `.env.example` — `CHUNK_MAX_CHARS`, `CHUNK_MERGE_BELOW_CHARS`, `CHUNK_OVERLAP_CHARS`, `STUB_MIN_CHARS`

Decisions made here:

- No markdown-it-py: the vault only has `##`/`###` headings (Task 1), so all the chunker needs is "is this line inside a code fence?" — it reuses the parser's `FENCE` regex.
- Merge rule (one condition): a section joins the previous chunk if either is under `CHUNK_MERGE_BELOW_CHARS` and the result fits `CHUNK_MAX_CHARS`. The merged chunk's `heading_path` is the shared prefix; headings not in the path stay in the text (`### A1`), so nothing is lost.
- Merge threshold 200, measured on the real vault (chunks / median / under 200 chars): 0 → 2,555 / 385 / 702 · 80 → 2,219 / 463 / 333 · **200 → 1,992 / 530 / 78** · 400 → 1,565 / 749 / 42. 200 removes almost all fragments; 400 starts mixing unrelated sections.
- Overlap: when a section is split, its last paragraph is repeated at the start of the next window if it's ≤ `CHUNK_OVERLAP_CHARS` (300). Paragraph-level, not a character slice, so no chunk starts mid-word.
- Chunk content excludes its own heading line when `heading_path` already carries it; Task 5 embeds `title + heading_path + content` (title is already the first path element).
- Stub notes (owner confirmed): rows in `notes`, `note_links`, `note_tags`; **no rows in `chunks`** (`embedding` is NOT NULL, so a chunk without a vector can't exist). So a stub is neither vector- nor keyword-searchable; it can only enter an answer via graph expansion from a linked note. Task 6 must upsert the note even when `chunk_note` returns `[]`. Alternative kept in mind: one unsplit, embedded chunk per stub, if stubs ever need to be findable (0 stubs today).
- Worked examples of each case are a comment at the end of `chunk.py`.
- The synthetic fixture vault is deferred (owner agreed) → BACKLOG. Unit tests use inline strings.

Gotchas:

- Real vault with `.env` values: 776 notes → 1,992 chunks, median 530, max exactly 1,500, 0 empty. heading_path depth: 285 title only, 854 one heading, 853 two.
- Stub filter drops 0 notes today: the one note under 100 chars in Task 1 has since grown (shortest body is now 131).
- A paragraph longer than the max (a long code block, say) is cut per line and rejoined with blank lines: harmless for embeddings, slightly changes code layout in that chunk. Marked `ponytail:` in code.
