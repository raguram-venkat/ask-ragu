from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/chat")
def chat() -> None:
    raise HTTPException(status_code=501, detail="not implemented (Sprint 5)")
