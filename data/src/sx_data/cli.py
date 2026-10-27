"""``python -m sx_data.cli sync --instrument EUR_USD --days 5``: practice feed to cache.

Reads ``OANDA_TOKEN`` from the environment or ``.env``. Refuses to run unless paper mode.
Prints data versions and the quality report for each timeframe. Never prints the token.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sx_core.config import load_settings
from sx_data.cache import DEFAULT_ROOT, CandleCache
from sx_data.oanda_rest import OandaClient
from sx_data.pipeline import HIGHER, rebuild_higher, sync_m1
from sx_data.quality import check_quality


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sx_data.cli")
    ap.add_argument("command", choices=["sync"])
    ap.add_argument("--instrument", default="EUR_USD")
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--dotenv", default=str(Path.cwd() / ".env"))
    ap.add_argument("--cache", default=str(DEFAULT_ROOT))
    args = ap.parse_args(argv)

    settings = load_settings(dotenv_path=args.dotenv)
    now = datetime.now(UTC)
    cache = CandleCache(args.cache)
    with OandaClient(settings.oanda_token) as client:
        v = sync_m1(client, cache, args.instrument, now - timedelta(days=args.days), now)
    print(f"M1 data_version: {v}")
    for tf, ver in rebuild_higher(cache, args.instrument).items():
        _print_quality(cache, args.instrument, tf, ver, now)
    _print_quality(cache, args.instrument, "M1", v or "-", now)
    print(f"timeframes built: {', '.join(HIGHER)}. Feed: OANDA practice. Data is not validated.")
    return 0


def _print_quality(cache: CandleCache, instrument: str, tf: str, version: str,
                   now: datetime) -> None:
    frame = cache.load(instrument, tf)
    if frame is None:
        print(f"{tf}: no data")
        return
    r = check_quality(frame, tf, now=now)
    print(f"{tf}: {version} bars={r.n_bars} degraded={r.feed_degraded} {'; '.join(r.reasons)}")


if __name__ == "__main__":
    raise SystemExit(main())
