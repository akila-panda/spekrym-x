"""Analyst routes (Phase 9C-2).

GET  /analyst/status          provider health and usage estimates; makes NO provider call
GET  /analyst/brief           the newest saved brief, or an empty state; makes NO provider call
POST /analyst/brief?force=    builds the evidence packet and generates a brief (spends free quota;
                              a saved brief for an unchanged packet is returned without a call)
The analyst writes prose from evidence only. Nothing here can place an order.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request

from sx_assistant.analyst.brief import LABELS
from sx_assistant.analyst.packet import build_packet
from sx_assistant.premarket.builder import build_premarket

router = APIRouter()


@router.get("/analyst/status")
def status(request: Request) -> dict:
    return request.app.state.analyst.status()


@router.get("/analyst/brief")
def latest_brief(request: Request) -> dict:
    saved = request.app.state.analyst.latest()
    if saved is None:
        return {"status": "none", "brief": None, "labels": LABELS,
                "note": "No brief has been generated yet."}
    return {"status": "ready", "brief": saved["brief"], "saved_at": saved["saved_at"],
            "labels": LABELS}


@router.post("/analyst/brief")
def make_brief(request: Request, instrument: str = "EUR_USD",
               as_of: str | None = Query(None, description="UTC ISO time; default = newest bar"),
               force: bool = False) -> dict:
    st = request.app.state
    if instrument not in st.source.instruments():
        raise HTTPException(404, f"unknown instrument {instrument!r}")
    try:
        t = (datetime.fromisoformat(as_of.replace("Z", "+00:00")).astimezone(UTC)
             if as_of else st.source.last_close(instrument))
        packet = build_packet(build_premarket(st.source, instrument, t))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return st.analyst.generate(packet, force=force)
