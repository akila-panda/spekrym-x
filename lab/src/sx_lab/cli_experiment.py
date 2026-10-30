"""Experiment commands for ``sx-lab``: import, spec-hash, lock, open-holdout (Phase 8A).

These never train anything. ``lock`` and ``open-holdout`` refuse unless the spec is complete
and approved, the data file has a matching provenance sidecar, the data label is not
sample/synthetic (L11), and the spec's data fields match the file. ``open-holdout`` spends the
holdout: it needs ``--confirm-spend-holdout`` and a reason, and works once (partition.py).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sx_core.ledger import Ledger
from sx_core.storage import data_version, frame_to_candles, read_parquet, candles_to_frame
from sx_data.importer import (ImportRefused, finalize_dataset, import_candles, read_provenance,
                              sidecar_path)
from sx_lab.features.gaps import make_gap_aware_dataset
from sx_lab.partition import LabPartition
from sx_lab.spec import load_spec, refuse_blocked_label


def cmd_import(a: argparse.Namespace) -> int:
    if not a.source_file:
        raise SystemExit("import needs --source-file FILE [FILE ...]")
    try:
        res = import_candles(a.source_file, instrument=a.instrument, tf=a.tf, source=a.source,
                             assume_tz=a.assume_tz, accept_degraded=a.accept_degraded,
                             time_format=a.time_format)
    except ImportRefused as e:
        print(f"REFUSED: {e}")
        return 2
    out = Path(a.out_file)
    prov = finalize_dataset(out, res.candles, res.provenance)
    print(f"imported {prov['n_bars']} bars {prov['first_bar']} .. {prov['last_bar']}")
    print(f"bars per year: {prov['bars_per_year']}")
    print(f"data_version {prov['data_version']} | label: {prov['label']} | verified: False")
    if prov["longest_flat_run"] >= 3:
        print(f"WARNING: {prov['flat_bars']} flat bars (high == low), longest run "
              f"{prov['longest_flat_run']}: filler bars distort variance; look before locking")
    print(f"quality: degraded={prov['feed_degraded']} expected_gaps={prov['expected_gaps']} "
          f"unexpected_gaps={prov['unexpected_gaps']} {prov['quality_reasons']}")
    print(f"wrote {out} and {sidecar_path(out)}")
    return 0


def cmd_spec_hash(a: argparse.Namespace) -> int:
    spec, h = load_spec(a.spec)
    print(f"{spec.id} status={spec.status} sha256={h}")
    why = spec.lockable()
    print("lockable" if not why else "NOT lockable: " + "; ".join(why))
    return 0


def _verified(a: argparse.Namespace):
    spec, h = load_spec(a.spec)
    why = spec.lockable()
    if why:
        raise SystemExit("refused: spec not lockable: " + "; ".join(why))
    if not a.candles or not a.candles.endswith(".parquet"):
        raise SystemExit("refused: --candles must be a .parquet written by `sx-lab import`")
    prov = read_provenance(a.candles)
    refuse_blocked_label(prov["label"])
    frame = read_parquet(a.candles)
    candles = frame_to_candles(frame)
    dv = data_version(candles_to_frame(candles))
    d = spec.data
    if not (dv == prov["data_version"] == d.data_version):
        raise SystemExit("refused: data_version differs between file, provenance and spec")
    if (d.instrument, d.tf, d.first_bar, d.last_bar) != (
            candles[0].instrument, candles[0].tf, candles[0].time.isoformat(),
            candles[-1].time.isoformat()):
        raise SystemExit("refused: spec data window/instrument/timeframe does not match the file")
    p = spec.partition
    part = LabPartition(make_gap_aware_dataset(candles, spec.horizon_bars, spec.windows),
                        horizon=spec.horizon_bars, embargo=p.embargo_bars,
                        fractions=(p.train, p.validation, p.holdout))
    return spec, h, part, Ledger(a.ledger)


def cmd_lock(a: argparse.Namespace) -> int:
    spec, h, part, ledger = _verified(a)
    part.lock_evaluation(ledger, h)
    print(f"{spec.id} locked: spec {h[:16]} holdout {part.holdout_status(ledger)} | {part!r}")
    return 0


def cmd_open_holdout(a: argparse.Namespace) -> int:
    if not a.confirm_spend_holdout or not (a.reason or "").strip():
        raise SystemExit("refused: needs --reason and --confirm-spend-holdout (this is one-shot)")
    spec, h, part, ledger = _verified(a)
    frame = part.open_holdout(ledger, h, a.reason)
    out = Path(a.out) / f"{spec.id}_holdout_{part.holdout_id.removeprefix('dv:')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.reset_index().to_json(out, orient="records", date_format="iso", indent=1)
    print(f"HOLDOUT SPENT for {spec.id}: {len(frame)} rows written to {out}")
    print(json.dumps({"holdout": part.holdout_status(ledger)}))
    return 0
