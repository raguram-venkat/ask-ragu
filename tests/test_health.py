from fastapi.testclient import TestClient

from ask_ragu import db
from ask_ragu.main import app

client = TestClient(app)  # not used as a context manager, so startup migrations don't run


def test_healthz_db_down(monkeypatch):
    def refuse():
        raise OSError("connection refused")

    monkeypatch.setattr(db, "connect", refuse)
    r = client.get("/healthz")
    assert r.status_code == 503
    assert r.json()["db"] == "down"
