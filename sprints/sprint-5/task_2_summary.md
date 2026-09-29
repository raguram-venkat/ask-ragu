# Task 2 — OpenAI-compatible adapter + hosted providers

Status: todo
Est: 75m
Spec: SPEC.md §10 · D-005, ADR-0009

What: One adapter for any OpenAI-compatible endpoint, configured for 2-3 free hosted providers.

Approach: Groq, Cerebras, OpenRouter (free models), and GitHub Models all speak the chat-completions format — same code, different base_url/model/key.

Read first:

- Each candidate's current free-tier limits and data-use terms — check on the day

Watch out for:

- Privacy (D-005): free tiers that train on prompts (e.g. Gemini free outside EU/UK/EEA, mid-2026) stay disabled unless you opt in.
- Free catalogs drop models without notice — log model errors loudly; keep ≥ 2 hosted providers.
- Keys in .env / Docker secrets, never in providers.yaml.

Done when: Each provider answers a smoke prompt; limits + data-policy table below, with the date checked.

## Providers checked

| Provider | Model | Free limits | Trains on data? | Checked on |
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
