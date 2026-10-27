"""Intended vs actual fills, slippage and P&L; optional append-only ledger logging."""

from __future__ import annotations

from dataclasses import dataclass

from sx_core.contracts import PaperOrder
from sx_core.ledger import Ledger


@dataclass(frozen=True)
class Summary:
    submitted: int
    filled: int  # filled or closed
    closed: int
    rejected: int
    total_pnl: float  # closed trades only, bid/ask fills, in quote currency
    mean_slippage: float | None  # price units, positive = worse than intended
    label: str = "Paper only. Not validated. Small samples mean nothing."


def summarize(orders: list[PaperOrder]) -> Summary:
    filled = [o for o in orders if o.actual_fill is not None]
    closed = [o for o in orders if o.state == "closed"]
    slips = [o.slippage for o in filled if o.slippage is not None]
    return Summary(
        submitted=len(orders), filled=len(filled), closed=len(closed),
        rejected=sum(o.state == "rejected" for o in orders),
        total_pnl=round(sum(o.pnl or 0.0 for o in closed), 6),
        mean_slippage=round(sum(slips) / len(slips), 6) if slips else None)


class Tracker:
    """Use ``tracker.record`` as a ``SimBroker`` listener to log every order event."""

    def __init__(self, ledger: Ledger | None = None, data_version: str = "sim") -> None:
        self.ledger = ledger
        self.data_version = data_version
        self.events: list[tuple[str, str, str]] = []  # (event, order id, detail)

    def record(self, event: str, order: PaperOrder, detail: str) -> None:
        self.events.append((event, order.id, detail))
        if self.ledger is not None:
            self.ledger.append(event, {"order": order.to_wire(), "detail": detail},
                               self.data_version, rules_version=order.rules_version)
