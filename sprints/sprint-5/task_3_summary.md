# Task 3 — Local llama.cpp provider + model bake-off

Status: todo
Est: 90m
Spec: SPEC.md §10

What: llama.cpp server container (arm64) serving a small quantized instruct model, called through the same OpenAI-compatible adapter.

Approach: Try 2-3 current 1-4B instruct models as Q4_K_M GGUF; measure tokens/sec, RAM, and quality on 5 eval questions; pick one; limit threads to leave a core for the app.

Read first:

- llama.cpp docs/docker.md (official `ghcr.io/ggml-org/llama.cpp:server`, arm64)
- llama.cpp server README (OpenAI-compatible endpoints)

Watch out for:

- 2 OCPUs → expect single-digit tokens/sec: long timeout, last in the chain.
- Model file in a volume, downloaded once; pin filename + checksum.
- Model + KV cache for your context size must fit Sprint 1's RAM budget.
- Internal network only — never publish its port.

Done when: Bake-off table below; local provider answers when every hosted provider is disabled.

## Bake-off

| Model (GGUF) | tokens/s | RAM | Quality (5 Qs) |
|---|---|---|---|
| | | | |

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
