# ADR-0014: Basic auth at the proxy for the public demo

Status: proposed
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

The UI will live on a public URL for interviews; without auth anyone can read the notes and burn the free quotas. SPEC v2 had auth out of scope. (D-004)

## Decision

Caddy basic auth on every route except /webhook (HMAC) and /healthz; app-level rate limiting on /chat and /search.

## Alternatives considered

- No auth — exposes private notes.
- App-level login — more code, no benefit for one user.
- Tailscale-only access — secure, but interviewers can't open it.

## Consequences

- Share a temporary password with an interviewer, rotate afterwards.
- Stock Caddy has no rate limiter, hence app-level.
