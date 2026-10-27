from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict:
    src = request.app.state.source.info
    return {"status": "ok", "trading_mode": "paper",
            "source": {"id": src.id, "label": src.label, "live": src.live}}
