"""GET /index/status: what the index holds and how the last sync went (SPEC §8)."""

from fastapi import APIRouter

from ask_ragu import db
from ask_ragu.index.full import settings_hash
from ask_ragu.index.sync import runner

router = APIRouter()


@router.get("/index/status")
def index_status() -> dict:
    with db.connect() as conn:
        state = conn.execute(
            "SELECT last_commit, embedding_model, settings_hash, embed_version, parse_version,"
            " updated_at FROM index_state"
        ).fetchone()
        notes, chunks = conn.execute(
            "SELECT (SELECT count(*) FROM notes), (SELECT count(*) FROM chunks)"
        ).fetchone()
    last_commit, model, stored_hash, embed_v, parse_v, indexed_at = state or (None,) * 6
    return {
        "last_commit": last_commit,
        "embedding_model": model,
        "code_versions": {"embed": embed_v, "parse": parse_v},  # which code built the index
        # False = the next sync will be a full index because .env index settings changed
        "settings_current": stored_hash == settings_hash(),
        "indexed_at": indexed_at,
        "notes": notes,
        "chunks": chunks,
        "sync_running": runner.running,
        "last_sync": runner.last,  # None until a sync has run in this process
    }
