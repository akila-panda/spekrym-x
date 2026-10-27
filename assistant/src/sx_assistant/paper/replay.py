"""Scripted replay of quotes and order requests through a broker (deterministic)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from sx_assistant.paper.broker import OrderRequest, PaperBroker, Quote
from sx_core.clock import bar_close
from sx_core.contracts import Candle


def quotes_from_candles(candles: Sequence[Candle]) -> list[Quote]:
    """One quote per CLOSED bar, known at the bar close (open + timeframe), from bid/ask close."""
    out = []
    for c in candles:
        if c.complete and c.bid_close is not None and c.ask_close is not None:
            out.append(Quote(bar_close(c.time, c.tf), c.bid_close, c.ask_close))
    return out


def replay(broker: PaperBroker, quotes: Sequence[Quote],
           schedule: Mapping[int, Sequence[OrderRequest]]) -> None:
    """For each quote: update existing orders first, then submit requests due at that index."""
    for i, q in enumerate(quotes):
        broker.on_quote(q)
        for req in schedule.get(i, ()):
            broker.submit(req, q)
