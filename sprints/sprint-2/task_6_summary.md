# Task 6 — Full index command

Status: todo
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

- 

Decisions made here:

- 

Gotchas:

- 
