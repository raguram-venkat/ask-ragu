# ADR-0001: Postgres full-text + pgvector over OpenSearch

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

OpenSearch solves lexical (and bolt-on vector) search but has no native notion of note-to-note links, and it's a second stateful JVM service on a 12 GB box.

## Decision

Use Postgres with pgvector: tsvector for lexical, pgvector for semantic, SQL for graph traversal — one datastore.

## Alternatives considered

- OpenSearch with k-NN plugin — hybrid search, but graph still needs a second system.
- Dedicated vector DB (Qdrant/Weaviate) + Postgres for metadata — two stores to keep consistent.

## Consequences

- One service to run, secure, and rebuild.
- Lexical ranking is simpler than BM25 (ts_rank_cd); acceptable at single-vault scale, measured in Sprint 4.
- OpenSearch stays a separate learning project.
