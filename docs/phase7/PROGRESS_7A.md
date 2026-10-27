
## Phase 7A notes (2026-10-27): Lab foundations, part 1

Phase 7 is split (owner request, 2026-10-27). **7A (this build):** partition with governed holdout, causal features and target, metrics, naive baselines, one frozen synthetic fixture. **7B (next, only when the owner says go):** HAR, GARCH (`arch`), negative controls, purged-CV cross-check, Optuna search with every trial in the ledger, `sx-lab` CLI, `Forecast` JSON records.

Built: `lab/pyproject.toml` (was empty), `sx_lab/partition.py`, `features/volatility.py`, `features/dataset.py`, `evaluation/metrics.py` (QLIKE, RMSE, interval coverage), `baselines/{base,naive}.py` (persistence, historical mean), `scripts/make_lab_fixtures.py`, fixture `tests/fixtures/lab/eurusd_h1_synth_1000.json` (SYNTHETIC GARCH, hash-pinned), 24 tests in `lab/tests/`. Decisions L1 to L4 (see `docs/DECISIONS.md` appendix).

Run by me (owner asked me not to spend effort on test runs): only the 24 new Lab tests (24 passed) and `ruff check` on the new files (one E501 found and fixed afterwards; that edit was not re-run by me), in a fresh venv with Python 3.12.3, pandas 3.0.2, numpy 2.4.4 (the repo pins pandas 3.1.0 and numpy 2.5.4; not installed here). The FULL suite, Python 3.14 on the Mac and the web app were NOT run by me; the web app was not touched.

Not verified / limits: see Lab known issues L-1 to L-7 in `docs/DEVELOPMENT_PLAN.md` (appended). No baseline has been scored on real data; no ranking of baselines is claimed.

Owner commands are in the delivery message. Next: Phase 7B only when the owner says go.
