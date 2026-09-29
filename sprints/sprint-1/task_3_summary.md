# Task 3 — Provision Oracle A1 VM

Status: todo
Est: 90m
Spec: SPEC.md §11

What: One VM.Standard.A1.Flex (2 OCPU / 12 GB, Ubuntu 24.04 aarch64) with key-only SSH and Docker Engine + compose plugin.

Approach: Console wizard for compartment + VCN; one instance using the whole A1 allowance; Docker from Docker's apt repo (not snap).

Read first:

- Oracle docs: Always Free Resources (limits and idle-reclamation rules)
- Docker Engine install for Ubuntu

Watch out for:

- "Out of host capacity" on A1 is common — retry later or another availability domain. Fallback host: GCP e2-micro (no local LLM).
- Idle reclamation: Oracle may reclaim if CPU p95, network, and memory are all < 20% over 7 days. Community reports say upgrading to Pay-As-You-Go avoids this while staying free within limits — verify in Oracle's docs and set a $1 budget alert first.
- Disable password login and root login in sshd; keep a second SSH session open while editing sshd_config.

Done when: `ssh` in, `uname -m` → aarch64, `docker run --rm hello-world` works, password SSH is refused.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
