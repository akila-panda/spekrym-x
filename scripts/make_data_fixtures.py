"""Regenerate the frozen Phase 3 data fixtures. SYNTHETIC data, seeded, not real market data.

    python scripts/make_data_fixtures.py

Writes ``tests/fixtures/oanda/eurusd_m1_oanda_shape.json`` (OANDA-shaped M1 response) and
``tests/fixtures/eurusd_h1_week.json`` (Candle-shaped H1 with a weekend gap). The fixtures are
committed and hash-pinned by tests, so run this only to change them deliberately.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

FIX = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
HALF_SPREAD = 0.00004


def _p(x: float) -> str:
    return f"{x:.5f}"


Bar = tuple[float, float, float, float]


def _blk(bar: Bar, d: float) -> dict:
    o, h, lo, c = bar
    return {"o": _p(o + d), "h": _p(h + d), "l": _p(lo + d), "c": _p(c + d)}


def _walk(rng: random.Random, start: float, n: int, step: float) -> list[Bar]:
    out, px = [], start
    for _ in range(n):
        o = px
        c = round(o + (rng.random() - 0.5) * step, 5)
        h = round(max(o, c) + rng.random() * step * 0.4, 5)
        lo = round(min(o, c) - rng.random() * step * 0.4, 5)
        out.append((round(o, 5), h, lo, c))
        px = c
    return out


def make_m1() -> dict:
    rng = random.Random(42)
    t0 = datetime(2026, 10, 19, 6, 0, tzinfo=UTC)
    quiet = {17, 18, 95, 96, 140}  # minute offsets with no trades: no bar exists
    bars = _walk(rng, 1.0850, 181, 0.00012)
    candles = []
    for i, (o, h, lo, c) in enumerate(bars):
        if i in quiet:
            continue
        t = (t0 + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S.000000000Z")

        candles.append({"complete": i != 180, "volume": 20 + int(rng.random() * 60), "time": t,
                        "bid": _blk((o, h, lo, c), -HALF_SPREAD),
                        "ask": _blk((o, h, lo, c), HALF_SPREAD),
                        "mid": _blk((o, h, lo, c), 0.0)})
    return {"instrument": "EUR_USD", "granularity": "M1", "candles": candles}


def make_h1() -> list[dict]:
    rng = random.Random(7)
    spans = [(datetime(2026, 10, 22, 0, tzinfo=UTC), 45),   # Thu 00:00 .. Fri 20:00
             (datetime(2026, 10, 25, 22, tzinfo=UTC), 8)]   # Sun 22:00 .. Mon 05:00
    out, px = [], 1.0850
    for start, n in spans:
        for i, (o, h, lo, c) in enumerate(_walk(rng, px, n, 0.0009)):
            t = start + timedelta(hours=i)
            out.append({"instrument": "EUR_USD", "tf": "H1",
                        "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "open": o, "high": h, "low": lo, "close": c,
                        "volume": float(800 + int(rng.random() * 900)),
                        "bid_close": round(c - HALF_SPREAD, 5),
                        "ask_close": round(c + HALF_SPREAD, 5), "complete": True})
            px = c
    return out


if __name__ == "__main__":
    (FIX / "oanda").mkdir(parents=True, exist_ok=True)
    m1_path = FIX / "oanda" / "eurusd_m1_oanda_shape.json"
    m1_path.write_text(json.dumps(make_m1(), indent=1) + "\n")
    (FIX / "eurusd_h1_week.json").write_text(json.dumps(make_h1(), indent=1) + "\n")
    print("fixtures written")
