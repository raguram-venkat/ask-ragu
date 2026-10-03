from fastapi import APIRouter, Response

from ask_ragu import db

router = APIRouter()


@router.get("/healthz")
def healthz(response: Response) -> dict[str, str]:
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
            has_vector = conn.execute(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
    except Exception:
        response.status_code = 503
        return {"status": "error", "db": "down", "vector": "unknown"}

    if not has_vector:
        response.status_code = 503
        return {"status": "error", "db": "ok", "vector": "missing"}
    return {"status": "ok", "db": "ok", "vector": "ok"}
