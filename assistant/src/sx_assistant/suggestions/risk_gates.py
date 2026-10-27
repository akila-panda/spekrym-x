"""Pre-trade risk gates. The runner builds them from a frozen rule set and gives them to the
broker, so they apply to every order. Each returns a reason to reject, or ``None``."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime

from sx_assistant.paper.broker import OrderRequest, Quote
from sx_assistant.rules.ruleset import Blackout
from sx_core.contracts import PaperOrder


class NewsBlackoutGate:
    name = "news_blackout"

    def __init__(self, windows: Sequence[Blackout]) -> None:
        self._windows = tuple(windows)

    def check(self, req: OrderRequest, quote: Quote, open_orders: list[PaperOrder]) -> str | None:
        for w in self._windows:
            if w.start <= quote.time < w.end:
                return f"inside blackout '{w.label}'"
        return None


class MaxOpenTradesGate:
    """Counts pending and filled orders, so a pile of unfilled orders cannot bypass the cap."""

    name = "max_open_trades"

    def __init__(self, limit: int) -> None:
        self._limit = limit

    def check(self, req: OrderRequest, quote: Quote, open_orders: list[PaperOrder]) -> str | None:
        if len(open_orders) >= self._limit:
            return f"{len(open_orders)} open or pending orders, limit {self._limit}"
        return None


class DailyLossGate:
    """Halts new orders once realized losses for the quote's UTC day reach the limit."""

    name = "daily_loss_halt"

    def __init__(self, limit: float, realized_on: Callable[[datetime], float]) -> None:
        self._limit = limit
        self._realized_on = realized_on

    def check(self, req: OrderRequest, quote: Quote, open_orders: list[PaperOrder]) -> str | None:
        pnl = self._realized_on(quote.time)
        if pnl <= -self._limit:
            return f"realized {pnl:.2f} today, loss limit {self._limit:.2f}"
        return None
