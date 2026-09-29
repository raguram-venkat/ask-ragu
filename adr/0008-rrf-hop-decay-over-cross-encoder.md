# ADR-0008: RRF + hop decay over a cross-encoder reranker

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Need to merge lexical and vector rankings and weigh graph-expanded notes against direct matches.

## Decision

Reciprocal Rank Fusion for seeds; similarity × hop decay × note_type prior for expanded notes.

## Alternatives considered

- Cross-encoder reranker — usually better ranking, but another model in RAM and seconds of CPU per query on ARM.
- Weighted sum of raw scores — ts_rank and cosine live on incomparable scales.

## Consequences

- No extra model; cheap and explainable score breakdowns.
- Reranker stays in BACKLOG, gated on the Sprint 4 ablation showing ranking (not recall) is the gap.
