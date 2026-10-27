"""Regenerate the frozen Phase 5A sample fixture (SYNTHETIC, not market data).

    python scripts/make_premarket_fixtures.py

528 M15 EUR_USD bars: Monday 2026-10-19 to Friday 2026-10-23 (full days) plus Monday
2026-10-26 00:00 to 12:00 UTC. Seeded random walk (seed 42) with a calmer Asia and a busier
London. The output is committed and hash-pinned by ``assistant/tests/test_premarket_fixture.py``.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "premarket"
STEP = timedelta(minutes=15)


def _times() -> list[datetime]:
    out: list[datetime] = []
    for day in range(19, 24):
        start = datetime(2026, 10, day, tzinfo=UTC)
        out += [start + i * STEP for i in range(96)]
    start = datetime(2026, 10, 26, tzinfo=UTC)
    return out + [start + i * STEP for i in range(48)]


def build() -> list[dict]:
    rng, price, bars = random.Random(42), 1.0850, []
    for t in _times():
        vol = 0.00012 if t.hour < 7 else 0.00028 if t.hour < 16 else 0.0002
        o = price
        c = round(o + rng.gauss(0, vol), 5)
        hi = round(max(o, c) + abs(rng.gauss(0, vol / 2)), 5)
        lo = round(min(o, c) - abs(rng.gauss(0, vol / 2)), 5)
        bars.append({"instrument": "EUR_USD", "tf": "M15", "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "open": o, "high": hi, "low": lo, "close": c, "volume": 100.0,
                     "bid_close": round(c - 0.00002, 5), "ask_close": round(c + 0.00002, 5),
                     "complete": True})
        price = c
    return bars


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build(), indent=1) + "\n"
    (OUT / "eurusd_m15_sample.json").write_text(text)
    print("sha256", hashlib.sha256(text.encode()).hexdigest())
