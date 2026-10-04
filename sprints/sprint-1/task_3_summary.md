# Task 3 — Provision Oracle A1 VM

Status: blocked — no free A1 capacity in Hyderabad (2026-10-03); Task 7 retries automatically
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
- Signup starts a 30-day / $300 trial alongside Always Free. Always Free resources survive trial end; paid ones are reclaimed after a 30-day grace period. Create only Always-Free-eligible resources (A1 exactly 2 OCPU / 12 GB total, ≤ 200 GB block storage): if A1 usage exceeds the allowance when the trial ends, Oracle disables all A1 instances, the good one included.
- Disable password login and root login in sshd; keep a second SSH session open while editing sshd_config.

Done when: `ssh` in, `uname -m` → aarch64, `docker run --rm hello-world` works, password SSH is refused.

---

Filled in while working

Files touched:

- infra/cloud-init.sh

Decisions made here:

- Home region: Hyderabad (ap-hyderabad-1). Permanent; one availability domain, so no other AD to try.
- Networking (reused by any future instance): VCN `ask-ragu-vcn`, public subnet `ask-ragu-public-subnet` (10.0.0.0/24), internet gateway, default route table `0.0.0.0/0 → internet gateway`.
- Firewall rules live only in the subnet's default security list; the three quick-action NSGs were removed.
- A1 launch failed with "Out of capacity" at 2/12 and 1/6. An E2.1.Micro created by mistake is kept temporarily as the host for Task 7's retry loop (D-008).
- Tenancy quota policy `ask-ragu-free-tier-guard` is the hard backstop: no compute shape but A1, A1 ≤ 2 OCPU / 12 GB, block storage ≤ 200 GB. Verified on the Limits page: A1 available 2 cores / 12 GB (D-009). The $1 budget alert stays as the second line.
- First-boot setup is a cloud-init script pasted at instance creation (SSH hardening + Docker from Docker's apt repo + `ubuntu` in the docker group), so a reclaimed VM is rebuilt with one paste instead of a manual redo.
- SSH hardening goes in `/etc/ssh/sshd_config.d/00-hardening.conf`: sshd keeps the first value it reads, so `00-` beats Ubuntu's `50-cloud-init.conf`. Verified with `sshd -T` in an ubuntu:24.04 container.

Gotchas:

- VM.Standard.E2.1.Micro is also tagged "Always Free" (Specialty series), and it can't be resized. Check the shape line on the review page before Create.
- The public-IPv4 toggle is greyed out when the subnet is created in the same form. Fix: VNIC → IP administration → Edit → Ephemeral public IP. Better: create the network first, then "Select existing".
- Quick action "Connect public subnet to internet" isn't idempotent: each click attached another NSG.
- Giving a card at signup ≠ Pay-As-You-Go. The limits page still says "upgrade to a paid account"; the account type is under Billing.
- The PAYG upgrade attempt (2026-10-03) failed: the card issuer declined a ~138 SGD authorization hold as an unregistered "standing instruction" (recurring-payment mandate); the hold was reversed. The account stays on Free Tier, and the plan doesn't depend on PAYG.
- Budgets only alert after a charge happens; only quotas actually prevent one.
- An ephemeral public IP is released when the instance is terminated — update DuckDNS after any rebuild.
- `cloud-init status` only verifies a script pasted at launch, not one run by hand over SSH.
- "Service limits: critical" for E2 micro cores (1 of 2) is just the Micro; it clears when the Micro is terminated. 
