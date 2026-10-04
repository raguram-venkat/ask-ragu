# Task 3 — Note parser & cleaning

Status: todo
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
- Resolution: 2,713 resolve to a unique filename (case-insensitive), 54 hit a duplicate name, 9 are dangling. All duplicates are one Concepts subfolder whose notes repeat names in its own sub-subfolders. Needs a tie-break rule (e.g. prefer the shortest path, as Obsidian does), decided here or in Sprint 3.
- No `aliases` frontmatter key anywhere, so the alias map is empty today; build it anyway (cheap, SPEC §8).
- Tags: always a frontmatter `- item` list, one tag per note, equal to the `domain` key (751 of 752). No inline `#tags` and no `#123` cases found; keep the tests.
- 19 notes have no frontmatter at all; that's valid, not malformed.
- Cleaning targets are tiny: 0 dataview/base blocks and 0 Templater tags outside Templates/ and Bases/; 6 callouts (all `[!note]`).
- Only 2 `[[...]]` inside code blocks (the rule still applies). 259 code blocks, mostly unlabelled, rust, or python.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
