# Task 3 — Prepare the Micro as host

Status: todo — re-scoped 2026-10-13 by D-014 (was: provision an A1, blocked on capacity since 2026-10-03)
Est: 60m
Spec: SPEC.md §11 · D-014, ADR-0020

What: Measure the E2.1.Micro's real CPU and free RAM, add swap and Docker, and decide from numbers whether the stack fits beside the A1 runner.

Approach: Baseline first, then a 4 GB swapfile and Docker via `infra/cloud-init.sh` run by hand (arch-neutral), then idle numbers again. Everything later (task_6's memory limits, the latency targets) comes from these numbers.

Read first:

- ADR-0020; Oracle docs: Always Free resources (E2.1.Micro shape, idle reclamation)
- `cheatsheets/ssh-vm.md`, `cheatsheets/a1-runner.md` (local)

Steps (owner at the keyboard: the SSH key has a passphrase):

1. Baseline: `ssh ragu-vm 'uname -m; nproc; lscpu; free -h; swapon --show; df -h /; systemctl is-active a1-runner; systemctl show a1-runner -p MemoryCurrent'`.
2. CPU reality: the same short single-thread benchmark on the Micro and the laptop (e.g. `openssl speed -seconds 10 sha256`), twice in a row on the Micro to see whether it throttles after a burst. Record the ratio.
3. Swap: 4 GB swapfile (`fallocate`, `chmod 600`, `mkswap`, `swapon`, `/etc/fstab`), `vm.swappiness=10` in `/etc/sysctl.d/`. Swap is for spikes (model load, full index), not steady state.
4. Docker: `scp infra/cloud-init.sh ragu-vm:` then `ssh ragu-vm 'sudo bash cloud-init.sh'`. The Docker apt source has no `Architectures:` line, so apt picks amd64; the SSH hardening part is idempotent. Then `docker run --rm hello-world`.
5. A1 runner beside the stack (D-014): add `MemoryMax=150M` to the unit (`sudo systemctl edit a1-runner`, a drop-in on the Micro; mirror it in `infra/a1-runner.service` together with the owner's pending infra edits, not in a sprint commit). Restart it, check it's still `active`.
6. Optional, measured before/after: if `snap list` shows nothing you use, `sudo systemctl disable --now snapd snapd.socket`.
7. Idle again: OS + Docker + runner, MB used.

Watch out for:

- Storage: Micro boot 100 GB + a future A1 boot ≤ 100 GB = the 200 GB allowance. No second Micro, no extra block volume (ADR-0020).
- The quota policy blocks creating a Micro: if this one is ever terminated or reclaimed and has to be rebuilt, first allow one E2 Micro core in `ask-ragu-free-tier-guard` (verify the quota name in Oracle's quota docs and write the exact statement here when you do).
- Idle reclamation: the weekly check in `cheatsheets/a1-runner.md` still applies.
- Kill criterion: idle RAM > 600 MB with only OS + Docker + runner → stop the runner and re-measure; still > 600 MB → stop and decide with the owner before task_6 (ordered fallbacks in task_6).

Done when: the table below is filled, swap is on, `docker run --rm hello-world` works, the runner is still active (or stopped by decision).

| Item | Value |
|---|---|
| CPU model / nproc / benchmark ratio vs laptop (1st, 2nd run) | |
| RAM used idle: before / after Docker + swap | |
| A1 runner RSS (capped 150M) | |
| Disk free | |

## Superseded plan (A1, before D-014)

Kept for the record and in case an A1 arrives: then this was the plan, and the move-back steps in `handoff.md` apply.

> Status: blocked — no free A1 capacity in Hyderabad (2026-10-03); Task 7 retries automatically
> Est: 90m
> Spec: SPEC.md §11
>
> What: One VM.Standard.A1.Flex (2 OCPU / 12 GB, Ubuntu 24.04 aarch64) with key-only SSH and Docker Engine + compose plugin.
>
> Approach: Console wizard for compartment + VCN; one instance using the whole A1 allowance; Docker from Docker's apt repo (not snap).
>
> Read first:
>
> - Oracle docs: Always Free Resources (limits and idle-reclamation rules)
> - Docker Engine install for Ubuntu
>
> Watch out for:
>
> - "Out of host capacity" on A1 is common — retry later or another availability domain. Fallback host: GCP e2-micro (no local LLM).
> - Idle reclamation: Oracle may reclaim if CPU p95, network, and memory are all < 20% over 7 days. Community reports say upgrading to Pay-As-You-Go avoids this while staying free within limits — verify in Oracle's docs and set a $1 budget alert first.
> - Signup starts a 30-day / $300 trial alongside Always Free. Always Free resources survive trial end; paid ones are reclaimed after a 30-day grace period. Create only Always-Free-eligible resources (A1 exactly 2 OCPU / 12 GB total, ≤ 200 GB block storage): if A1 usage exceeds the allowance when the trial ends, Oracle disables all A1 instances, the good one included.
> - Disable password login and root login in sshd; keep a second SSH session open while editing sshd_config.
>
> Done when: `ssh` in, `uname -m` → aarch64, `docker run --rm hello-world` works, password SSH is refused.

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
