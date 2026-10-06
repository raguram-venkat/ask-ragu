# Task 6 — Full index command

Status: done
Est: 75m
Spec: SPEC.md §8

What: `askragu index --full` walks the vault and parses, chunks, embeds, and upserts every note, one transaction per note, then records the commit SHA.

Approach: Skip notes whose content_hash is unchanged; upsert note by path and replace its chunks/links/tags; delete DB notes whose files are gone; update index_state last.

Read first:

- psycopg 3: transactions, executemany / COPY

Watch out for:

- Idempotent: a second run embeds nothing and changes nothing.
- Embedding model in index_state differs from config → re-embed everything.
- Expose progress counters for /index/status (Task 8).

Done when: First run indexes the vault; second run reports 0 embedded; counts match Task 1's profile.

---

Filled in while working

Files touched:

- `src/ask_ragu/index/full.py` — `index_full(conn, vault) -> Stats`, `content_hash`, `git()` helper
- `src/ask_ragu/cli.py`, `pyproject.toml` — `askragu index --full` (stdlib argparse)
- `tests/test_full_index.py` — throwaway git vault + fake embedder: first run, idempotent rerun, frontmatter-only edit, body edit (id kept), delete, chunk-setting change re-embeds
- `tests/conftest.py` — the DB fixture moved here from `test_migrate.py` (shared)
- `Dockerfile` — installs `git`; `compose.override.yml` — vault mounted read-only at `/vault`
- `src/ask_ragu/index/chunk.py`, `tests/test_chunk.py` — metadata headings (follow-up fix below)
- `src/ask_ragu/settings.py`, `.env.example` — `CHUNK_METADATA_HEADINGS`, `VAULT_PATH` (in-container path), `VAULT_HOST_PATH` (laptop, used by compose only)

Decisions made here:

- Files come from `git ls-files -z` and the commit from `git rev-parse HEAD`, not a folder walk, so the index matches what Task 8's diffs will see. Uncommitted changes in the vault → a warning (the recorded commit wouldn't match); the VM clone is never edited, so it doesn't happen there.
- `content_hash` = sha256 of title, cleaned body and every chunk/model setting. Changing `CHUNK_*`, `STUB_MIN_CHARS` or the model in `.env` re-embeds everything on the next run; that also covers "model in index_state differs from config".
- One upsert decides "did this note change?": `ON CONFLICT ... WHERE (...) IS DISTINCT FROM (...) RETURNING id` returns nothing for an unchanged note, so a rerun writes nothing. A frontmatter-only edit rewrites the row, links and tags but keeps the chunks (SPEC §8 step 4).
- Embedding runs before the note's transaction, so no transaction is held open while the model works.
- Deletions and `index_state` happen last in one transaction: a crash mid-run leaves `last_commit` at the previous commit, so the next run redoes the work.
- `note_links.target_note_id` stays NULL; resolution is Sprint 3 Task 1.
- No progress counters for `/index/status` yet: `Stats` is returned and logged; Task 8 can expose it.
- Run it in the stack: `docker compose exec app askragu index --full`. From the host: `DATABASE_URL=<TEST_DATABASE_URL value> VAULT_PATH=<vault> uv run askragu index --full` (real env vars beat `.env`).

- Follow-up fix, "Part of" headings: in this vault `## Part of` is a metadata section (links to the parent concept/MOC), the first heading in 704 of 748 notes. In 277 notes the body sections below it are `###`, so the chunker treated them as sub-sections of "Part of": paths like "<Note title> > Part of > <Section>", with "Part of" embedded and given full-text weight A on every one of those chunks. Fix: `CHUNK_METADATA_HEADINGS='["Part of"]'` in `.env`; such a heading starts a section but never joins `heading_path`, and its line stays in the chunk text ("## Part of\n- Parent"). The list is part of `content_hash`, so the re-index re-embedded everything on its own. After: 0 paths contain "Part of", 704 opening chunks carry the parent links + intro, and the self-attention section's similarity went 0.769 → 0.785. The parent link itself was already stored as a link; a typed parent edge is a Sprint 3 idea (BACKLOG).

Gotchas:

- `git ls-files` without `-z` prints 186 of the vault's paths quoted and escaped (non-ASCII titles, e.g. em-dashes): a plain line split silently drops them (567 vs 753 `.md`). Always `-z`. Covered by a test with a non-ASCII path.
- The vault is mounted from the host with a different owner, so git refuses it ("dubious ownership") unless run with `-c safe.directory=<vault>`.
- `git status` on a read-only mount: use `--no-optional-locks` so it doesn't try to write `.git/index`.
- Real vault (commit 28b76545): first run 748 notes, 1,964 chunks (1,965 after the "Part of" fix), 2,660 links, 84 tags in 2 min 18 s (including the first model download into the `models` volume); second run 4.6 s, 0 written, 0 embedded. Matches the profiler (748 indexable).
- Sample vector search works (right notes on top), with two quirks → BACKLOG: (1) `## Part of` (parent links, the first heading in 704 notes) becomes a heading_path ancestor of the `###` body sections in 277 notes ("Title > Part of > X"); (2) a MOC's `## Links` list scores as high as the definition (0.774 vs 0.775).
- On the VM the vault mount must go in the VM's compose setup (compose.override.yml is laptop-only) — Sprint 1 Tasks 5–6.
