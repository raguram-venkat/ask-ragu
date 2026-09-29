# Task 3 — Security pass

Status: todo
Est: 75m
Spec: SPEC.md §15 · ADR-0014

What: Verify auth, rate limiting, secrets, container users, and exposed ports.

Approach: Basic auth everywhere except /webhook and /healthz; app-level rate limit on /chat and /search; gitleaks over full history; `nmap` from outside; non-root containers, read-only root filesystem where easy.

Read first:

- OWASP API Security Top 10 (skim)
- gitleaks README

Watch out for:

- /healthz must not leak versions or internal hostnames.
- Rotate the webhook secret and basic-auth password once, to prove the procedure works.

Done when: Findings table here; every high fixed.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
