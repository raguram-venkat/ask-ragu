# ADR-0005: Ack-fast webhook + in-process background task

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

GitHub fails a webhook delivery that isn't answered within 10 seconds. SPEC v2 planned synchronous in-process indexing — too slow for a large push on 2 ARM cores. (D-001)

## Decision

Verify HMAC, return 202, run the sync as an in-process background task. A single-flight lock allows one sync at a time; a dirty flag coalesces pushes that arrive mid-run.

## Alternatives considered

- Synchronous indexing inside the request — breaks the 10 s limit.
- Task queue (RQ/Celery + Redis) — durable jobs, but a broker service for a few pushes a day.

## Consequences

- A crash mid-sync loses the in-flight job; startup reconciliation (diff from last_commit) recovers it, so no durability is lost in practice.
- Duplicate deliveries are harmless: sync is idempotent against last_commit.
