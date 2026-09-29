# Task 7 — Webhook receiver

Status: todo
Est: 90m
Spec: SPEC.md §8, §15 · D-001, ADR-0005

What: POST /webhook verifies the signature, filters events, dedupes deliveries, returns 202 immediately, and triggers a background sync.

Approach: HMAC-SHA256 over the raw body vs `X-Hub-Signature-256`, constant-time compare; accept `push` to the default branch, answer `ping` with 200; remember recent `X-GitHub-Delivery` ids; hand off to a single-flight runner with a dirty flag that coalesces pushes arriving mid-run.

Read first:

- GitHub docs: Validating webhook deliveries
- GitHub docs: Best practices for using webhooks (10 s timeout, redelivery)

Watch out for:

- Never index inside the request: GitHub fails deliveries after 10 s (D-001).
- Compute the HMAC on raw bytes before any JSON parsing.
- Payload data never reaches a shell; the sync reads git itself.
- A crash drops the in-flight job — fine, Task 8's startup reconciliation catches up.

Done when: GitHub's Recent Deliveries shows 202s; a curl with a wrong signature gets 401; redelivery is a no-op.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
