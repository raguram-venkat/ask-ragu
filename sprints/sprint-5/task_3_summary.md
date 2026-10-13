# Task 3 — Self-hosted small model in a private Hugging Face Space (timebox)

Status: todo — re-scoped 2026-10-13 by D-015 (was: local llama.cpp container on the A1)
Est: 90m, hard timebox
Spec: SPEC.md §10 · D-015, ADR-0021

What: llama.cpp serving one small quantized instruct model in a private Hugging Face Space on free CPU hardware, called through the same OpenAI-compatible adapter, last in the chain.

Approach: Docker Space `FROM ghcr.io/ggml-org/llama.cpp:server`; the GGUF (0.5–3B, Q4_K_M) is downloaded at container start from the HF Hub, filename + SHA256 pinned in Space variables; `llama-server` listens on port 7860 with `--ctx-size` sized to the context budget and `--threads` = the Space's vCPUs. Call `https://<owner>-<space>.hf.space/v1/chat/completions` with the HF read token as the API key: a private Space accepts `Authorization: Bearer <hf token>`, which is exactly what the adapter sends, so no code change.

Read first:

- Hugging Face docs: Docker Spaces, Spaces hardware (free CPU tier limits, sleep after inactivity), private Spaces
- llama.cpp server README (OpenAI-compatible endpoints) and docs/docker.md

Watch out for:

- Timebox: if it doesn't answer a smoke prompt through the adapter within 90 min, set Status `dropped` with the reason. The chain is then hosted-only, which D-015 already covers.
- The Space sleeps when idle and cold-starts in minutes: long timeout, last in `providers.yaml`, and the UI's loading state must say so. Don't keep it awake with pings.
- The Space is its own repo, separate from ask-ragu: no keys in it, model pulled at runtime. The HF token goes in ask-ragu's `.env`.
- Check that a private Space really rejects requests without the token (curl without the header → 401/404).

Done when: with every hosted provider disabled, /chat answers through the Space; bake-off table below (or Status `dropped` with the reason).

## Bake-off

| Model (GGUF) | tokens/s | Cold start | RAM | Quality (5 synthetic Qs) |
|---|---|---|---|---|
| | | | | |

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
