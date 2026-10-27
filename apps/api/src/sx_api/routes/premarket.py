from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request

from sx_assistant.premarket.builder import build_premarket
from sx_assistant.premarket.chart_payload import build_payload

router = APIRouter()


def _parse(value: str) -> datetime:
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(422, f"as_of is not an ISO-8601 time: {value!r}") from exc
    if t.tzinfo is None:
        raise HTTPException(422, "as_of must include a timezone, for example ...Z")
    return t.astimezone(UTC)


@router.get("/premarket")
def premarket(request: Request, instrument: str = "EUR_USD",
              as_of: str | None = Query(None, description="UTC ISO time; default = newest bar")
              ) -> dict:
    source, cache = request.app.state.source, request.app.state.cache
    if instrument not in source.instruments():
        raise HTTPException(404, f"unknown instrument {instrument!r}")
    t = _parse(as_of) if as_of else source.last_close(instrument)
    key = (instrument, t)
    if key not in cache:
        try:
            cache[key] = build_payload(build_premarket(source, instrument, t))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    return cache[key]
