from __future__ import annotations

from pydantic import model_validator

from sx_core.contracts._base import Contract, Tf, UtcDatetime


class Candle(Contract):
    """One OHLCV bar. ``time`` is the bar open (UTC). Only ``complete`` bars enter analysis."""

    instrument: str
    tf: Tf
    time: UtcDatetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid_close: float | None = None
    ask_close: float | None = None
    complete: bool

    @model_validator(mode="after")
    def _ohlc_in_order(self) -> Candle:
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("OHLC out of order")
        return self
