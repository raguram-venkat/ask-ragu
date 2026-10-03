# Sprint 1 — Foundations & Infra

Goal: The same Docker Compose stack (Postgres+pgvector, FastAPI) runs on the laptop and on an Oracle A1 VM behind Caddy HTTPS with auth, and the private vault is cloned onto the VM via a read-only deploy key.

Spec reference: SPEC.md §6, §11, §15, §16 Phase 1 · D-004

Status: in progress
Started: 2026-09-29
Closed: 
Estimated effort: ~7.2 h across 6 tasks

## Tasks

- [x] [Task 1 — Repo skeleton & tooling](task_1_summary.md) · 60m
- [x] [Task 2 — Local compose stack + migrations](task_2_summary.md) · 90m
- [ ] [Task 3 — Provision Oracle A1 VM](task_3_summary.md) · 90m
- [ ] [Task 4 — Public HTTPS + auth at the proxy](task_4_summary.md) · 75m
- [ ] [Task 5 — Vault deploy key + sparse clone](task_5_summary.md) · 60m
- [ ] [Task 6 — Deploy workflow](task_6_summary.md) · 60m

## Definition of Done

- `docker compose up` brings up healthy postgres + app, locally and on the VM
- `https://<name>.duckdns.org/healthz` returns 200 (DB + vector extension OK) from outside your network
- Every route except /webhook and /healthz returns 401 without credentials
- Vault `.md` files present in a named volume on the VM; deploy key read-only and not in git
- Secret scan (gitleaks) over the repo finds nothing; stack survives a VM reboot

## Deviations from plan

- (none yet)

## ADRs touched

- ADR-0007 Oracle over AWS — accepted
- ADR-0012 raw SQL over ORM — accepted
- ADR-0013 Caddy + DuckDNS — proposed, resolve before Task 4
- ADR-0014 auth at proxy — proposed, resolve before Task 4

## Outcome

_(fill in at close)_
