"""Frozen fixtures for the Phase 9A tests: synthetic H1 candles and synthetic setups.

Seeded random walk (no edge by construction). Setups are placed on bar closes, so the scorer
tests can check protocol and plumbing, NOT real-market skill.
Run: python scripts/make_model_fixtures.py
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

OUT = Path("tests/fixtures/model")
N, T0 = 1800, datetime(2025, 1, 6, tzinfo=UTC)
KINDS = ["swing", "bos", "choch", "fvg", "order_block", "liquidity_sweep"]


def main() -> None:
    rng = np.random.default_rng(7)
    close = 1.10 + np.cumsum(rng.normal(0, 0.0006, N))
    opn = np.concatenate([[1.10], close[:-1]])
    high = np.maximum(opn, close) + np.abs(rng.normal(0, 0.0003, N))
    low = np.minimum(opn, close) - np.abs(rng.normal(0, 0.0003, N))
    candles = [{"instrument": "EUR_USD", "tf": "H1", "time": (T0 + timedelta(hours=i)).isoformat(),
                "open": round(float(opn[i]), 5), "high": round(float(high[i]), 5),
                "low": round(float(low[i]), 5), "close": round(float(close[i]), 5),
                "volume": 100.0, "bid_close": None, "ask_close": None, "complete": True}
               for i in range(N)]
    setups = []
    for i in range(60, N - 1, 5):
        k, d = KINDS[(i // 5) % 6], ["bullish", "bearish"][(i // 5) % 2]
        t_ev = T0 + timedelta(hours=i)
        mid = float(close[i - 1])
        setups.append({
            "id": f"fx{i:05d}", "kind": k, "instrument": "EUR_USD", "tf": "H1", "direction": d,
            "geometry": {"price_low": round(mid - 0.0004, 5), "price_high": round(mid + 0.0004, 5),
                         "t_start": (t_ev - timedelta(hours=3)).isoformat()},
            "event_time": t_ev.isoformat(), "known_at": (t_ev + timedelta(hours=1)).isoformat(),
            "lifecycle": "fresh", "source": {"library": "fixture", "version": "1", "adapter": "x"},
            "plain_text": "synthetic", "invalidation": "synthetic", "status": "causal"})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "candles_h1_1800.json").write_text(json.dumps(candles))
    (OUT / "setups_synthetic.json").write_text(json.dumps(setups))
    print(len(candles), "candles,", len(setups), "setups")


if __name__ == "__main__":
    main()
