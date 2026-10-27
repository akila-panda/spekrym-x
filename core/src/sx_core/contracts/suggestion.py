from __future__ import annotations

from pydantic import Field

from sx_core.contracts._base import Contract, Side, Tf, UtcDatetime
from sx_core.labels import SuggestionStatus


class Reason(Contract):
    text: str
    evidence_id: str = Field(min_length=1)  # a Setup or Forecast id; no claim without evidence


class Gate(Contract):
    name: str
    passed: bool
    detail: str


class Suggestion(Contract):
    """``score`` is a heuristic ranking, NOT a probability."""

    id: str
    instrument: str
    tf: Tf
    created_at: UtcDatetime
    setup_ids: list[str]
    forecast_id: str | None = None
    side: Side
    entry: float
    stop: float
    target: float
    score: float
    reasons: list[Reason]
    gates: list[Gate]
    rules_version: str
    status: SuggestionStatus
