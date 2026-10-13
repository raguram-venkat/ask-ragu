# Sprint 1 — Foundations & Infra

Goal: The same Docker Compose stack (Postgres+pgvector, FastAPI) runs on the laptop and on the Oracle E2.1.Micro [D-014; was: an A1 VM] behind Caddy HTTPS with auth, and the private vault is cloned onto it via a read-only deploy key.

Spec reference: SPEC.md §6, §11, §15, §16 Phase 1 · D-004, D-008, D-014

Status: un-parked 2026-10-13 — host is the Micro (D-014); Tasks 3–6 todo, Task 7 runner keeps running
Started: 2026-09-29
Closed: 
Estimated effort: ~8.4 h across 7 tasks

## Tasks

- [x] [Task 1 — Repo skeleton & tooling](task_1_summary.md) · 60m
- [x] [Task 2 — Local compose stack + migrations](task_2_summary.md) · 90m
- [ ] [Task 3 — Prepare the Micro as host](task_3_summary.md) · 60m — re-scoped by D-014 (was: provision A1); networking done
- [ ] [Task 4 — Public HTTPS + auth at the proxy](task_4_summary.md) · 75m — on the Micro (D-014)
- [ ] [Task 5 — Vault deploy key + sparse clone](task_5_summary.md) · 60m — on the Micro (D-014)
- [ ] [Task 6 — Deploy workflow](task_6_summary.md) · 90m — on the Micro, with memory limits + first full index (D-014)
- [ ] [Task 7 — A1 capacity retry runner on the Micro](task_7_summary.md) · 75m — added by D-008

## Definition of Done

- `docker compose up` brings up healthy postgres + app, locally and on the Micro, within its 1 GB (measured, task_6)
- `https://<name>.duckdns.org/healthz` returns 200 (DB + vector extension OK) from outside your network
- Every route except /webhook and /healthz returns 401 without credentials
- Vault `.md` files present in a named volume on the VM; deploy key read-only and not in git
- Secret scan (gitleaks) over the repo finds nothing; stack survives a VM reboot

## Deviations from plan

- D-008 — deploy work decoupled; A1 retry runner added as Task 7
- D-014 — host is the E2.1.Micro; Task 3 re-scoped, Tasks 4–6 target the Micro, runner stays as an opportunistic upgrade

## ADRs touched

- ADR-0007 Oracle over AWS — accepted (host shape amended by ADR-0020)
- ADR-0020 Micro host over waiting for an A1 — proposed, resolve before Task 3
- ADR-0012 raw SQL over ORM — accepted
- ADR-0013 Caddy + DuckDNS — proposed, resolve before Task 4
- ADR-0014 auth at proxy — proposed, resolve before Task 4

## Outcome

_(fill in at close)_
