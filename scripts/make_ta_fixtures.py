"""Regenerate the frozen Phase 4 TA fixtures (SYNTHETIC, hand-designed, not market data).

    python scripts/make_ta_fixtures.py

Prices are written as pips above 1.0800 so each bar is easy to check by hand. Everything under
``EXPECTED_*`` is a HAND-DERIVED label (worked out from the library definitions in
``sx_assistant/ta/smc_adapter.py``'s docstring), never copied from program output. The fixtures
are committed and hash-pinned by ``assistant/tests/test_fixtures.py``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "ta"
BASE = 1.0800


def px(pips: float) -> float:
    return round(BASE + pips * 0.0001, 5)


def candle(t: datetime, tf: str, o: float, h: float, lo: float, c: float) -> dict:
    return {"instrument": "EUR_USD", "tf": tf, "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": px(o), "high": px(h), "low": px(lo), "close": px(c), "volume": 100.0,
            "bid_close": px(c - 0.2), "ask_close": px(c + 0.2), "complete": True}


def chain(start: datetime, tf: str, step: timedelta, o0: float, closes: list[float],
          over: dict[int, dict[str, float]] | None = None) -> list[dict]:
    """Bars with open = previous close, 1-pip wicks, per-bar ``up``/``dn`` wick overrides."""
    over, out, o = over or {}, [], o0
    for i, c in enumerate(closes):
        w = over.get(i, {})
        out.append(candle(start + i * step, tf, o, max(o, c) + w.get("up", 1),
                          min(o, c) - w.get("dn", 1), c))
        o = c
    return out


M15 = timedelta(minutes=15)
D0 = datetime(2026, 10, 19, tzinfo=UTC)  # Monday; UK on BST, US on EDT

# --- labelled day: 28 M15 bars = exactly the Asia session (00:00-07:00 UTC) ---------------
DAY_CLOSES = [9, 8, 7, 6, 5, 6, 7, 8, 9, 10, 11, 12, 11, 10, 9, 8, 7, 8, 9, 15, 17, 19, 21,
              20, 19, 18, 17, 16]
DAY_OVER = {5: {"dn": 3}, 11: {"up": 4}, 16: {"dn": 4}, 21: {"dn": 2}, 22: {"up": 4, "dn": 3}}
DAY = chain(D0, "M15", M15, 10, DAY_CLOSES, DAY_OVER)

# continuation used only for lifecycle tests: (o, h, l, c) in pips, bars 28..32
TAIL_RAW = [(16, 17, 14, 15), (15, 16, 11, 12), (12, 13, 7, 8), (8, 9, 1, 2), (2, 3, 0, 1)]
TAIL = [candle(D0 + (28 + i) * M15, "M15", *b) for i, b in enumerate(TAIL_RAW)]


def t(i: int) -> str:
    return (D0 + i * M15).strftime("%Y-%m-%dT%H:%M:%SZ")


# swing_length=2: a swing needs 2 lower bars on its right, so it is known at close of bar i+2.
def exp(kind: str, direction: str, ev: int, kn: int, low: float, high: float | None = None):
    return {"kind": kind, "direction": direction, "event": t(ev), "known": t(kn),
            "low": px(low), "high": px(low if high is None else high)}


EXPECTED_DAY = [
    exp("swing", "bullish", 5, 8, 2),
    exp("swing", "bearish", 11, 14, 16),
    exp("swing", "bullish", 16, 19, 3),
    exp("swing", "bearish", 22, 25, 25),
    # gap between high of bar 18 (10) and low of bar 20 (14); bar 20 closes -> known (21)
    exp("fvg", "bullish", 19, 21, 10, 14),
    # candle with the lowest low (bar 16) before the close above swing high 11 on bar 20
    exp("order_block", "bullish", 16, 21, 3, 9),
    # close above swing high 11 (16) on bar 20, but the library labels it only once the next
    # swing high (bar 22) is confirmed at the close of bar 24 (known at 25)
    exp("bos", "bullish", 20, 25, 16),
    exp("session_level", "bearish", 22, 28, 25),   # Asia high, known at the 07:00 window end
    exp("session_level", "bullish", 5, 28, 2),     # Asia low
]

# --- liquidity: equal swing highs (bars 8 and 18) swept by bar 22 -------------------------
LIQ_CLOSES = [10, 11, 12, 13, 14, 15, 16, 17, 18, 17, 16, 15, 14, 13, 14, 15, 16, 17, 18, 17,
              16, 15, 17, 16]
LIQ = chain(D0, "M15", M15, 9, LIQ_CLOSES, {8: {"up": 7}, 13: {"dn": 4}, 18: {"up": 7}})
LIQ[22] = candle(D0 + 22 * M15, "M15", 15, 26, 14, 17)   # sweep bar: high 26 > 25 + tolerance
EXPECTED_LIQ = {"event": t(22), "known": t(23), "level": px(25)}

# --- candle patterns: 16 quiet bars, an engulfing near a level, one far away from it ---------
QUIET = [(10, 11, 9, 10)] * 16
CANDLE_RAW = QUIET + [(11, 12, 8, 9), (8, 14, 7, 13), (13, 14, 12, 13), (13, 14, 12, 13),
                      (22, 23, 19, 20), (19, 25, 18, 24)]
CANDLES = [candle(D0 + i * M15, "M15", *b) for i, b in enumerate(CANDLE_RAW)]
CANDLE_LEVEL_PIPS = 6          # a causal level just under the first engulfing's low (7)
EXPECTED_CANDLE = [{"pattern": "engulfing", "direction": "bullish", "bar": 17}]

# --- DST week: Thu 22, Fri 23 (both UK BST) and Mon 26 Oct (UK back on GMT), H1, 24 bars/day ---
H1 = timedelta(hours=1)


def day_bars(day: datetime, spikes: dict[int, float]) -> list[dict]:
    out = []
    for h in range(24):
        mid = 10 + 0.1 * h
        top = spikes.get(h, mid + 1)
        out.append(candle(day + h * H1, "H1", mid, top, mid - 1, mid + 0.05))
    return out


# a 30-pip spike at 06:00 UTC: inside London on Fri (06-11 UTC, BST) but not on Mon (07-12, GMT)
SPIKES = {6: 30, 3: 20}
DST_H1 = (day_bars(datetime(2026, 10, 22, tzinfo=UTC), {6: 12})
          + day_bars(datetime(2026, 10, 23, tzinfo=UTC), SPIKES)
          + day_bars(datetime(2026, 10, 26, tzinfo=UTC), SPIKES))


def dump(name: str, obj) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1) + "\n")


if __name__ == "__main__":
    dump("labelled_day.json", DAY)
    dump("labelled_day_tail.json", TAIL)
    dump("labelled_day_expected.json", EXPECTED_DAY)
    dump("liquidity_day.json", {"candles": LIQ, "expected": EXPECTED_LIQ})
    dump("candle_day.json", {"candles": CANDLES, "level_price": px(CANDLE_LEVEL_PIPS),
                             "expected": EXPECTED_CANDLE})
    dump("dst_h1.json", DST_H1)
    print("wrote", sorted(p.name for p in OUT.iterdir()))
