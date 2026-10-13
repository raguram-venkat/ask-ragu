# ADR-0021: Hosted open-weight inference; no local model; optional Hugging Face Space

Status: proposed — resolve before sprint-5/task_2 starts
Date: 2026-10-13
Sprint: sprint-4 (raised during; work is sprint-5/task_2–3) · D-015

## Context

SPEC §10 had a local llama.cpp container as the last-resort provider, sized for an A1 (12 GB). The host is now a 1 GB Micro (ADR-0020), and the owner wants answers from open-weight models.

## Decision

The provider chain is 2–3 hosted free APIs that serve open-weight models, each with `trains_on_data=false` verified and dated (ADR-0009). Optionally, last in the chain: llama.cpp serving a 0.5–3B GGUF in a private Hugging Face Space on free CPU hardware, called through the same OpenAI-compatible adapter (the HF token is the bearer key). That attempt is timeboxed (90 min, sprint-5/task_3); if it fails, the chain is hosted-only.

## Alternatives considered

- llama.cpp on the Micro — no RAM: even a 0.5B model plus KV cache would starve Postgres and the embedder.
- Wait for an A1 — open-ended (ADR-0020).
- Closed-model free tiers — not open-weight, and some train on prompts (ADR-0009).
- Other free hosts for a model — Render/Koyeb free tiers have 512 MB; Colab/Kaggle are notebooks, not servers; credit-based platforms (Modal and similar) scale to zero with a monthly credit model.

## Consequences

- No provider is local: if every hosted provider fails and the Space is asleep or gone, /chat says the answer is unavailable (retrieval and /search still work).
- The Space sleeps after inactivity, so it cold-starts in minutes: long timeout, last in the chain. Don't keep it awake with pings.
- Snippets still leave the host only at query time (SPEC §4 unchanged).
- If an A1 ever arrives, a local provider can come back (BACKLOG), as a new D-entry, not an edit of this one.
