from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from sx_core.contracts._base import Contract, Direction, Tf, UtcDatetime
from sx_core.labels import SetupStatus

SetupKind = Literal["swing", "bos", "choch", "fvg", "order_block", "liquidity_sweep",
                    "session_level", "support_resistance", "candle_pattern"]
Lifecycle = Literal["fresh", "tested", "mitigated", "broken"]


class Geometry(Contract):
    """A box (``price_low < price_high``) or a line (equal), from ``t_start`` to ``t_end``."""

    price_low: float
    price_high: float
    t_start: UtcDatetime
    t_end: UtcDatetime | None = None


class Source(Contract):
    library: str
    version: str
    adapter: str


class Setup(Contract):
    """A detected structure or pattern; output of the TA adapters."""

    id: str = Field(min_length=1)
    kind: SetupKind
    instrument: str
    tf: Tf
    direction: Direction
    geometry: Geometry
    event_time: UtcDatetime
    known_at: UtcDatetime
    lifecycle: Lifecycle
    source: Source
    plain_text: str
    invalidation: str
    status: SetupStatus

    @model_validator(mode="after")
    def _checks(self) -> Setup:
        if self.geometry.price_low > self.geometry.price_high:
            raise ValueError("price_low above price_high")
        if self.known_at < self.event_time:
            raise ValueError("known_at before event_time")
        return self
