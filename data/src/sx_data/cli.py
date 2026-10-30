"""``python -m sx_data.cli sync --instrument EUR_USD --days 5``: practice feed to cache.
``python -m sx_data.cli history --start 2021-01-01 --end 2026-10-27 --out FILE.parquet``:
long H1 history to a Lab dataset with a provenance sidecar (Phase 8A).

Reads ``OANDA_TOKEN`` from the environment or ``.env``. Refuses to run unless paper mode.
Prints data versions and the quality report for each timeframe. Never prints the token.
"""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sx_core.config import load_settings
from sx_data.cache import DEFAULT_ROOT, CandleCache
from sx_data.errors import OandaError
from sx_data.history import fetch_history
from sx_data.importer import ImportRefused, finalize_dataset, sidecar_path
from sx_data.oanda_rest import OandaClient
from sx_data.pipeline import HIGHER, rebuild_higher, sync_m1
from sx_data.quality import check_quality


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sx_data.cli")
    ap.add_argument("command", choices=["sync", "history"])
    ap.add_argument("--tf", default="H1")
    ap.add_argument("--start", help="history: first day, YYYY-MM-DD (UTC)")
    ap.add_argument("--end", help="history: last day EXCLUDED, YYYY-MM-DD (UTC)")
    ap.add_argument("--out", default="lab/outputs/data/oanda_h1.parquet")
    ap.add_argument("--accept-degraded", action="store_true")
    ap.add_argument("--instrument", default="EUR_USD")
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--dotenv", default=str(Path.cwd() / ".env"))
    ap.add_argument("--cache", default=str(DEFAULT_ROOT))
    args = ap.parse_args(argv)

    settings = load_settings(dotenv_path=args.dotenv)
    if args.command == "history":
        return _history(args, settings)
    now = datetime.now(UTC)
    cache = CandleCache(args.cache)
    with OandaClient(settings.oanda_token, env=_guard_env(settings)) as client:
        v = sync_m1(client, cache, args.instrument, now - timedelta(days=args.days), now)
    print(f"M1 data_version: {v}")
    for tf, ver in rebuild_higher(cache, args.instrument).items():
        _print_quality(cache, args.instrument, tf, ver, now)
    _print_quality(cache, args.instrument, "M1", v or "-", now)
    print(f"timeframes built: {', '.join(HIGHER)}. Feed: OANDA practice. Data is not validated.")
    return 0


def _guard_env(settings) -> dict[str, str]:
    """Values that came from .env must reach the client's own paper-mode guard."""
    return {"SX_TRADING_MODE": settings.trading_mode, "OANDA_ENV": settings.oanda_env}


def _day(text: str | None, name: str) -> datetime:
    if not text:
        raise SystemExit(f"history needs --{name} YYYY-MM-DD")
    return datetime.combine(date.fromisoformat(text), datetime.min.time(), tzinfo=UTC)


def _history(args: argparse.Namespace, settings) -> int:
    start, end = _day(args.start, "start"), _day(args.end, "end")
    if end <= start:
        raise SystemExit("--end must be after --start")
    try:
        with OandaClient(settings.oanda_token, env=_guard_env(settings)) as client:
            res = fetch_history(client, args.instrument, args.tf, start, end,
                                accept_degraded=args.accept_degraded)
        prov = finalize_dataset(args.out, res.candles, res.provenance)
    except (ImportRefused, OandaError) as e:
        print(f"REFUSED: {e}")
        return 2
    print(f"downloaded {prov['n_bars']} {args.tf} bars {prov['first_bar']} .. {prov['last_bar']}")
    print(f"bars per year: {prov['bars_per_year']}")
    print(f"data_version {prov['data_version']} | label: {prov['label']} | verified: False")
    print(f"quality: degraded={prov['feed_degraded']} expected_gaps={prov['expected_gaps']} "
          f"unexpected_gaps={prov['unexpected_gaps']} flat_bars={prov['flat_bars']} "
          f"{prov['quality_reasons']}")
    print(f"wrote {args.out} and {sidecar_path(args.out)}")
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
