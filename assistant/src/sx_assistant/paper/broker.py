"""Paper broker interface. Paper backends only: no live backend exists (principle 2)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sx_core.contracts import PaperOrder
from sx_core.contracts._base import Side
from sx_core.contracts.paper_order import Backend

PAPER_BACKENDS: tuple[Backend, ...] = ("sim", "oanda_practice", "ib_paper")


class BrokerError(Exception):
    """A broker was used wrongly (for example quotes out of time order)."""


@dataclass(frozen=True)
class Quote:
    """One known bid/ask pair. ``time`` is when it was known (a bar close, never earlier)."""

    time: datetime
    bid: float
    ask: float

    def __post_init__(self) -> None:
        if self.time.tzinfo is None or self.time.utcoffset() is None:
            raise ValueError("quote time must be timezone-aware")
        if not (math.isfinite(self.bid) and math.isfinite(self.ask)):
            raise ValueError("bid and ask must be finite")
        if self.bid <= 0 or self.bid > self.ask:
            raise ValueError("need 0 < bid <= ask")


@dataclass(frozen=True)
class OrderRequest:
    """What a suggestion asks the broker to do. ``entry`` is a limit-style touch price."""

    suggestion_id: str
    side: Side
    units: float
    entry: float
    stop: float
    target: float
    rules_version: str


class RiskGate(Protocol):
    """A pre-trade check. Return a reason to reject, or ``None`` to allow (Phase 6B)."""

    name: str

    def check(self, req: OrderRequest, quote: Quote, open_orders: list[PaperOrder]) -> str | None:
        ...


class PaperBroker(Protocol):
    backend: Backend

    def submit(self, req: OrderRequest, quote: Quote) -> PaperOrder: ...
    def on_quote(self, quote: Quote) -> list[PaperOrder]: ...
    def cancel(self, order_id: str, quote: Quote) -> PaperOrder: ...
    def close_all(self, quote: Quote) -> list[PaperOrder]: ...
    def orders(self) -> list[PaperOrder]: ...
