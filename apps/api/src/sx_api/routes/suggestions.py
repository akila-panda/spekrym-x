from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request

from sx_api.suggestions import build_payload

router = APIRouter()


def _parse(value: str) -> datetime:
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(422, f"as_of is not an ISO-8601 time: {value!r}") from exc
    if t.tzinfo is None:
        raise HTTPException(422, "as_of must include a timezone, for example ...Z")
    return t.astimezone(UTC)


@router.get("/suggestions")
def suggestions(request: Request, instrument: str = "EUR_USD",
                as_of: str | None = Query(None, description="UTC ISO time; default = newest bar")
                ) -> dict:
    st = request.app.state
    if instrument not in st.source.instruments():
        raise HTTPException(404, f"unknown instrument {instrument!r}")
    t = _parse(as_of) if as_of else st.source.last_close(instrument)
    try:
        return build_payload(st.source, instrument, t, st.model_dir, st.rules_path, st.cache)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
