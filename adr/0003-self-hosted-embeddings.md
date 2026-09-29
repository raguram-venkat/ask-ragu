# ADR-0003: Self-hosted embeddings (fastembed, bge-small-en-v1.5)

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Indexing embeds every changed chunk on every push; the privacy principle (SPEC §4) says note content shouldn't leave the host during indexing.

## Decision

Embed in-process with fastembed (ONNX, no PyTorch) using BAAI/bge-small-en-v1.5, 384 dimensions.

## Alternatives considered

- Hosted embedding API — better models, but ships every note off-box on every push and adds a rate-limited dependency.
- sentence-transformers + PyTorch — heavier image and RAM on ARM.
- Hugging Face TEI container — another service to run.

## Consequences

- Zero cost, no network dependency at index time.
- English-centric, smaller model; quality checked in the Sprint 4 ablation.
- Changing models means a migration (vector dimension) and a full re-embed; `index_state` records the model to detect mismatch.
