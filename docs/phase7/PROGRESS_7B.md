
## Phase 7B notes (2026-10-27): Lab foundations, part 2

Built: `baselines/har.py` (OLS HAR-style), `baselines/garch.py` (`arch` used to ESTIMATE only; our own recursion forecasts), `evaluation/negative_controls.py` (shuffled labels, leaked-feature guard), `evaluation/purged_cv_crosscheck.py`, `search/optuna_search.py` (every trial logged to the ledger as `lab.trial`), `records.py` (contract `Forecast` records), `cli.py` (`python -m sx_lab.cli run | evaluate | search | report`, also `sx-lab` after `pip install -e lab`). Pins added to `lab/pyproject.toml`: `arch==8.0.0`, `optuna==5.0.0`. 17 new tests (41 Lab tests in total). Decisions L5 to L9.

Run by me (owner asked me not to spend effort on test runs): `pytest lab/tests` **41 passed** and `ruff check lab` clean, in a fresh venv with Python 3.12.3 and the repo's own pins (pandas 3.1.0, numpy 2.5.4), plus `pip-audit` (nothing except the venv's own `pip` 24.0) and one `evaluate` run of the CLI on the synthetic fixture. The FULL suite, Python 3.14 on the Mac and the web app were NOT run by me; the web app was not touched. No mutation checks this time.

What the one `evaluate` run showed (SYNTHETIC data, 147 validation rows, no ranking claimed): validation QLIKE historical_mean 0.101, persistence 0.195, har 0.105, garch11 0.091. The purged CV cross-check ordered the models differently (har best, then persistence, garch11, historical_mean), so the single-split ranking is not stable. The shuffled-label control FAILED for HAR (the label-shuffled fit was not worse), meaning HAR shows no measurable skill over a constant on that split; the leak guard PASSED (flagged only the planted leak).

Not verified / limits: see Lab known issues L-8 to L-15 in `docs/DEVELOPMENT_PLAN.md` (appended). Nothing has run on real data. I checked `arch` behaviour by cross-test (our GARCH recursion equals `arch`'s own forecast to 1e-6) and read the source only for `convergence_flag`; I did not read all of `arch` or `optuna`.

Phase 7 "done when" is only partly met: baselines run and the negative controls and variants count work, but not on real data (issues 18, 24). Next: Phase 8 only when the owner says go.
