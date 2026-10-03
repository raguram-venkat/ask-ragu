from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/webhook")
def webhook() -> None:
    raise HTTPException(status_code=501, detail="not implemented (Sprint 2)")
