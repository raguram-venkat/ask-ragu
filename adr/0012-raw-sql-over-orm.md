# ADR-0012: psycopg 3 + raw SQL over an ORM

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

The important queries are Postgres-specific: pgvector operators, tsvector, recursive or lateral graph queries.

## Decision

psycopg 3 with hand-written SQL; schema changes as numbered .sql migrations applied by a small runner at startup.

## Alternatives considered

- SQLAlchemy ORM + Alembic — industry standard, but most queries would be raw text() anyway.
- dbmate/yoyo for migrations — fine tools; a 30-line runner is also a lesson.

## Consequences

- Full control and readable EXPLAIN plans; no portability (none wanted).
- Must be disciplined about parameterized queries — never string-format SQL.
