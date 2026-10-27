"""Parquet cache for closed candles, one file per instrument and timeframe.

Layout: ``<root>/<INSTRUMENT>/<TF>.parquet`` plus ``<TF>.json`` (data_version, bar count, first
and last bar). The default root is ``data/src/sx_data/cache/`` (gitignored). ``store`` merges
into what is already cached (new bars replace old bars with the same time) and returns the
content-based ``data_version`` of the merged frame.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from sx_core.contracts._base import format_utc
from sx_core.storage import CANDLE_COLUMNS, data_version, read_parquet, write_parquet
from sx_data.errors import DataError

DEFAULT_ROOT = Path(__file__).parent / "cache"
_INSTRUMENT = re.compile(r"^[A-Z]{3}_[A-Z]{3}$")


class CandleCache:
    def __init__(self, root: str | Path = DEFAULT_ROOT) -> None:
        self.root = Path(root)

    def path(self, instrument: str, tf: str) -> Path:
        if not _INSTRUMENT.match(instrument):
            raise DataError(f"bad instrument name {instrument!r}")
        if not re.fullmatch(r"[A-Z0-9]{1,3}", tf):
            raise DataError(f"bad timeframe {tf!r}")
        return self.root / instrument / f"{tf}.parquet"

    def load(self, instrument: str, tf: str) -> pd.DataFrame | None:
        p = self.path(instrument, tf)
        return read_parquet(p) if p.is_file() else None

    def version(self, instrument: str, tf: str) -> str | None:
        df = self.load(instrument, tf)
        return None if df is None else data_version(df)

    def store(self, df: pd.DataFrame) -> str:
        """Merge ``df`` into the cache and return the merged ``data_version``."""
        if df.empty:
            raise DataError("refusing to store an empty frame")
        if df["instrument"].nunique() != 1 or df["tf"].nunique() != 1:
            raise DataError("one instrument and timeframe per store call")
        if not df["complete"].all():
            raise DataError("only complete (closed) bars may be cached")
        instrument, tf = str(df["instrument"].iloc[0]), str(df["tf"].iloc[0])
        old = self.load(instrument, tf)
        merged = df if old is None else pd.concat([old, df], ignore_index=True)
        merged = (merged.drop_duplicates("time", keep="last").sort_values("time")
                  .reset_index(drop=True))[CANDLE_COLUMNS]
        version = write_parquet(merged, self.path(instrument, tf))
        manifest = {
            "data_version": version, "n_bars": len(merged),
            "first": format_utc(merged["time"].iloc[0].to_pydatetime()),
            "last": format_utc(merged["time"].iloc[-1].to_pydatetime()),
        }
        self.path(instrument, tf).with_suffix(".json").write_text(
            json.dumps(manifest, indent=2) + "\n")
        return version
