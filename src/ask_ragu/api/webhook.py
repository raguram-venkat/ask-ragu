"""POST /webhook: GitHub push -> verify -> 202 -> background sync (SPEC §8 step 1, D-001)."""

import hashlib
import hmac
import json
from collections import deque

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from ask_ragu import db
from ask_ragu.index.full import index_full
from ask_ragu.index.runner import SyncRunner
from ask_ragu.settings import settings

router = APIRouter()


def _sync() -> None:
    # ponytail: full index until Task 8 adds git fetch + incremental diff.
    with db.connect() as conn:
        index_full(conn, settings.vault_path)


runner = SyncRunner(_sync)
# In memory: a restart forgets them, which is fine because a re-run sync is idempotent.
seen = deque(maxlen=settings.webhook_seen_deliveries)


def signature_ok(body: bytes, header: str | None) -> bool:
    if not settings.webhook_secret:  # an empty key is trivially forgeable: refuse everything
        return False
    expected = (
        "sha256=" + hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    )
    return header is not None and hmac.compare_digest(expected, header)  # constant time


@router.post("/webhook", status_code=202)
async def webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
    x_github_delivery: str | None = Header(None),
):
    body = await request.body()  # raw bytes: the HMAC is over exactly what GitHub sent
    if not signature_ok(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="bad signature")
    if x_github_event == "ping":
        return JSONResponse({"status": "pong"}, status_code=200)
    if x_github_delivery in seen:  # GitHub redelivers; checked after the HMAC so junk can't fill it
        return {"status": "duplicate"}
    seen.append(x_github_delivery)

    if x_github_event != "push":
        return {"status": "ignored", "reason": f"event {x_github_event}"}
    try:
        payload = json.loads(body)
        default = f"refs/heads/{payload['repository']['default_branch']}"
        ref = payload["ref"]
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=400, detail="not a push payload") from None
    if ref != default:
        return {"status": "ignored", "reason": f"ref {ref}"}

    runner.trigger()  # returns at once; the sync runs in its own thread
    return {"status": "queued"}
