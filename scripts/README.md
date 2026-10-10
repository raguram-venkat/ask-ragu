# scripts/

One-off tools run by hand from the laptop. Not imported by the app, not run in CI.

| Script | Purpose | Used in |
|---|---|---|
| `profile_vault.py` | Measure the vault's real shape before designing the parser and chunker | sprint-2/task_1 |
| `bench_expansion.py` | Per-hop expansion vs one recursive CTE: latency and overlap on the real index | sprint-3/task_3, ADR-0015 |

## bench_expansion.py

```bash
uv run python scripts/bench_expansion.py          # DB: TEST_DATABASE_URL from .env
PGOPTIONS="-c jit=off" uv run python scripts/bench_expansion.py   # without Postgres JIT
```

Read-only; prints aggregate numbers only. Caps and depth come from `.env` (`GRAPH_*`). Re-run it
on the A1 once it exists, and whenever the vault or the expansion query changes a lot.

## profile_vault.py

```bash
python3 scripts/profile_vault.py /path/to/vault-clone
```

Read-only on the vault and stdlib-only, so it needs no venv and adds no dependency. Its output
includes note titles and tag names, so keep the output in your terminal and never paste it
into git. Only aggregate numbers go into task files. Results from the last run are in
`sprints/sprint-2/task_1_summary.md`; re-run it whenever the vault changes a lot.

### How it measures

- Scope: every `*.md` file not under an excluded folder (`Templates/`, `.obsidian/`, `Bases/`,
  `Attachments/`, `.git/` — D-006). It sees what the indexer would see.
- Size is in characters (`len(text)`), not tokens. Rough conversion for English prose: ~4
  chars per token; code and symbols use more tokens per char. Task 5 can check this with the
  real tokenizer.
- Frontmatter is the block between a leading `---` line and the next `---`. Keys and `tags`
  are read with regexes. This is no YAML parser, so it can't detect malformed YAML; Task 3 uses
  a real one.
- Code blocks: a line starting with ` ``` ` or `~~~` toggles "inside code". Headings, links
  and tags inside code are not counted as such. `[[...]]` inside code is counted separately.
  Inline `` `code` `` spans are removed before searching a line for links and tags.
- Sections: the body under one heading, up to the next heading of any level. The heading line
  itself is excluded, and blank lines count as 0. Text before the first heading is the
  *preamble*, counted separately (for a heading-less note, the whole body is preamble).
- Links: `[[target|alias]]` without a leading `!`. Kind: `#^` → block, `#` → heading,
  `/` → folder path, else plain; `+alias` if it has `|`. Resolution, in this order: empty
  target → self link; matches a full path → by path; matches exactly one filename
  (case-insensitive) → unique; several → ambiguous; none → dangling.
- Embeds: `![[x]]` grouped by file extension, plus Markdown images `![alt](target)` grouped by
  target (URL / `Attachments/` / other).
- Tags: frontmatter `tags` (inline or `- item` list) plus inline `#tag` outside code and
  outside heading lines. A tag's share is the number of notes using it divided by the total
  number of notes. `#123` (all digits) isn't a tag in Obsidian and is counted separately.

### What it reports, and why each one matters

| Stat | Why we care | Decides / feeds |
|---|---|---|
| Notes per folder; `type:` key vs folder | `note_type` comes from the folder (D-006); checks that every folder maps to a type, and that frontmatter agrees when it has a `type:` key | Task 2 `note_type`, Task 3 |
| Note size (median/p95/max), largest notes | Shows whether huge notes exist that need special handling; sanity check | Task 4 test cases |
| Note body size, small end | Near-empty notes add noise to vector search (SPEC §14) | **stub min** (note level) |
| Preamble empty vs with text | Is there text before the first heading that needs its own chunk? | Task 4 |
| Section size (median/p90/p95/max, counts over 1000/1500/2000/4000) | Chunks follow headings, so a section is the natural chunk; the chunk max should split only the tail, and must stay under the embedding model's 512 tokens with the title and heading path prepended | **chunk max** |
| Section size, small end (empty, under 80/200/400) | Shows whether small sections should be dropped or merged into a neighbour | Task 4 merge rule |
| Headings per note, notes with none, heading levels | Notes without headings need the paragraph-window fallback; the levels used set what `heading_path` looks like | Task 4 |
| Links per note (median/p95/max, total) | Graph density; max is the hub fan-out (D-007) | Sprint 3 fan-out cap |
| Link kinds | Which link variants the parser *must* handle on real data | Task 3 tests |
| Link resolution (unique / ambiguous / dangling), duplicate filenames, `aliases` key | How hard link resolution really is; ambiguous names need a tie-break rule | Task 3, Sprint 3 |
| `[[...]]` inside code | These must never become links | Task 3 |
| Embeds and image targets | Embeds are skipped, not resolved; shows which syntaxes the skip rule must cover | Task 3 |
| Frontmatter presence, keys, tag style, tags per note, tag vs `domain` | What the frontmatter jsonb actually holds; whether tags behave as labels or as categories | Task 2, Task 3, ADR-0010 |
| Distinct tags, top tag shares | A tag on too many notes is a useless graph edge (SPEC §7) | **tag cutoff** |
| Callouts, code-block languages, Templater tags | What the cleaning step actually has to strip or unwrap | Task 3 |
