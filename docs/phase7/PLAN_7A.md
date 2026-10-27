
---

## Phase 7 split and Lab known issues (added 2026-10-27)

**Phase 7A: BUILT 2026-10-27** (partition, features, metrics, naive baselines; see `docs/PROGRESS.md`). **Phase 7B: not started** (HAR, GARCH via `arch`, negative controls, purged-CV cross-check, Optuna search logged to the ledger, `sx-lab` CLI, `Forecast` JSON outputs). 7B must first install `arch` and `optuna` in a sandbox, read the source, pin versions and record them in `docs/DEPENDENCIES.md`.

Lab known issues:
- L-1 All Lab numbers use a SYNTHETIC fixture. Nothing is known about real EUR/USD; "baselines run on real data" is still open (OANDA never run, issues 18 and 24).
- L-2 Features assume continuous bars. Real H1 data has weekend gaps, so "h bars" would not mean h hours across a weekend and the first Monday returns span the gap. A gap policy is needed before real data; not built.
- L-3 Holdout governance is a process rule kept in the ledger, not security. Two processes racing could both pass the check; single-process use is assumed. Appending new data changes the holdout rows, which is a new evaluation by design.
- L-4 Persistence divides nothing but can return zero in a flat window, and QLIKE then refuses to run (by design: no silent clipping).
- L-5 Feature definitions (ATR as mean true range over close, Parkinson range variance, windows 6/24/120) are my choices and untuned; ATR was not cross-checked against `apps/web/src/layers/atr.ts` or TA-Lib.
- L-6 Sandbox ran pandas 3.0.2 / numpy 2.4.4, repo pins 3.1.0 / 2.5.4.
- L-7 Root `pyproject.toml` `testpaths` does not list `lab/tests`; run `pytest lab/tests` or add it (command in the delivery message).
