from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/suggestions")
def suggestions() -> dict:
    return {"status": "not_built", "items": [], "note": "Placeholder; built in a later phase."}
