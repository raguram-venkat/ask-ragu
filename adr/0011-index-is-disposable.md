# ADR-0011: Index is derived state: rebuild, don't back up

Status: proposed
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Everything in Postgres is derived from the vault repo plus deterministic code and a pinned embedding model.

## Decision

No database backups. Recovery = fresh volume + full reindex. Only non-derivable data (query logs, eval results) is optional to keep.

## Alternatives considered

- Nightly pg_dump to object storage — protects data that can be regenerated anyway.

## Consequences

- Rebuild time is the recovery time: measured in the Sprint 6 drill.
- Enables later zero-downtime reindex (build new, swap).
