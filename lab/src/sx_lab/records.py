"""Turn a fitted Lab model into contract ``Forecast`` records (Phase 7B).

Units: ``point`` and the interval are per-bar volatility, i.e. sqrt of the mean squared log
return over the next ``horizon`` bars. The interval is NOT conformal (that is Phase 8): it is
the training-set quantile band of target/prediction ratios, widened if needed so the point lies
inside (the contract requires that). Its empirical coverage on the frame is measured and
reported in ``track_record``; do not read ``nominal_coverage`` as a guarantee.
Status is always ``exploratory``.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from sx_core.contracts import Forecast, forecast_id
from sx_core.contracts.forecast import BaselineComparison, Interval, ModelRef, TrackRecord
from sx_lab.baselines.base import Baseline
from sx_lab.evaluation.metrics import qlike

VERSION = "sx-lab-7b"


def params_hash(params: dict[str, object]) -> str:
    blob = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def make_forecasts(model: Baseline, baseline: Baseline, train: pd.DataFrame, val: pd.DataFrame,
                   *, instrument: str, tf: str, variants_tried: int, nominal: float = 0.8
                   ) -> list[Forecast]:
    """``model`` and ``baseline`` must already be fitted on ``train`` only."""
    ratio = train["target"].to_numpy() / model.predict(train).to_numpy()
    q_lo, q_hi = np.quantile(ratio, [(1 - nominal) / 2, 1 - (1 - nominal) / 2])
    pred = model.predict(val).to_numpy()
    lo, hi = np.minimum(pred * q_lo, pred), np.maximum(pred * q_hi, pred)
    y = val["target"].to_numpy()
    coverage = float(np.mean((y >= lo) & (y <= hi)))
    delta = qlike(pred, y) - qlike(baseline.predict(val), val["target"])
    ph = params_hash(model.params())  # type: ignore[attr-defined]
    ref = ModelRef(name=model.name, version=VERSION, params_hash=ph)
    out = []
    for i, (_t, row) in enumerate(val.iterrows()):
        issued = pd.Timestamp(row["known_at"]).to_pydatetime()
        out.append(Forecast(
            id=forecast_id(instrument, tf, issued, "realized_vol", model.name, ph),
            instrument=instrument, tf=tf, issued_at=issued,  # type: ignore[arg-type]
            horizon_end=pd.Timestamp(row["target_known_at"]).to_pydatetime(),
            target="realized_vol", point=float(np.sqrt(pred[i])),
            interval=Interval(low=float(np.sqrt(lo[i])), high=float(np.sqrt(hi[i])),
                              nominal_coverage=nominal),
            model=ref,
            baseline_comparison=BaselineComparison(baseline=baseline.name, metric="qlike",
                                                   delta=float(delta)),
            track_record=TrackRecord(n=len(val), empirical_coverage=coverage,
                                     variants_tried=variants_tried),
            status="exploratory"))
    return out
