"""Internal simulator: bid/ask fills plus slippage, deterministic, no wall clock.

Rules (documented limits, not market truth):
- An entry is a touch order: long fills when ask <= entry, short when bid >= entry, at the
  touching quote's ask (bid) with slippage against the trader. ``slippage`` on the order is
  actual minus intended for a long, intended minus actual for a short (positive = worse).
- Stops fill at the quote's bid (long) or ask (short) with slippage against the trader.
  Targets fill at the target price exactly (no price improvement).
- Only quotes are seen, so a move inside a bar that never shows in a quote is missed.
- No commission, no swap, no partial fills. P&L is in quote currency, from fills only.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime

from sx_assistant.paper.broker import BrokerError, OrderRequest, Quote, RiskGate
from sx_assistant.paper.orders import KillSwitch, request_order_id, validate_request
from sx_core.config import enforce_paper_mode
from sx_core.contracts import PaperOrder

Listener = Callable[[str, PaperOrder, str], None]
DEFAULT_SLIPPAGE = 0.00002  # 0.2 pip on EUR/USD; provisional, configurable


def _r(x: float) -> float:
    return round(x, 6)


class SimBroker:
    backend = "sim"

    def __init__(self, *, slippage: float = DEFAULT_SLIPPAGE, gates: Sequence[RiskGate] = (),
                 kill_switch: KillSwitch | None = None, listener: Listener | None = None,
                 env: Mapping[str, str] | None = None) -> None:
        enforce_paper_mode(env)
        if slippage < 0:
            raise ValueError("slippage must be >= 0")
        self._slip = slippage
        self._gates = tuple(gates)
        self.kill_switch = kill_switch or KillSwitch()
        self._listener = listener
        self._orders: dict[str, PaperOrder] = {}
        self._last: datetime | None = None

    # ---- public --------------------------------------------------------------------
    def orders(self) -> list[PaperOrder]:
        return list(self._orders.values())

    def submit(self, req: OrderRequest, quote: Quote) -> PaperOrder:
        self._tick(quote)
        oid = request_order_id(req, self.backend)
        if oid in self._orders:  # idempotent: same suggestion and rules, same order
            return self._orders[oid]
        order = PaperOrder(id=oid, suggestion_id=req.suggestion_id, backend="sim", side=req.side,
                           units=req.units, entry=req.entry, stop=req.stop, target=req.target,
                           intended_fill=req.entry, state="pending",
                           rules_version=req.rules_version)
        reason = self._refusal(req, quote)
        if reason:
            order = order.model_copy(update={"state": "rejected"})
            self._store(order, "order_rejected", reason)
            return order
        self._store(order, "order_submitted", "")
        return self._step(order, quote)

    def on_quote(self, quote: Quote) -> list[PaperOrder]:
        self._tick(quote)
        changed = []
        for order in list(self._orders.values()):
            new = self._step(order, quote)
            if new is not order:
                changed.append(new)
        return changed

    def cancel(self, order_id: str, quote: Quote) -> PaperOrder:
        self._tick(quote)
        order = self._orders[order_id]
        if order.state != "pending":
            return order
        order = order.model_copy(update={"state": "cancelled", "closed_at": quote.time})
        self._store(order, "order_cancelled", "")
        return order

    def cancel_all_pending(self, quote: Quote) -> list[PaperOrder]:
        return [self.cancel(o.id, quote) for o in self.orders() if o.state == "pending"]

    def close_all(self, quote: Quote) -> list[PaperOrder]:
        """Close every open position at the current quote with slippage against the trader."""
        self._tick(quote)
        out = []
        for o in self.orders():
            if o.state == "filled":
                px = quote.bid - self._slip if o.side == "long" else quote.ask + self._slip
                out.append(self._close(o, px, quote.time, "manual_close"))
        return out

    # ---- internals -----------------------------------------------------------------
    def _tick(self, quote: Quote) -> None:
        if self._last is not None and quote.time < self._last:
            raise BrokerError("quotes must arrive in time order")
        self._last = quote.time

    def _refusal(self, req: OrderRequest, quote: Quote) -> str | None:
        if self.kill_switch.tripped:
            return f"kill switch: {self.kill_switch.reason}"
        bad = validate_request(req)
        if bad:
            return bad
        open_orders = [o for o in self._orders.values() if o.state in ("pending", "filled")]
        for gate in self._gates:
            why = gate.check(req, quote, open_orders)
            if why:
                return f"gate {gate.name}: {why}"
        return None

    def _step(self, o: PaperOrder, q: Quote) -> PaperOrder:
        long = o.side == "long"
        if o.state == "pending":
            if long and q.ask <= o.entry:
                fill = _r(q.ask + self._slip)
            elif not long and q.bid >= o.entry:
                fill = _r(q.bid - self._slip)
            else:
                return o
            slip = _r(fill - o.intended_fill if long else o.intended_fill - fill)
            new = o.model_copy(update={"state": "filled", "actual_fill": fill, "slippage": slip,
                                       "opened_at": q.time})
            self._store(new, "order_filled", "")
            return new
        if o.state != "filled" or (o.opened_at is not None and q.time <= o.opened_at):
            return o  # never exit on the quote that filled the order
        if long:
            if q.bid <= o.stop:
                return self._close(o, q.bid - self._slip, q.time, "stop")
            if q.bid >= o.target:
                return self._close(o, o.target, q.time, "target")
        else:
            if q.ask >= o.stop:
                return self._close(o, q.ask + self._slip, q.time, "stop")
            if q.ask <= o.target:
                return self._close(o, o.target, q.time, "target")
        return o

    def _close(self, o: PaperOrder, px: float, when: datetime, why: str) -> PaperOrder:
        assert o.actual_fill is not None
        sign = 1 if o.side == "long" else -1
        pnl = _r(sign * (px - o.actual_fill) * o.units)
        new = o.model_copy(update={"state": "closed", "closed_at": when, "pnl": pnl})
        self._store(new, "order_closed", f"{why} at {_r(px)}")
        return new

    def _store(self, o: PaperOrder, event: str, detail: str) -> None:
        self._orders[o.id] = o
        if self._listener:
            self._listener(event, o, detail)
