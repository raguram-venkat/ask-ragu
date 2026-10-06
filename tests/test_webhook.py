import hashlib
import hmac
import json
import threading
import time
from collections import deque
from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

from ask_ragu import db
from ask_ragu.api import webhook
from ask_ragu.index.runner import SyncRunner
from ask_ragu.main import app
from ask_ragu.settings import settings

client = TestClient(app)  # not a context manager: startup migrations don't run
SECRET = "test-secret"
PUSH = {"ref": "refs/heads/main", "repository": {"default_branch": "main"}}


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(settings, "webhook_secret", SECRET)
    monkeypatch.setattr(webhook, "seen", deque(maxlen=10))
    triggers = []
    monkeypatch.setattr(webhook.runner, "trigger", lambda: triggers.append(1))
    return triggers


def post(payload, event="push", delivery="d1", secret=SECRET):
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    headers = {"X-GitHub-Event": event, "X-GitHub-Delivery": delivery, "X-Hub-Signature-256": sig}
    return client.post("/webhook", content=body, headers=headers)


def test_signed_push_to_default_branch_queues_a_sync(setup):
    r = post(PUSH)
    assert (r.status_code, r.json()["status"], setup) == (202, "queued", [1])


def test_wrong_or_missing_signature_is_401(setup):
    assert post(PUSH, secret="wrong").status_code == 401
    assert (
        client.post("/webhook", content=b"{}", headers={"X-GitHub-Event": "push"}).status_code
        == 401
    )
    assert setup == []


def test_empty_secret_rejects_even_matching_signature(monkeypatch):
    monkeypatch.setattr(settings, "webhook_secret", "")
    assert post(PUSH, secret="").status_code == 401


def test_repeated_delivery_is_a_no_op(setup):
    assert post(PUSH, delivery="same").json()["status"] == "queued"
    assert post(PUSH, delivery="same").json()["status"] == "duplicate"
    assert setup == [1]


def test_ping_and_ignored_events(setup):
    assert post({"zen": "hi"}, event="ping").status_code == 200
    assert post(PUSH, event="issues", delivery="d2").json()["status"] == "ignored"
    other = {**PUSH, "ref": "refs/heads/feature"}
    assert post(other, delivery="d3").json()["status"] == "ignored"
    assert post({"no": "ref"}, delivery="d4").status_code == 400
    assert setup == []


def test_runner_is_single_flight_and_coalesces():
    started, release, runs = threading.Event(), threading.Event(), []

    def job():
        runs.append(1)
        started.set()
        release.wait(5)

    r = SyncRunner(job)
    assert r.trigger() is True
    started.wait(5)
    # three pushes while the first run is busy: no new thread, one pending re-run
    assert [r.trigger() for _ in range(3)] == [False, False, False]
    release.set()
    for _ in range(100):  # wait for the worker to finish both runs
        if not r._running:
            break
        time.sleep(0.05)
    assert runs == [1, 1]


def test_runner_records_last_outcome():
    r = SyncRunner(lambda: 1 / 0)
    r.trigger()
    for _ in range(100):
        if r.last:
            break
        time.sleep(0.05)
    assert r.last["ok"] is False and "ZeroDivisionError" in r.last["error"]


def test_index_status(conn, monkeypatch):
    db.migrate(conn)
    monkeypatch.setattr(db, "connect", lambda: nullcontext(conn))  # use the test schema
    body = client.get("/index/status").json()
    assert (body["notes"], body["last_commit"], body["sync_running"]) == (0, None, False)
