# Task 4 — Observability & rebuild drill

Status: todo
Est: 75m
Spec: SPEC.md §11 · ADR-0011, ADR-0007

What: JSON logs with request ids, a query_log table (stage latencies, provider, fallbacks, refusal), and a timed rebuild from scratch.

Approach: Drill = drop the DB volume → start → full reindex → smoke test; write the steps into handoff.md. Check a week of Oracle utilization metrics against the idle-reclamation thresholds.

Read first:

- Docker json-file logging driver options

Watch out for:

- Don't log question and answer text if logs ever leave the VM — they contain your notes.
- Set log rotation (max-size) or the disk fills eventually.
- If memory sits under 20% with low CPU/network, reclamation is a real risk — decide the mitigation (ADR-0007 consequences).

Done when: Rebuild time recorded; utilization vs thresholds noted.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
