"""Higher-timeframe checklist: plain facts from closed D and H4 bars. No bias verdict.

Each item states what the closed bars show and carries the bar times it used. Nothing here is a
forecast, a score or a probability, and nothing says buy or sell.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sx_assistant.ta.common import fmt_price
from sx_core.clock import bar_close
from sx_core.contracts import Candle

H4_LOOKBACK = 6


@dataclass(frozen=True)
class ChecklistItem:
    id: str
    tf: str
    text: str
    known_at: datetime        # close of the newest bar the statement used

    def to_wire(self) -> dict[str, str]:
        return {"id": self.id, "tf": self.tf, "text": self.text,
                "known_at": self.known_at.strftime("%Y-%m-%dT%H:%M:%SZ")}


def _daily(d: Sequence[Candle]) -> list[ChecklistItem]:
    if len(d) < 2:
        return []
    last, prev = d[-1], d[-2]
    known = bar_close(last.time, "D")
    inst = last.instrument
    if last.close > prev.high:
        rel = f"above the previous daily high {fmt_price(prev.high, inst)}"
    elif last.close < prev.low:
        rel = f"below the previous daily low {fmt_price(prev.low, inst)}"
    else:
        rel = (f"inside the previous daily range {fmt_price(prev.low, inst)} to "
               f"{fmt_price(prev.high, inst)}")
    direction = "up" if last.close > last.open else "down" if last.close < last.open else "flat"
    out = [ChecklistItem("d_close_vs_prev", "D",
                         f"Last closed day ({last.time:%Y-%m-%d}) closed {direction} and {rel}.",
                         known)]
    hh, hl = last.high > prev.high, last.low > prev.low
    lh, ll = last.high < prev.high, last.low < prev.low
    seq = ("a higher high and higher low" if hh and hl else
           "a lower high and lower low" if lh and ll else
           "an outside day (higher high, lower low)" if hh and ll else
           "an inside day (lower high, higher low)" if lh and hl else
           "a mixed day relative to the previous one")
    out.append(ChecklistItem("d_sequence", "D", f"That day made {seq}.", known))
    return out


def _h4(h: Sequence[Candle]) -> list[ChecklistItem]:
    if len(h) < 2:
        return []
    window = h[-H4_LOOKBACK:]
    lo, hi, last = min(c.low for c in window), max(c.high for c in window), window[-1]
    if hi <= lo:
        return []
    pos = (last.close - lo) / (hi - lo)
    where = "upper third" if pos >= 2 / 3 else "lower third" if pos <= 1 / 3 else "middle third"
    inst = last.instrument
    return [ChecklistItem(
        "h4_range_position", "H4",
        f"Last H4 close {fmt_price(last.close, inst)} sits in the {where} of the last "
        f"{len(window)} H4 bars' range ({fmt_price(lo, inst)} to {fmt_price(hi, inst)}).",
        bar_close(last.time, "H4"))]


def build_checklist(daily: Sequence[Candle], h4: Sequence[Candle]) -> list[ChecklistItem]:
    """Facts from the closed bars given. The caller must pass only bars closed by ``as_of``."""
    return _daily(daily) + _h4(h4)
