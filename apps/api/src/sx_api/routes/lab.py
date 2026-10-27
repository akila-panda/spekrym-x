from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/lab")
def lab() -> dict:
    return {"status": "not_built", "items": [], "note": "Placeholder; built in a later phase."}
