# ADR-0007: Oracle Cloud Always Free over AWS free tier

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Requirement: always on, indefinitely free. AWS's post-July-2025 free tier for new accounts is $100-200 credit for 6 months.

## Decision

Oracle Always Free Ampere A1: 2 OCPU / 12 GB RAM, arm64, not time-limited. Fallback: GCP e2-micro (1 GB, no local LLM).

## Alternatives considered

- AWS free tier — expires.
- GCP e2-micro as primary — 1 GB RAM can't hold Postgres + embeddings + llama.cpp.
- Home server — laptop can't be the always-on host.

## Consequences

- Everything must build and run on arm64.
- Oracle may reclaim instances idle for 7 days (CPU p95, network, and memory all < 20%); utilization checked in Sprint 6.
- A1 capacity can be scarce at creation time.
