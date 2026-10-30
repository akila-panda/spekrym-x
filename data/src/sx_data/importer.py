"""Import owner-supplied candle files (CSV or Parquet) with provenance (Phase 8A, decision L14).

This is the only real-data path for the Lab until a provider is verified. Nothing here claims
the file is correct: it checks structure and quality, hashes the bytes, and writes a provenance
sidecar that carries an honest label. The label is ``OWNER-SUPPLIED DATA - PROVIDER NOT
VERIFIED`` unless the caller states otherwise; it never says LIVE.

Required columns: time, open, high, low, close (names matched through ``import_formats``).
Optional: volume. Other columns (bid/ask closes, a ``complete`` flag) are NOT read: every bar is
assumed closed and bid/ask are left empty. A naive ``time`` column is REFUSED unless the
caller passes ``assume_tz`` (no silent timezone guess). Several files can be merged: identical
overlapping rows are dropped, conflicting ones refuse the import. Missing ``complete`` means
every bar is assumed closed; that assumption is written into the provenance.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from sx_core.clock import TF_SECONDS
from sx_core.contracts import Candle
from sx_core.storage import candles_to_frame, data_version, frame_to_candles, write_parquet
from sx_data.import_formats import (FormatRefused, flat_stats, normalise_columns,
                                    parse_times)
from sx_data.quality import DEFAULT_RULES, GapRules, QualityReport, check_quality

LABEL_UNVERIFIED = "OWNER-SUPPLIED DATA - PROVIDER NOT VERIFIED"
REQUIRED = ("time", "open", "high", "low", "close")


class ImportRefused(ValueError):
    """The file cannot be imported as is."""


@dataclass(frozen=True)
class ImportResult:
    candles: list[Candle]
    report: QualityReport
    provenance: dict


def sidecar_path(path: str | Path) -> Path:
    p = Path(path)
    return p.with_name(p.name + ".provenance.json")


def _read(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix in (".csv", ".txt"):
        return pd.read_csv(path)
    raise ImportRefused(f"unsupported file type {path.suffix!r} (use .csv or .parquet)")


def _localise(t: pd.Series, assume_tz: str | None) -> pd.Series:
    if t.dt.tz is None:
        if assume_tz is None:
            raise ImportRefused("time column has no timezone; pass assume_tz explicitly "
                                "(for example 'UTC'). No silent guess is made")
        t = t.dt.tz_localize(assume_tz)
    return t.dt.tz_convert("UTC").astype("datetime64[ns, UTC]")


def _load_one(p: Path, assume_tz: str | None, time_format: str | None,
              ) -> tuple[pd.DataFrame, str, bool]:
    try:
        raw = normalise_columns(_read(p))
        times, used = parse_times(raw["time"], time_format)
    except FormatRefused as e:
        raise ImportRefused(f"{p.name}: {e}") from e
    df = pd.DataFrame({"time": _localise(times, assume_tz)})
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(raw[c], errors="raise").astype("float64")
    df["volume"] = pd.to_numeric(raw["volume"], errors="raise").astype("float64") \
        if "volume" in raw.columns else 0.0
    return df, used, "volume" in raw.columns


def _merge(frames: list[pd.DataFrame]) -> pd.DataFrame:
    df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    if len(frames) > 1:
        df = df.drop_duplicates()
        dup = df[df.duplicated("time", keep=False)]
        if len(dup):
            raise ImportRefused(f"{dup['time'].nunique()} timestamp(s) appear in more than one "
                                f"file with different values, first at {dup['time'].iloc[0]}")
    return df


def import_candles(path: str | Path | Sequence[str | Path], *, instrument: str, tf: str,
                   source: str, assume_tz: str | None = None, label: str = LABEL_UNVERIFIED,
                   rules: GapRules = DEFAULT_RULES, accept_degraded: bool = False,
                   time_format: str | None = None) -> ImportResult:
    paths = [Path(x) for x in ([path] if isinstance(path, str | Path) else path)]
    if not paths:
        raise ImportRefused("no input files")
    if tf not in TF_SECONDS:
        raise ImportRefused(f"unknown timeframe {tf!r}")
    loaded = [_load_one(p, assume_tz, time_format) for p in paths]
    df = _merge([x[0] for x in loaded])
    df["bid_close"] = float("nan")
    df["ask_close"] = float("nan")
    df["complete"] = True
    assumed_complete = True
    df["instrument"], df["tf"] = instrument, tf
    if df.isna().drop(columns=["bid_close", "ask_close"]).any().any():
        raise ImportRefused("NaN in time or price columns")
    df = df.sort_values("time", kind="stable").reset_index(drop=True)
    report = check_quality(candles_to_frame(frame_to_candles_safe(df)), tf, rules=rules)
    if report.feed_degraded and not accept_degraded:
        raise ImportRefused("quality check failed: " + "; ".join(report.reasons))
    candles = frame_to_candles_safe(df)
    files = [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
              "time_format": x[1]} for p, x in zip(paths, loaded, strict=True)]
    combined = files[0]["sha256"] if len(files) == 1 else hashlib.sha256(
        "".join(f["sha256"] for f in files).encode()).hexdigest()
    prov = build_provenance(candles, report, source=source, label=label, instrument=instrument,
                            tf=tf, assumed_complete=assumed_complete, assume_tz=assume_tz)
    prov.update(file=files[0]["name"] if len(files) == 1 else f"{len(files)} files",
                file_sha256=combined, files=files)
    return ImportResult(candles, report, prov)


def build_provenance(candles: list[Candle], report: QualityReport, *, source: str, label: str,
                     instrument: str, tf: str, assumed_complete: bool,
                     assume_tz: str | None) -> dict:
    """Provenance fields shared by file imports and broker downloads (no file hashes here)."""
    frame = candles_to_frame(candles)
    years = pd.Series([c.time.year for c in candles]).value_counts().sort_index()
    return {
        "source": source, "label": label, "instrument": instrument, "tf": tf,
        "data_version": data_version(frame), "n_bars": len(candles),
        "bars_per_year": {int(k): int(v) for k, v in years.items()},
        "first_bar": candles[0].time.isoformat(), "last_bar": candles[-1].time.isoformat(),
        "assumed_complete": assumed_complete, "assume_tz": assume_tz,
        "expected_gaps": len(report.expected_gaps),
        "unexpected_gaps": len(report.unexpected_gaps),
        "feed_degraded": report.feed_degraded, "quality_reasons": list(report.reasons),
        **flat_stats(frame), "verified": False,
    }


def finalize_dataset(out: str | Path, candles: list[Candle], prov: dict) -> dict:
    """Write the Parquet file and its provenance sidecar; return the final provenance."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_parquet(candles_to_frame(candles), out)
    final = {**prov, "source_file": prov.get("file"), "source_file_sha256": prov.get("file_sha256"),
             "file": out.name, "file_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
    write_provenance(out, final)
    return final


def frame_to_candles_safe(df: pd.DataFrame) -> list[Candle]:
    try:
        return frame_to_candles(df)
    except ValueError as e:  # pydantic ValidationError is a ValueError
        raise ImportRefused(f"invalid candle row: {str(e)[:200]}") from e


def write_provenance(path: str | Path, prov: dict) -> Path:
    out = sidecar_path(path)
    out.write_text(json.dumps(prov, indent=1, sort_keys=True) + "\n")
    return out


def read_provenance(path: str | Path) -> dict:
    sp = sidecar_path(path)
    if not sp.exists():
        raise ImportRefused(f"no provenance sidecar at {sp}; import the file first")
    prov = json.loads(sp.read_text())
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != prov["file_sha256"]:
        raise ImportRefused("file changed since its provenance was written")
    return prov
