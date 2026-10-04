# Task 3 — Note parser & cleaning

Status: done
Est: 90m
Spec: SPEC.md §8 · D-006

What: Turns one file into {frontmatter, note_type, cleaned body, links, tags} — or rejects it as non-indexable.

Approach: Exclusions first (Templates/, .obsidian/, Bases/, Attachments/, non-.md); tolerant YAML frontmatter; strip dataview/base fences and Templater `<% %>` tags; unwrap callouts to plain text; extract wikilinks and tags (inline and frontmatter).

Read first:

- python-frontmatter or PyYAML safe_load
- Obsidian help: Internal links, Tags, Callouts

Watch out for:

- Link variants: `[[Note]]`, `[[Note|alias]]`, `[[Note#Heading]]`, `[[Note#^block]]`, `[[Folder/Note]]`; `![[x.png]]` is not a link, `![[Note]]` (note embed) is.
- No links or tags from inside fenced or inline code.
- Malformed frontmatter → warning + index the body; never fail the run.
- `#tag` vs `# Heading` vs `#123` (pure numbers aren't tags in Obsidian).

Done when: Unit tests for every variant above pass against the fixture vault (Task 4).

From Task 1 profiling (real vault, `scripts/profile_vault.py`):

- Images are Markdown `![alt](Attachments/...)` (123 refs, 58 notes), not `![[x.png]]`. Skip both syntaxes; never turn either into a link.
- Link variants in real use: only `[[Note]]` (2,619) and `[[Note|alias]]` (157). No `#heading`, `#^block`, `[[Folder/Note]]` or `![[Note]]` yet; keep their tests (fixture vault) but don't over-invest.
- Resolution: 2,713 resolve to a unique filename (case-insensitive), 54 hit a duplicate name, 9 are dangling. All duplicates are one Concepts subfolder whose notes repeat names in its own sub-subfolders. Needs a tie-break rule (e.g. prefer the shortest path, as Obsidian does) → Sprint 3 Task 1 (link resolution); this task only extracts raw targets.
- No `aliases` frontmatter key anywhere, so the alias map is empty today; build it anyway (cheap, SPEC §8).
- Tags: always a frontmatter `- item` list, one tag per note, equal to the `domain` key (751 of 752). No inline `#tags` and no `#123` cases found; keep the tests.
- 19 notes have no frontmatter at all; that's valid, not malformed.
- Cleaning targets are tiny: 0 dataview/base blocks and 0 Templater tags outside Templates/ and Bases/; 6 callouts (all `[!note]`).
- Only 2 `[[...]]` inside code blocks (the rule still applies). 259 code blocks, mostly unlabelled, rust, or python.

---

Filled in while working

Files touched:

- `src/ask_ragu/index/parse.py` — `is_indexable(path)`, `parse_note(path, text) -> ParsedNote | None`; pure, no I/O
- `tests/test_parse.py` — 37 cases: exclusions, type/title, frontmatter (good, malformed, dates), every link variant, code, tags, cleaning
- `pyproject.toml`, `uv.lock` — added PyYAML
- `src/ask_ragu/settings.py`, `.env.example` — `VAULT_FOLDER_TYPES`, `VAULT_DEFAULT_NOTE_TYPE`, `VAULT_EXCLUDED_DIRS`, `VAULT_STRIPPED_FENCES`

Decisions made here:

- PyYAML `safe_load` (can't run code from the vault), not python-frontmatter: splitting off the `---` block is a few lines.
- Links are extracted raw; resolution is Sprint 3 Task 1. `raw_target` is the note part only (`[[A#H|x]]` → `A`), so one edge per target note; repeats in a note are deduplicated (matches the note_links primary key).
- The cleaned body replaces links with their display text (`[[A|x]]` → `x`, `[[A#H]]` → `A > H`) so embeddings and full-text search see prose, not `[[` syntax. Images (`![](...)`, `![[x.png]]`) are removed; `![[Note]]` stays an `embed` link.
- Tags = frontmatter `tags` (list or comma/space string) + inline `#tags`, lowercased, because Obsidian treats tags case-insensitively.
- Callouts are unwrapped (`> [!note] Title` → `Title`, `> ` stripped from following lines); plain blockquotes are left alone.
- A note at the vault root or in an unknown folder is typed `fleeting` (lowest ranking prior) instead of being dropped silently.
- Folder→type map, default type, excluded folders and stripped fence types live in `.env` (`VAULT_*`, JSON for maps/lists), so they can be changed for an experiment without touching code. Tests pin their own values with `monkeypatch`, so editing `.env` can't break them.
- Tests use inline strings, not the fixture vault: each rule sits next to its input. The fixture vault is deferred (owner agreed); pipeline tests can adopt it later.

Gotchas:

- In YAML, ` #` starts a comment: `tags: a, #b` is just `a` (Obsidian agrees). Quote it: `tags: '#b'`.
- YAML turns `created: 2024-01-01` into a `date`, which `jsonb` can't store; frontmatter is round-tripped through JSON with `default=str`.
- `.env` JSON values are single-quoted; both compose `env_file` and pydantic-settings strip the quotes (checked inside the app container).
- Real-vault run: 776 notes, 85 tags, 2,685 unique links (2,776 occurrences), 0 errors or warnings. The leftover `[[`/`![` in bodies are all inline code, code blocks, Rust `vec![...]`, or bracket notation like `[[un- lock] -able]` (not a link: `]` inside).
