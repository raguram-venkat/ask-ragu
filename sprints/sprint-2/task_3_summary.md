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

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
