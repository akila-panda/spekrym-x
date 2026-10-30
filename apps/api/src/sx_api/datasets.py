"""Dataset import for the Lab dashboard: request rules, file naming, listing (no network here).

The browser never sees the OANDA token and never chooses a path: the file name is built from
validated fields only, inside one data folder. Everything downloaded is labelled as the broker's
practice feed, NOT independently verified (the provenance label from ``sx_data.history``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator

from sx_data.importer import ImportRefused, read_provenance, sidecar_path

INSTRUMENTS = ("EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD", "USD_CHF", "NZD_USD")
TIMEFRAMES = ("M5", "M15", "M30", "H1")        # M1 is too large; H4 and D come from resample
_MINUTES = {"M5": 5, "M15": 15, "M30": 30, "H1": 60}
MAX_BARS = 250_000
EARLIEST = date(2005, 1, 1)
LIST_KEYS = ("instrument", "tf", "n_bars", "first_bar", "last_bar", "label", "data_version",
             "feed_degraded", "expected_gaps", "unexpected_gaps", "flat_bars", "source", "verified")


def estimate_bars(start: date, end: date, tf: str) -> int:
    """Rough bar count: calendar days times bars per day times 5/7 (weekends closed)."""
    return int((end - start).days * (1440 // _MINUTES[tf]) * 5 / 7)


class ImportRequest(BaseModel):
    instrument: str
    tf: str
    start: date
    end: date           # last day EXCLUDED, like the CLI

    @field_validator("instrument")
    @classmethod
    def _instrument(cls, v: str) -> str:
        if v not in INSTRUMENTS:
            raise ValueError(f"instrument must be one of {', '.join(INSTRUMENTS)}")
        return v

    @field_validator("tf")
    @classmethod
    def _tf(cls, v: str) -> str:
        if v not in TIMEFRAMES:
            raise ValueError(f"timeframe must be one of {', '.join(TIMEFRAMES)}")
        return v

    @model_validator(mode="after")
    def _range(self) -> ImportRequest:
        if self.start < EARLIEST:
            raise ValueError(f"start must be {EARLIEST} or later")
        if self.end <= self.start:
            raise ValueError("end must be after start")
        if self.end > datetime.now(UTC).date() + timedelta(days=1):
            raise ValueError("end cannot be in the future")
        if estimate_bars(self.start, self.end, self.tf) > MAX_BARS:
            raise ValueError(f"range too large (about {MAX_BARS} bars at most); shorten it")
        return self

    @property
    def filename(self) -> str:
        return (f"{self.instrument.lower()}_{self.tf.lower()}_"
                f"{self.start:%Y%m%d}_{self.end:%Y%m%d}.parquet")

    def bounds(self) -> tuple[datetime, datetime]:
        mid = datetime.min.time()
        return (datetime.combine(self.start, mid, tzinfo=UTC),
                datetime.combine(self.end, mid, tzinfo=UTC))


def summarize(prov: dict) -> dict:
    return {k: prov.get(k) for k in LIST_KEYS}


def list_datasets(folder: Path) -> list[dict]:
    """Every Parquet file in ``folder`` with its provenance and an integrity verdict."""
    out: list[dict] = []
    for p in sorted(folder.glob("*.parquet")) if folder.is_dir() else []:
        row: dict = {"file": p.name, "size_bytes": p.stat().st_size}
        try:
            row.update(summarize(read_provenance(p)), integrity="ok")
        except ImportRefused as e:
            missing = not sidecar_path(p).exists()
            row.update(integrity="no_provenance" if missing else "modified", problem=str(e))
        except (ValueError, KeyError):
            row.update(integrity="unreadable", problem="provenance file is not valid")
        out.append(row)
    return out
