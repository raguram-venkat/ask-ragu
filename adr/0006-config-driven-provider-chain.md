# ADR-0006: Config-driven provider fallback chain

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Free inference providers rate-limit, change models, and go down; the local model is slow but always there.

## Decision

One provider interface; an ordered list in providers.yaml (reloaded on change); each provider fails with a typed reason and the chain moves on; a circuit breaker skips a failing provider for a few minutes.

## Alternatives considered

- Single hardcoded provider — simplest, one outage from broken.
- Third-party router only (e.g. OpenRouter alone) — outsources the fallback logic and the lesson.

## Consequences

- Local and hosted providers share one OpenAI-compatible adapter; only URL/model/key differ.
- Every answer records which provider answered and why others were skipped.
