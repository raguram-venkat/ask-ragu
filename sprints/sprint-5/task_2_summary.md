# Task 2 — OpenAI-compatible adapter + hosted providers

Status: todo
Est: 75m
Spec: SPEC.md §10 · D-005, D-015, ADR-0009, ADR-0021

What: One adapter for any OpenAI-compatible endpoint, configured for 2-3 free hosted providers serving open-weight models (D-015).

Approach: Groq, Cerebras, OpenRouter (free models), GitHub Models, Cloudflare Workers AI and the NVIDIA API catalog all speak the chat-completions format — same code, different base_url/model/key. Only open-weight models; no provider is local any more, so keep ≥ 2 enabled at all times.

Read first:

- Each candidate's current free-tier limits and data-use terms — check on the day

Watch out for:

- Privacy (D-005): free tiers that train on prompts (e.g. Gemini free outside EU/UK/EEA, mid-2026) stay disabled unless you opt in.
- Free catalogs drop models without notice — log model errors loudly; keep ≥ 2 hosted providers.
- Keys in .env / Docker secrets, never in providers.yaml.

Done when: Each provider answers a smoke prompt; limits + data-policy table below, with the date checked.

## Providers checked

| Provider | Model | Open-weight? | Free limits | Trains on data? | Checked on |
|---|---|---|---|---|---|
| | | | | | |

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
