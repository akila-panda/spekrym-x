"""Regenerate the frozen Phase 7 Lab fixture. SYNTHETIC data, seeded, not real market data.

    python scripts/make_lab_fixtures.py

Writes ``tests/fixtures/lab/eurusd_h1_synth_1000.json``: 1000 continuous H1 candles (no weekend
gaps) from a GARCH(1,1) process with an intraday volatility pattern. It is committed and
hash-pinned by a test, so run this only to change it deliberately.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "lab"
N = 1000
BASE_VAR = 8e-7  # per-hour return variance, roughly 7% annual
A, B = 0.08, 0.90


def _seasonal(hour: int) -> float:
    return 0.6 + 0.8 * math.exp(-((hour - 12) ** 2) / 30.0)


def main() -> None:
    rng = np.random.default_rng(7)
    start = datetime(2026, 1, 5, tzinfo=UTC)
    sig2, price, rows = BASE_VAR, 1.1, []
    for i in range(N):
        t = start + timedelta(hours=i)
        s = _seasonal(t.hour)
        r = s * math.sqrt(sig2) * float(rng.standard_normal())
        o, c = price, price * math.exp(r)
        wick = s * math.sqrt(sig2) * o
        hi = max(o, c) + abs(float(rng.standard_normal())) * 0.4 * wick
        lo = min(o, c) - abs(float(rng.standard_normal())) * 0.4 * wick
        o, c, hi, lo = (round(x, 5) for x in (o, c, hi, lo))
        hi, lo = max(hi, o, c), min(lo, o, c)
        rows.append({"instrument": "EUR_USD", "tf": "H1",
                     "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "open": o, "high": hi,
                     "low": lo, "close": c, "volume": float(1000 + int(rng.integers(0, 900))),
                     "complete": True})
        price = c
        sig2 = BASE_VAR * (1 - A - B) + A * (r / s) ** 2 + B * sig2
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "eurusd_h1_synth_1000.json"
    lines = ",\n".join(json.dumps(r, separators=(",", ":")) for r in rows)
    path.write_text("[\n" + lines + "\n]\n")
    print(f"wrote {path} ({N} bars)")


if __name__ == "__main__":
    main()
