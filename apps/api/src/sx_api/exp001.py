"""Read-only view of the EXP-001 result files (written by sx-lab exp001-validate / exp001-holdout).

Nothing here computes a result. It passes the stage JSON through a whitelist (so paths and host
details in `environment` never reach the browser) and refuses to mix stages from different specs.
"""

from __future__ import annotations

import json
from pathlib import Path

KEEP = ("experiment", "stage", "labels", "spec_hash", "data_version", "data_label", "n_validation",
        "n_holdout", "scores", "mcs", "outcome", "conformal", "variants_tried",
        "per_seed_qlike_diagnostic", "train_loss_by_epoch", "train_config", "reason")


def _read(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        raise ValueError(f"{path.name} is not valid JSON: {e}") from e
    return {k: raw[k] for k in KEEP if k in raw}


def _report(folder: Path) -> Path:
    return folder.parent.parent / "experiments" / "EXP-001_mamba_vs_har.md"


def load_exp001(folder: Path) -> dict:
    val, hold = _read(folder / "validation_results.json"), _read(folder / "holdout_results.json")
    if hold and not val:
        raise ValueError("holdout_results.json exists without validation_results.json")
    if val and hold and val.get("spec_hash") != hold.get("spec_hash"):
        raise ValueError("validation and holdout results come from different spec hashes")
    status = "complete" if hold else "validated" if val else "not_run"
    return {"status": status, "validation": val, "holdout": hold,
            "report_present": _report(folder).exists()}
