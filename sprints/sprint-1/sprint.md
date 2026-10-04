# Sprint 1 — Foundations & Infra

Goal: The same Docker Compose stack (Postgres+pgvector, FastAPI) runs on the laptop and on an Oracle A1 VM behind Caddy HTTPS with auth, and the private vault is cloned onto the VM via a read-only deploy key.

Spec reference: SPEC.md §6, §11, §15, §16 Phase 1 · D-004

Status: parked — Tasks 4–6 wait for an A1 instance (D-008)
Started: 2026-09-29
Closed: 
Estimated effort: ~8.4 h across 7 tasks

## Tasks

- [x] [Task 1 — Repo skeleton & tooling](task_1_summary.md) · 60m
- [x] [Task 2 — Local compose stack + migrations](task_2_summary.md) · 90m
- [ ] [Task 3 — Provision Oracle A1 VM](task_3_summary.md) · 90m — blocked: no A1 capacity; networking done
- [ ] [Task 4 — Public HTTPS + auth at the proxy](task_4_summary.md) · 75m — deferred until A1 (D-008)
- [ ] [Task 5 — Vault deploy key + sparse clone](task_5_summary.md) · 60m — deferred until A1 (D-008)
- [ ] [Task 6 — Deploy workflow](task_6_summary.md) · 60m — deferred until A1 (D-008)
- [ ] [Task 7 — A1 capacity retry runner on the Micro](task_7_summary.md) · 75m — added by D-008

## Definition of Done

- `docker compose up` brings up healthy postgres + app, locally and on the VM
- `https://<name>.duckdns.org/healthz` returns 200 (DB + vector extension OK) from outside your network
- Every route except /webhook and /healthz returns 401 without credentials
- Vault `.md` files present in a named volume on the VM; deploy key read-only and not in git
- Secret scan (gitleaks) over the repo finds nothing; stack survives a VM reboot

## Deviations from plan

- D-008 — deploy work decoupled; A1 retry runner added as Task 7

## ADRs touched

- ADR-0007 Oracle over AWS — accepted
- ADR-0012 raw SQL over ORM — accepted
- ADR-0013 Caddy + DuckDNS — proposed, resolve before Task 4
- ADR-0014 auth at proxy — proposed, resolve before Task 4

## Outcome

_(fill in at close)_
