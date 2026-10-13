# Task 4 — Observability & rebuild drill

Status: todo
Est: 75m
Spec: SPEC.md §11 · ADR-0011, ADR-0007

What: JSON logs with request ids, a query_log table (stage latencies, provider, fallbacks, refusal), and a timed rebuild from scratch.

Approach: Drill on the Micro (D-014) = drop the DB volume → start → full reindex (or the laptop-built dump, if sprint-1/task_6 had to fall back to it) → smoke test; write the steps into handoff.md. Rehearse a lost-Micro rebuild on paper too: quota policy edit to allow one E2 Micro core, cloud-init, swap, restore. Check a week of Oracle utilization metrics against the idle-reclamation thresholds.

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
