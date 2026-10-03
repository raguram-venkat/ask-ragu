from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    # Sprint 1 Task 2 adds the DB + pgvector check.
    return {"status": "ok"}
