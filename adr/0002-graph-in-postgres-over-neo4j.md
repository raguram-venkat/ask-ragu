# ADR-0002: Graph in Postgres over a dedicated graph DB

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Retrieval needs ≤ 2-hop expansion over a few thousand notes.

## Decision

Store links in a `note_links` table and traverse in SQL.

## Alternatives considered

- Neo4j — Cypher is nicer for deep traversal, but it's a JVM service plus a sync pipeline from Postgres.
- In-memory graph in the app (networkx) — fast, but rebuilt on every restart and duplicated state.

## Consequences

- No second store to keep in sync; links update in the same transaction as notes.
- Deep or weighted path queries would get awkward in SQL — revisit only if depth > 2 is ever needed.
