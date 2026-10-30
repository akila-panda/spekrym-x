"""Fill EXP-001 data.* from an import provenance sidecar; optionally record YOUR approval.

Usage:
  python scripts/exp001_prepare.py --candles FILE.parquet            # fill data.* only
  python scripts/exp001_prepare.py --candles FILE.parquet --approve-as "Your Name"

Only the data fields, status and the approval block are touched; comments are kept. The
approval flag is a deliberate owner act: do not pass it until you have read the review.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


def set_line(text: str, key: str, value: str, indent: str) -> str:
    pat = re.compile(rf"^({re.escape(indent)}{re.escape(key)}:)[^\n]*", re.M)
    if len(pat.findall(text)) != 1:
        raise SystemExit(f"cannot find exactly one '{indent}{key}:' line in the spec")
    return pat.sub(lambda m: f"{m.group(1)} {value}", text, count=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candles", required=True)
    ap.add_argument("--spec", default="lab/experiments/prereg/EXP-001.yaml")
    ap.add_argument("--approve-as")
    a = ap.parse_args()
    prov = json.loads(Path(a.candles + ".provenance.json").read_text())
    for need in ("data_version", "first_bar", "last_bar", "instrument", "tf", "label"):
        if not prov.get(need):
            raise SystemExit(f"sidecar has no {need}")
    p = Path(a.spec)
    t = p.read_text()
    t = set_line(t, "instrument", prov["instrument"], "  ")
    t = set_line(t, "tf", prov["tf"], "  ")
    t = set_line(t, "data_version", f"\"{prov['data_version']}\"", "  ")
    t = set_line(t, "first_bar", f"\"{prov['first_bar']}\"", "  ")
    t = set_line(t, "last_bar", f"\"{prov['last_bar']}\"", "  ")
    if a.approve_as:
        t = set_line(t, "status", "approved", "")
        t = set_line(t, "approved_by", f"\"{a.approve_as}\"", "  ")
        t = set_line(t, "approved_on", f"\"{date.today().isoformat()}\"", "  ")
    p.write_text(t)
    print(f"data label: {prov['label']} | bars {prov['n_bars']} | "
          f"{prov['first_bar']} .. {prov['last_bar']}")
    print(f"gaps: expected {prov['expected_gaps']} unexpected {prov['unexpected_gaps']} "
          f"degraded {prov['feed_degraded']} | flat bars {prov.get('flat_bars')} "
          f"(longest run {prov.get('longest_flat_run')})")
    print("approval recorded" if a.approve_as else "data filled; NOT approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
