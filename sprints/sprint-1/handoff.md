# Handoff — Sprint 1

Interim handoff, 2026-10-03: sprint parked, not closed (D-008). Rewrite at real close.

Update 2026-10-13 (D-014): no A1 after ~4,100 attempts, so the sprint is un-parked with the Micro as the host. Next: Task 3 (prepare the Micro), then 6, 5, 4 as the owner prefers. The A1 notes below stay valid for the move-back case.

If an A1 ever arrives (the runner emails): run `infra/cloud-init.sh` on it (its first-boot script), clone the repo and build the image there (arm64, proved under QEMU in Sprint 2), restore a `pg_dump` or run a full index, repoint DuckDNS and the `ragu-vm` alias, then terminate the Micro with its boot volume (200 GB storage allowance). A local LLM can then come back as a new D-entry (BACKLOG).

System state: Laptop — compose stack (Postgres 17 + pgvector 0.8.6, FastAPI app) healthy, migration runner working, /healthz checks DB + vector. Oracle (Hyderabad) — VCN, public subnet, internet gateway, and route are done and reusable. A temporary E2.1.Micro (x86, 1 GB) is reachable over SSH; it hosts only the A1 retry loop. No A1 yet: out of capacity.

How to resume:

- Sprint 1, Task 7 first: set up the retry runner on the Micro (about 75 min), then leave it running.
- Then Sprint 2, Task 1 on the laptop — all of Sprint 2 develops locally (`docker compose up`).
- Micro: `ssh -i ~/.ssh/ask-ragu-oci ubuntu@<micro-public-ip>`.
- When the A1 arrives: SSH in, run the verification list in Task 3, do Tasks 4–6, terminate the Micro (tick "delete boot volume").

Open risks / unfinished threads:

- A1 capacity may take days.
- Storage: Micro boot 100 GB + A1 boot ≤ 100 GB = the whole 200 GB free allowance. No extra volumes or backups until the Micro is gone.
- Trial ends about 30 days after signup (early November). Any A1 usage over 2 OCPU / 12 GB at that moment disables all A1 instances.
- Account appears not to be Pay-As-You-Go — check under Billing before relying on PAYG behaviour.
- ADR-0013 (Caddy + DuckDNS) and ADR-0014 (auth at proxy) are still proposed; resolve before Task 4.

Relevant ADRs and deviations:

- D-008, ADR-0007, ADR-0013, ADR-0014

Next sprint starts at: Sprint 2, Task 1 — vault profiling (laptop)
