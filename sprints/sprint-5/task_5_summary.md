# Task 5 — /chat + minimal web UI

Status: todo
Est: 90m
Spec: SPEC.md §6, §15 · D-004

What: POST /chat returns {answer, citations[{title, heading, how_reached}], provider, timings}; one static HTML page renders it.

Approach: No framework: one HTML + vanilla JS file served by FastAPI; citation badges "direct" vs "via [[X]]" make graph retrieval visible.

Read first:

- FastAPI StaticFiles

Watch out for:

- Behind Caddy basic auth (D-004) — a public URL would otherwise expose your notes and burn free quotas.
- Clear loading state: a local-model fallback can take tens of seconds.

Done when: From your phone, ask a cross-note question and point at the "via" badge.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
