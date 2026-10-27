"""Shared building blocks for the contract models."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer

Tf = Literal["M1", "M5", "M15", "M30", "H1", "H4", "D"]
Direction = Literal["bullish", "bearish", "neutral"]
Side = Literal["long", "short"]


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    return value.astimezone(UTC)


def format_utc(value: datetime) -> str:
    """ISO-8601 with a trailing ``Z``; sub-seconds only when non-zero (zod ``iso.datetime``)."""
    value = value.astimezone(UTC)
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ" if value.microsecond else "%Y-%m-%dT%H:%M:%SZ"
    return value.strftime(fmt)


UtcDatetime = Annotated[
    datetime, AfterValidator(_to_utc), PlainSerializer(format_utc, return_type=str)
]


class Contract(BaseModel):
    """Base: immutable, no unknown fields, no NaN or infinity in floats."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    def to_wire(self) -> dict[str, Any]:
        """JSON-ready dict for the web app: ISO ``Z`` times, unset optional fields omitted.

        zod's ``.optional()`` accepts a missing key but rejects ``null``, so ``None``
        model fields are dropped. Values inside free-form dicts (``payload``) are kept.
        """
        out: dict[str, Any] = json.loads(self.model_dump_json(exclude_none=True))
        return out
