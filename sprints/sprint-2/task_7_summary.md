# Task 7 — Webhook receiver

Status: done
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
- No public URL yet (D-008): test with requests you sign yourself using the same secret. GitHub can't reach the laptop, and that's fine.

Done when: a correctly signed local request gets 202, a wrong signature gets 401, and a repeated delivery id is a no-op. GitHub's Recent Deliveries check happens once the A1 is live (D-008).

---

Filled in while working

Files touched:

- `src/ask_ragu/api/webhook.py` — `POST /webhook`: HMAC → ping → dedupe → event/branch filter → `runner.trigger()` → 202
- `src/ask_ragu/index/runner.py` — `SyncRunner`: single-flight background thread + dirty flag (ADR-0005)
- `src/ask_ragu/main.py` — `logging.basicConfig` so `ask_ragu.*` logs (the background sync) show up next to uvicorn's
- `tests/test_webhook.py` — signed push → 202 queued; wrong/missing signature → 401; empty secret → 401; repeated delivery → duplicate; ping → 200; other events/branches → ignored; bad payload → 400; runner coalescing
- `src/ask_ragu/settings.py`, `.env.example` — `WEBHOOK_SECRET`, `WEBHOOK_SEEN_DELIVERIES`

Decisions made here:

- Order of checks: raw body → HMAC (constant-time `hmac.compare_digest`) → ping → dedupe → parse JSON → event/branch. Dedupe sits after the signature check so unsigned requests can't fill the list; JSON is parsed only after the signature is known good.
- Default branch comes from the payload (`repository.default_branch`), not config: renaming the branch on GitHub needs no `.env` change.
- Status codes: 202 for everything accepted (queued, duplicate, ignored), 200 for ping, 401 for a bad signature, 400 for a signed body that isn't a push payload. GitHub only cares about 2xx vs not.
- Empty `WEBHOOK_SECRET` rejects every request: an HMAC with an empty key is trivially forgeable.
- Runner = own daemon thread, not FastAPI `BackgroundTasks`: the sync isn't tied to a request, and the single-flight/dirty logic sits in one small class.
- Dedupe ids live in memory (`deque(maxlen=WEBHOOK_SEEN_DELIVERIES)`): a restart forgets them, harmless because a re-run sync is idempotent (ADR-0005).
- Until Task 8, the runner's job is `index_full` (idempotent, ~5 s when nothing changed); Task 8 swaps in `git fetch` + incremental diff. Marked `ponytail:` in code.

Gotchas:

- Live check against the running stack (requests signed with the `.env` secret): signed push 202 queued, same delivery 202 duplicate, wrong signature 401, ping 200. Three pushes in a row → exactly 2 sync runs (one + one coalesced).
- uvicorn only configures its own loggers, so `ask_ragu.*` INFO lines (the background sync) were silently dropped until `basicConfig` in `main.py`.
- The live GitHub → VM delivery check waits for the A1 (D-008). The secret set on the GitHub webhook must equal `WEBHOOK_SECRET` in the VM's `.env`.
