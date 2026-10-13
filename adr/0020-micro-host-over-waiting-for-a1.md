# ADR-0020: Host on the existing E2.1.Micro instead of waiting for an A1

Status: proposed — resolve before sprint-1/task_3 starts
Date: 2026-10-13
Sprint: sprint-4 (raised during; work is sprint-1/task_3–6) · D-014

## Context

No A1 capacity in Hyderabad (one availability domain) after ~4,100 automated attempts since 2026-10-03; the Pay-As-You-Go upgrade failed (card declined, sprint-1/task_3). Everything since Sprint 2 runs on the laptop, and Sprints 4–6 have "on the VM" checks. The Always Free E2.1.Micro (x86_64, 1 GB RAM, 100 GB boot volume) already exists and runs only the A1 retry loop.

## Decision

Run the compose stack (Postgres + pgvector, app with the int8 embedder, Caddy) on the Micro, with a swapfile, per-container memory limits and a small Postgres config, all from `.env`. Images are built on the laptop (also x86_64) and shipped with `docker save | ssh ragu-vm docker load`. The A1 retry runner keeps running beside the stack, memory-capped; if an A1 ever arrives, the stack moves there and the Micro is terminated with its boot volume.

## Alternatives considered

- Keep waiting for an A1 — open-ended; blocks deploy, HTTPS, the webhook and every "on the VM" check.
- A second Micro just for the stack — 100 + ≥47 GB boot volumes leave no room in the 200 GB allowance for an A1 boot volume, and the quota policy would need loosening.
- GCP e2-micro — same 1 GB, a new account and billing setup, no gain.
- Managed free Postgres (Neon/Supabase) + tiny compute — every note's full text leaves the host, breaking SPEC §4. Last resort only, with its own D-entry.
- The laptop — not always-on.

## Consequences

- x86_64, not arm64; ADR-0007's "Oracle over AWS" still holds, its A1/arm64 consequences don't apply while on the Micro. The image stays arm64-compatible (proved under QEMU in Sprint 2) for a later move.
- Embedding and retrieval are slower on a fractional OCPU: full-index time and retrieval p95 are measured in sprint-1/task_3 and task_6, and the Sprint 4 latency target is re-checked against them.
- If the Micro is ever terminated, creating a new one needs the quota policy (D-009) to allow one E2 Micro core first.
- No local LLM (ADR-0021).
