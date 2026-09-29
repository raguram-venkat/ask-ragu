# ADR-0009: Exclude free tiers that train on prompts

Status: proposed
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Some free LLM tiers use prompts to improve models (e.g. Gemini's free tier outside the EU/UK/EEA, per mid-2026 terms). Every answer sends note snippets to the provider. (D-005)

## Decision

Each provider in config carries `trains_on_data`; providers with `true` are disabled unless explicitly opted in.

## Alternatives considered

- Use whatever free tier is most generous — more quota, notes become training data.
- Local model only — fully private, too slow to be the main path.

## Consequences

- Smaller free-quota pool; mitigated by chaining several non-training providers.
- Terms change: re-verify on each provider change and record the date checked.
