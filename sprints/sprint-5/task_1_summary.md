# Task 1 — Provider contract & fallback chain

Status: todo
Est: 90m
Spec: SPEC.md §10 · ADR-0006

What: A Provider interface and a Chain that tries providers in config order, with a failure taxonomy and a circuit breaker.

Approach: providers.yaml: name, base_url, model, timeout, max_context_tokens, trains_on_data, enabled; reload on file change; fall through on timeout / 429 / 5xx / empty or malformed output / model-not-found; open the circuit for a few minutes after repeated failures.

Read first:

- refactoring.guru: Strategy, Chain of Responsibility

Watch out for:

- Honour Retry-After on 429 when sizing the circuit break.
- Fit context per provider — a smaller window drops the weakest context first.
- Unit tests use fake providers (always-fail, slow, garbage) — no network in tests.

Done when: Tests cover each failure type; the chain returns who answered and why others were skipped.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
