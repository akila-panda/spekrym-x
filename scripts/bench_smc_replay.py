"""Time the SMC replay at increasing history lengths, fast engine vs the library reference.

Usage: python scripts/bench_smc_replay.py [max_library_bars]   (default 192)
Uses a seeded random series (no network, no real data). Also checks both engines agree.
"""

from __future__ import annotations

import random
import sys
import time
from datetime import UTC, datetime, timedelta

from sx_assistant.ta.smc_adapter import smc_setups
from sx_core.contracts import Candle


def series(n: int, seed: int = 7, tick: float = 0.00005) -> list[Candle]:
    rng, px, out = random.Random(seed), 1.1, []
    t0 = datetime(2026, 10, 19, tzinfo=UTC)
    for i in range(n):
        o = round(px / tick) * tick
        c = round((o + rng.gauss(0, 3 * tick)) / tick) * tick
        hi, lo = max(o, c) + rng.choice([0, tick, 2 * tick]), min(o, c) - rng.choice([0, tick])
        px = c
        out.append(Candle(instrument="EUR_USD", tf="M15", time=t0 + timedelta(minutes=15 * i),
                          open=o, high=hi, low=lo, close=c, volume=float(rng.randint(1, 9)),
                          bid_close=c, ask_close=c, complete=True))
    return out


def timed(cs: list[Candle], engine: str):
    t = time.perf_counter()
    res = smc_setups(cs, swing_length=3, engine=engine)
    return res, time.perf_counter() - t


def main() -> None:
    max_lib = int(sys.argv[1]) if len(sys.argv) > 1 else 192
    print(f"{'bars':>6} {'fast s':>8} {'library s':>10} {'speedup':>8} {'setups':>7} same")
    for n in (48, 96, 192, 384, 768):
        cs = series(n)
        fast, tf = timed(cs, "fast")
        if n <= max_lib:
            ref, tl = timed(cs, "library")
            print(f"{n:>6} {tf:>8.2f} {tl:>10.2f} {tl / tf:>7.1f}x {len(fast):>7} {fast == ref}")
        else:
            print(f"{n:>6} {tf:>8.2f} {'-':>10} {'-':>8} {len(fast):>7} (library skipped)")


if __name__ == "__main__":
    main()
