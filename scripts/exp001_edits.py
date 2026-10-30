"""Apply the two agreed pre-lock edits to EXP-001.yaml (idempotent)."""
import re
import sys
from pathlib import Path

p = Path(sys.argv[1] if len(sys.argv) > 1 else "lab/experiments/prereg/EXP-001.yaml")
t = p.read_text()
if "inconclusive:" not in t:
    t, n = re.subn(r"^(  loss:[^\n]*\n)",
                   r"\1  inconclusive: Anything not covered above (for example only a "
                   r"reference model is in the model confidence set).\n",
                   t, count=1, flags=re.M)
    if n != 1:
        raise SystemExit("could not find the 'loss:' line")
if "seeds 1, 2, 3" not in t:
    t, n = re.subn(r"\(seeds\s+listed in the ledger\)", "(seeds 1, 2, 3)", t, count=1)
    if n != 1:
        raise SystemExit("could not find '(seeds listed in the ledger)'")
p.write_text(t)
print("edits applied")
