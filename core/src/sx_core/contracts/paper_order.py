from __future__ import annotations

from typing import Literal

from sx_core.contracts._base import Contract, Side, UtcDatetime

Backend = Literal["sim", "oanda_practice", "ib_paper"]
OrderState = Literal["pending", "filled", "closed", "rejected", "cancelled"]


class PaperOrder(Contract):
    """``id`` is the idempotent client order id (see ``ids.order_id``). Paper backends only."""

    id: str
    suggestion_id: str
    backend: Backend
    side: Side
    units: float
    entry: float
    stop: float
    target: float
    intended_fill: float
    actual_fill: float | None = None
    slippage: float | None = None
    state: OrderState
    opened_at: UtcDatetime | None = None
    closed_at: UtcDatetime | None = None
    pnl: float | None = None
    rules_version: str
