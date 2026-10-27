
---

## Phase 8 split (owner request, 2026-10-27)

Phase 8 is divided in two so each piece fits a session and so the experiment spec is frozen BEFORE any challenger model exists. Nothing below is built yet. Phase 8 question is unchanged: **does Mamba beat HAR and GARCH on volatility?** A documented tie or loss is a valid result.

### Phase 8A: experiment infrastructure and the frozen spec (no neural models)
**Goal:** everything EXP-001 needs except the challengers, plus the pre-registration committed first.
- **Feasibility spike (first, before any code):** can the challengers run at all on the owner's machine? `minimamba` needs PyTorch, and the owner's Mac is Intel (x86_64, Python 3.14.3). I believe recent PyTorch releases have no Intel-Mac wheels; this is UNVERIFIED. Check in the sandbox and on the Mac, and record the answer in `docs/DEPENDENCIES.md`. If it cannot run locally, decide where EXP-001 runs (Linux box, rented CPU/GPU, Colab) before building 8B.
- **Real data path:** EXP-001 must not run on the synthetic fixture. Decide the data source (OANDA practice is unconfirmed, issues 18 and 24; alternatives: Dukascopy export, another broker's demo, owner-supplied CSV/Parquet) and add an importer through `sx_data`/`sx_core.storage` with quality checks. Add the **weekend/gap policy** for features and targets (known issue L-2).
- `calibration/conformal.py`: split-conformal intervals with coverage tracking, verified for time-series validity (exchangeability caveat written down and tested). Replaces the non-conformal interval of decision L5 in `records.py`.
- `evaluation/model_confidence_set.py`: arch MCS (and SPA if useful). Read the `arch` source for the bootstrap block length and seed handling before adopting.
- `regime/markov_switching.py` (statsmodels, **filtered** probabilities only, causality-tested with the Phase 2 harness) and `regime/changepoints_offline.py` (ruptures, offline labelling only, tagged Retrospective).
- CLI: `sx-lab lock` and `sx-lab open-holdout` wrapping `LabPartition.lock_evaluation` / `open_holdout` (the CLI still never opens the holdout by itself).
- `lab/experiments/prereg/EXP-001.yaml` written, **owner-approved, hashed and locked in the ledger** before 8B starts: data window, horizon, models and their pinned versions, primary metric (QLIKE), secondary (RMSE, coverage), MCS level, number of variants allowed, stopping rule, what counts as a win, tie or loss.
- Tests: conformal coverage on frozen fixtures, MCS on a known-answer fixture, regime filtered-only causality, spec-hash refusal.
- **Done when:** the spec is locked, conformal and MCS tests pass, the real-data path loads a quality-checked dataset, and the feasibility spike has a recorded answer.

### Phase 8B: challengers and the one experiment run
**Goal:** run EXP-001 once under the locked spec and report it honestly.
- `models/minimamba_vol.py` (CPU, MPS optional): **pin the exact version, read the source, sanity-check** shapes, scan causality and determinism. `mamba_ssm_vol.py` stays a stub until a CUDA GPU exists.
- `models/nf_baselines.py` (NHITS, PatchTST, LSTM) and `models/chronos_zeroshot.py` as baselines only; **include them only if the owner approves the heavy dependencies in 8A's spec**.
- Runner that refuses to start if the spec hash differs from the lock, if the data label is SAMPLE/synthetic, or if the holdout was already opened.
- Run EXP-001 **once**; every trial and seed goes to the ledger (variants-tried count). Open the holdout exactly once, through the logged call.
- `lab/experiments/EXP-001_mamba_vs_har.md`: results with the model confidence set, coverage and variants tried. Status labels `Exploratory` and `Not validated`.
- Web: Lab screen and the Forecast tab (interval, regime label, track record, variants tried, honesty labels; zod mirror of `Forecast` if not yet present). Web checks run as in Phase 5B.
- **Done when:** EXP-001 is run once under the pre-registered spec and reported with the model confidence set and coverage; web Lab and Forecast tab show it with labels.

### Owner decisions needed before 8A starts
1. Real data source for EXP-001 (see above). Without it, 8A can be built and tested but 8B cannot be run honestly.
2. Where the neural models will run (feasibility spike result).
3. Whether neuralforecast and Chronos are in scope for EXP-001 (heavy dependencies) or only minimamba vs HAR/GARCH.
4. Approval of the proposed spec defaults L11 and L12 in `docs/DECISIONS.md`.
