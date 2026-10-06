# ADR-0018: One sync at a time per index — Postgres advisory lock + coalescing runner

Status: accepted
Date: 2026-10-06
Sprint: sprint-2 (task_8)

## Context

Syncs start from the webhook and app startup (in-process `SyncRunner`, single-flight) and from the CLI (a separate process the runner can't see). Two syncs at once waste CPU on duplicate embedding, trip unique-key errors, can leave `index_state` behind the newest content until the next sync, and collide on git's lock during fetch/reset.

## Decision

`sync()` holds a session-level Postgres advisory lock for its whole run (fetch, diff, index, state, working-tree reset), keyed by the current schema. A second sync blocks until the lock is free, then reads the newest target itself. Inside the app, the runner's dirty flag still coalesces any number of triggers during a run into one follow-up run. No lock timeout.

## Alternatives considered

- A queue of individual sync requests — pointless work: every sync goes to the newest commit, so one follow-up run covers any number of pushes.
- CLI asks the app to sync over HTTP — another endpoint and failure path to serialize something Postgres already can.
- Transaction-level advisory lock — a sync is many transactions (one per note), so it would be released mid-run.
- A lock timeout — a waiter should wait out a long full index on 2 ARM cores; a crashed holder's connection closes and Postgres frees the lock, so it can't go stale.

## Consequences

- Any number of processes can start syncs safely; they queue in Postgres and the late ones are usually no-ops.
- Per-schema keys: Sprint 4 experiment schemas and test schemas never block the real index.
- A sync that hangs while holding the lock blocks later ones; visible as `sync_running` in `/index/status`.
