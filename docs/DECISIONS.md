# Decisions

Status: **Proposed** (not yet confirmed) or **Confirmed**. Edit the status line when you decide.

## Confirmed

| ID | Decision |
|---|---|
| X1 | spekrym-x is a new, standalone project. It imports no code from any earlier project. |
| X2 | Two modules: Lab (volatility/regime forecasting) and Assistant (TA, premarket, suggestions, paper). They connect only through `core/` contracts and files. |
| X3 | Paper trading only. No live execution path exists. |
| X4 | Web stack: React, TypeScript, Tailwind, TradingView Lightweight Charts, built with Vite. |
| X5 | UI theme: warm Claude Code style, dark and light modes. |
| X6 | Home screen: the guided Premarket workflow. The live chart with suggestions is one click away. |
| X7 | Mamba challenger: `minimamba` on CPU (MPS optional). The official `mamba-ssm` needs a CUDA GPU and is deferred. |
| X8 | Until the backend exists, the UI runs on frozen sample data, always labelled **Sample data**. |
| X9 | Python 3.12 or newer. Raised from 3.11 on 2026-10-27 by the owner because the pinned `numpy==2.5.4` requires 3.12+ (PyPI metadata checked: wheels for cp312 to cp315, including macOS arm64). `numpy` stays pinned. |
| X15 | Phase 6 split into 6A (simulator core) and 6B (gates, frozen rules, runner). Simulator-first (P5) taken as confirmed by the owner's "proceed" on 2026-10-27; only the simulator is built, no OANDA practice backend. |
| X16 | **Phase 8 close-out (owner, 2026-10-28): mark Phase 8 done PROVIDED (1) the implemented work and the experiment records are committed and (2) the close-out checks pass (backend `pytest -q`, `ruff check .`, web typecheck, lint, tests, build).** Status: web checks and 81 web tests passed on the owner's Mac; backend suite and commit NOT yet confirmed, so Phase 8 is `Closed, pending commit and checks` until the owner reports them. Experiment records: `lab/outputs/` is git-ignored, so the ledger, `validation_results.json` and `holdout_results.json` are archived to the tracked folder `lab/experiments/EXP-001_records/` (copies; the originals stay in place; data Parquet and model weights stay out of git, the weights' hashes are in the ledger). NeuralForecast, Chronos and the regime display are moved to the clearly labelled LATER-PHASE BACKLOG (plan section 5b). They are NOT added to Phase 8's scope. Any new Lab model or retrained MiniMamba is a new pre-registered experiment (EXP-002 or later). |
| X17 | **Phase 9 is split into 9A, 9B and 9C (owner, 2026-10-28).** 9A = `assistant/model` (labels, features, LightGBM, SHAP reasons, scorer), no LLM. 9B = suggestions engine, evidence links, Suggestions screen. 9C = analyst (LLM brief, debate step, prompts). 9A and 9B do not need P6. **P6 (Pydantic AI vs Anthropic SDK) must be decided before 9C starts**; Claude's lean is the Anthropic SDK directly behind an adapter. **Lab badge (owner confirmed, 2026-10-28), folded into 9A:** on the Lab screen the top-bar "Sample data" badge and the status-line "SAMPLE DATA - NOT LIVE" text refer to the premarket chart sample and do not describe what the Lab shows. Hiding them is a PRESENTATION-ONLY change: the dataset's provenance label stays in the data and in every other screen; nothing is relabelled as real; the Lab screen must instead show the accurate provenance of what it displays (the EXP-001 data label `OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED`, and each dataset's own label in the Data tab), and if any Lab view ever shows sample or synthetic data it must say so there. Tested. |
| X14 | **Previous-day levels use the previous completed trading day (was P10).** Approved 2026-10-27 by the owner. Monday uses Friday; Tuesday to Friday use the day before; weekends and holidays use the latest completed trading day; a day with any missing bar is never used, and the search goes back at most 5 trading days (`DEFAULT_MAX_LOOKBACK`), otherwise no level. "Completed" follows a per-instrument `TradingCalendar` (`core/src/sx_core/trading_calendar.py`); an unregistered instrument must be given a calendar explicitly. **Deviation from the owner's original wording, approved by the owner 2026-10-27:** trading-day boundaries stay at 00:00 UTC (X10, so D bars and levels agree); the market timezone (America/New_York, DST-aware) is used only for the Friday weekly close (17:00 New York = 21:00 UTC in US summer, 22:00 in winter), which is where DST changes the result. The Sunday-evening stub belongs to no trading day. Assumptions: close time 17:00 New York, no daily break, **empty holiday list** (a holiday with no bars is skipped as incomplete anyway; the list only keeps holidays from using up the lookback). A calendar-date rule ("previous calendar day") is a separate rule, not built. Safeguards (owner): UTC midnight for all ordinary day boundaries; New York time only for the Friday close; an incomplete Friday is never a confirmed weekly close; tests cover US clock changes and the Friday close in standard and daylight time (done). **UTC calendar days are not New York trading days; do not mix the two definitions.** |
| X13 | DST-aware sessions (was P9). Approved 2026-10-27 by the owner. London and New York windows follow their own local clocks and are converted to UTC per date; Asia is explicit (see I10). Internal timestamps stay UTC; logs and dashboard display `Asia/Colombo` (UTC+5:30, no DST). Daily bars stay at 00:00 UTC (X10). Built in `sx_core/local_sessions.py` (re-exported from `clock.py`) and `assistant/ta/sessions.py`. The display-zone helper exists (`to_display_time`) but is not yet wired into any log or screen. |
| X10 | Daily bars open at 00:00 UTC (H4 at 00/04/08/12/16/20 UTC). They are built from M1, not fetched from the broker. Confirmed 2026-10-26 by the owner. |
| X11 | Instruments: EUR/USD first, then the other majors (was P3). Confirmed 2026-10-26. |
| X12 | Timeframes: closed bars only. M15 and H1 execution, H4 and D context (was P4). Confirmed 2026-10-26. |

## Proposed (please confirm)

| ID | Decision | Default |
|---|---|---|
| P1 | Lab goal | Volatility and regime forecasting, not direction. |
| P2 | Holdout | `lab/partition.py` keeps a final holdout (train 60 / validation 20 / holdout 20, chronological) reachable only through one logged call. |
| P5 | Paper backends | Internal simulator first, then OANDA practice. IB paper later. **Simulator-first confirmed for 6A (X15); the OANDA practice backend remains proposed.** |
| P6 | LLM analyst | **RESOLVED 2026-10-28 by the owner (zero-cost multi-provider router, Groq and Gemini first): see A1.** Was: Pydantic AI or the Anthropic SDK directly. |
| P8 | Light-theme contrast | Five light tokens (accent, bull, asia, london, warn) are below 4.5:1 as small text. Options: darken those five light values, or keep them and only use them for large text, lines and fills. Owner to choose. |

## Implementation notes from Phase 2 (made by Claude, not yet reviewed by the owner)

| ID | Note |
|---|---|
| I1 | Ledger hash chain: `hash = sha256(previous_hash + canonical_json(entry without hash))`, first entry chains to 64 zeros. No `prev_hash` field was added, so `LedgerEntry` is unchanged. |
| I2 | Wire format: unset optional fields are omitted, never `null` (zod `.optional()` rejects `null`). `Contract.to_wire()` does this. Ledger lines also omit an unset `rules_version`. |
| I3 | The paper guard refuses any `SX_TRADING_MODE` other than the exact string `paper` (including unset) and any `OANDA_ENV` other than `practice`. |
| I4 | The fixed-UTC `SessionConfig` (Asia 00-07, London 07-12, NY 12-17) must not overlap. It still works and is kept for compatibility. The DST-aware `LocalSessionConfig` (X13) may overlap; see I10. |
| I5 | Ids are `prefix:` plus 16 hex of SHA-256 over canonical JSON of semantic fields; floats are rejected so prices cannot enter an id. |

## Implementation notes from Phase 3 (made by Claude, not yet reviewed by the owner)

| ID | Note |
|---|---|
| I6 | M1 is the only fetched timeframe that matters. The client can also fetch M5 to H1, but never H4 or D. M15, H1, H4 and D are always rebuilt from cached M1 so every timeframe agrees. |
| I7 | A resampled bar exists only if its window has ended by `as_of` (default: close of the last source bar). Missing source bars are never filled; a window with no source bars produces no bar. |
| I8 | The client drops the still-forming candle and clips results to `[start, end)`, with `end` clamped to now. Retries (429, 5xx, network errors) use `Retry-After` or exponential backoff; 4xx other than 429 are not retried. |
| I9 | `feed_degraded` is true on duplicates, out-of-order or off-grid bars, crossed quotes, incomplete bars, unexpected gaps over 3 bars, or a stale feed. Thresholds and the weekly closure window are assumptions (`GapRules`). |

## Implementation notes from Phase 4 (made by Claude, not yet reviewed by the owner)

| ID | Note |
|---|---|
| I10 | **Approved by the owner 2026-10-27 as strategy-defined windows, not the venues' official hours.** `asia` 09:00 to 16:00 Asia/Tokyo (Japan has no DST, so exactly 00:00 to 07:00 UTC all year); `london` 07:00 to 12:00 Europe/London; `ny` 07:00 to 12:00 America/New_York. In winter these equal the old fixed UTC sessions. Summer: London 06 to 11 UTC, NY 11 to 16 UTC. London and Asia overlap 06 to 07 UTC in UK summer, and London and NY overlap 11 to 12 UTC while only the US is on summer time (second Sunday of March to the last Sunday of March, and the last Sunday of October to the first Sunday of November). `session_at` returns the session that opened most recently; `sessions_at` returns all. Change the hours by editing `DEFAULT_LOCAL_SESSIONS`; nothing else depends on them. Local times that do not exist or are ambiguous on a date raise `ValueError`. Intervals are `[start, end)`. Pinned by `test_default_sessions_are_the_approved_i10_hours`. |
| I11 | Orientation of high/low objects (swings, session levels): a high is `bearish` (a level overhead), a low is `bullish` (underfoot). It describes where the reference sits, not a forecast. Liquidity sweeps are `neutral`. Lifecycle logic relies on this. |
| I12 | The SMC library is not causal as shipped (see `smc_adapter.py` docstring). `causal_wrapper.replay_first_seen` runs it on every prefix and freezes each object at first sight, so output can differ from one library call on the full series. That is intended. Cost is quadratic in bars: about 5 s for 28 bars of the harness, about 10 s for 40. |
| I13 | Producers always emit `lifecycle = fresh`. `normalize.lifecycle_at` / `as_of` compute the lifecycle at time `t` from bars that closed by `t`. Zones: `tested` when a bar's range enters, `mitigated` when a bar closes beyond the far edge. Swings and session levels: `broken` when a bar closes beyond. BOS, CHoCH, liquidity sweeps and candle patterns do not evolve. |
| I14 | Session and previous-day levels are emitted only when every bar of the window is present, and only once the window has ended (`known_at` = window end). Incomplete or gappy windows emit nothing. Previous-day levels follow the trading calendar (X14, I18), so Monday gets Friday's. |
| I15 | **Split on 2026-10-27.** Approved: explicit, configurable definitions of candle measurements (range, body, wicks, body-to-range, doji, pin bar, engulfing, strict vs inclusive comparisons, zero-range handling), now written in `ta/candle_metrics.py` with boundary tests. **Numbers: provisional defaults, confirmed by the owner 2026-10-27 as configurable engineering starting points, not validated or calibrated trading parameters. No sample-data result may be used to claim they are profitable. Original wording: not approved:** (`CandleRules` defaults: doji body/range <= 0.10, pin body/range <= 0.35 and long wick >= 2 x body, engulfing strict). They are proposed defaults to be checked against the owner's specification. `candle_metrics` is **not wired into the pipeline**: the emitted candle setups still come from TA-Lib (engulfing, hammer, shooting star, morning star, evening star), emitted only if ATR(14) exists and a causal level lies within 0.5 x ATR of the bar's range (`DEFAULT_ATR_PERIOD`, `DEFAULT_PROXIMITY_ATR`). TA-Lib's own shape thresholds are not the ones in `CandleRules`. |
| I16 | `Setup.geometry` is an axis-aligned box. A sloped trendline is stored as the bounding box of its endpoints, with the slope in `plain_text`. No contract field was added. |
| I17 | (Issue 27) The SMC adapter's default engine uses numpy ports of `swing_highs_lows`, `bos_choch` and the newest-bar FVG (`ta/smc_fast.py`); `engine="library"` keeps the original path. Output is identical (tests compare every prefix of the fixtures and of 16 random series, with ties, for swing lengths 1 to 3). Order blocks and liquidity still call the library; they are now about 80% of the replay time. Replay is still quadratic, just about 4 to 5 times faster. |
| I18 | `previous_day_levels(candles, on, calendar, max_lookback)` is the function that answers "which levels apply on date `on`". `session_setups` still emits a previous-day pair for **every** complete trading day, each with `known_at` = end of that day's trading window (Friday: the weekly close, not midnight). Text changed from "UTC day" to "trading day". |

## Open questions

- Is a GPU available later for the official Mamba reference?
- Is the optional calendar pilot (forex-pytory) worth the scraping risk, or should the calendar come from a plain JSON feed?
| I19 | (Phase 5A, 2026-10-27) Data comes through `MarketDataSource` (`premarket/data_source.py`). The only source is `FixtureSource`: a frozen synthetic M15 fixture (`tests/fixtures/premarket/eurusd_m15_sample.json`, seed 42, hash pinned) with H1/H4/D built by `sx_data.resample`. Its label is `SAMPLE DATA — NOT LIVE` and `live` is false. A provider may set `live` true only after it has fetched real candles. |
| I20 | (Phase 5A) The premarket analysis window is the last 3 calendar days of M15 (`WINDOW_DAYS`), because replay cost is quadratic (issue 27). The builder is read-only and `as_of`-driven; the API caches payloads in memory per `(instrument, as_of)`. |
| I21 | (Phase 5A) The bias checklist states facts from closed D and H4 bars and never a verdict, score or probability (tested by a banned-words check). |
| I22 | (Phase 5B) The web app reads one `Dataset` through `useDataset()` (`apps/web/src/data/`). The `DataProvider` asks the API (`VITE_API_URL`, default `http://127.0.0.1:8000`) with TanStack Query and validates the payload with zod. If the API is unreachable or the payload is invalid, the UI shows a visible banner and the built-in offline sample labelled `Sample data (offline copy, not from the API)`; it never presents the offline copy as API data. `VITE_DATA_SOURCE=sample` forces the offline copy. |
| I23 | (Phase 5B) The chart draws only `session_level` (lines) and `liquidity_sweep` (markers). Other setup kinds are counted ("N other detected objects ... not drawn yet") and stay in the data (known issue 36). |
| I24 | (Phase 5B) ATR is computed in the web app from the closed bars known at the replay time: Wilder ATR(14) on M15, first value = mean of the first 14 true ranges. It is shown as a plain distance (pips and multiples of ATR) from the last close; it is a measurement, not a forecast. It has not been cross-checked against TA-Lib. |
| I25 | (Housekeeping) The repo-root `pyproject.toml` (ruff and pytest config) was missing from the delivered repo, so ruff ran on defaults and printed 70 findings. It was RECONSTRUCTED: ruff line-length 100, target py312, rules E, F, B, UP (inferred from existing `noqa` comments and verified at zero findings); pytest testpaths are the five test folders. Owner to confirm it matches any original in git history. |
| I26 | (Phase 6A) Fill model: entry is a touch order (long fills when ask <= entry, short when bid >= entry) at the touching quote's ask or bid plus slippage against the trader; stops fill at bid (long) or ask (short) minus or plus slippage; targets fill at the target price. No exit on the quote that filled the order. Quotes must arrive in time order or the broker raises. Provisional slippage 0.00002; all numbers unapproved. |
| I27 | (Phase 6A) `PaperOrder` gained no field. The rejection reason and exit reason travel in the event `detail` passed to the listener and written to the ledger, not on the order. Order events logged: order_submitted, order_filled, order_closed, order_rejected, order_cancelled. |
| I28 | (Phase 6A) The broker takes `RiskGate` objects and a shared `KillSwitch`; with no gates it still enforces request validity and the kill switch. Real gates are Phase 6B. |
| I29 | (Phase 6B) Frozen rules: `rules/ruleset.py`. The hash is SHA-256 over the canonical JSON of the parsed rules (layout does not matter, values do); `freeze` writes `<file>.lock` once and refuses to change it; the runner refuses to start without a lock or on a mismatch. `rules_version` stamped on every order and ledger entry is `<version>-<first 12 hash chars>`. A rule change means a new rule file and a new run. |
| I30 | (Phase 6B) `PaperRunner` is the supported entry point: it stamps the run's rules version on the request (overriding the caller's), builds the three gates from the frozen rules, owns the kill switch and tracker, and writes a `run_started` ledger entry with the rules and hash. Order of checks in the broker: kill switch, request validity, then gates in order (blackout, max open, daily loss). |
| I31 | (Phase 6B) Shipped rules `paper_v1`: max 2 open or pending orders, daily loss limit 100.0 (quote currency), no blackouts. Provisional and unapproved. OANDA practice backend not built (P5 remains proposed for it). |
| I32 | (Chart pass) Zones (`fvg`, `order_block`) are boxes from `t_start` to the right edge (or the replay time); `bos`/`choch` are lines from `t_start` to `t_end` with a tag. Colours are the existing bull/bear/muted tokens and mean ORIENTATION only (I11), never a forecast; the accent is not used. Mitigated or broken zones are drawn faded. Replay hides a zone before its `known_at` and clips it at the replay time. |
| I33 | (Chart pass) Presets cap session levels/events (`maxItems`) and zones/structure lines (`maxZones`: premarket 6, execution 4, clean 0, everything unlimited) separately, ranked by distance to price, so many small zones cannot push session levels off the chart. No minimum zone size was added (issue 26: needs evidence). Step 3 shows session levels and events only; steps 4 to 6 add zones and structure. |
| I34 | (Chart pass fix) The timeline lists session groups, sweeps and BOS/CHoCH lines, but NOT FVG or order-block zones (43 of them flooded it and pushed the chart off the screen in the owner's first look). The timeline list also scrolls inside a short box (`max-h-24`). Zones are still drawn on the chart and listed in the objects panel. |

## Lab decisions from Phase 7A (owner approved P1 and P2, 2026-10-27)

| # | Decision | Status |
|---|---|---|
| L1 (was P1) | Lab goal is volatility and regime forecasting, not direction. Direction is a separate research question. | Confirmed (owner, 2026-10-27) |
| L2 (was P2) | Chronological 60/20/20 train/validation/holdout. Holdout is opened by one logged call, only after the evaluation spec hash is locked in the ledger, and once per holdout content; later calls are refused. | Confirmed (owner, 2026-10-27) |
| L3 | Embargo: `embargo >= horizon` rows are dropped before validation and before the holdout so overlapping target windows cannot straddle a boundary. Default embargo = horizon; smaller is refused. Claude's choice, not yet reviewed. | Proposed |
| L4 | Variance scale: features, target and forecasts are per-bar means of squared close-to-close log returns. Target = mean over bars t+1..t+h from the bar-t close. Horizon must be one of the feature windows. Claude's choice, not yet reviewed. | Proposed |

## Lab decisions from Phase 7B (Claude's choices, not yet reviewed by the owner)

| # | Decision | Status |
|---|---|---|
| L5 | `Forecast` interval in 7B is the training-set quantile band of target/prediction ratios (80% nominal), widened so the point lies inside. It is NOT conformal; Phase 8 replaces it. Empirical coverage is measured and stored in `track_record`. Point and interval are per-bar volatility (sqrt of mean squared return). Status `exploratory`. | Proposed |
| L6 | HAR is a level OLS on rv_6, rv_24, rv_120. Predictions are floored at the smallest training target; the count floored is reported. | Proposed |
| L7 | GARCH(1,1): `arch` estimates omega, alpha, beta on the training frame; forecasts use our own recursion (started from the first row's rv_120) so no library forecasting behaviour is assumed. A non-converged or non-stationary fit raises and is shown as FAILED, never hidden. | Proposed |
| L8 | Search: Optuna TPE (seeded) over HAR short window {3,6,12} and long window {72,120}, objective = validation QLIKE, every trial in the ledger as `lab.trial`. `variants_tried` counts trials including repeats. The dataset is built once with windows (3,6,12,24,72,120) so every trial shares one holdout. | Proposed |
| L9 | CLI exit code: `evaluate` returns non-zero only if the leak guard fails. A failed shuffled-label control is reported as "no measurable skill", not as an error. The CLI never opens the holdout. | Proposed |

## Lab decisions from the Phase 8 split (2026-10-27)

| # | Decision | Status |
|---|---|---|
| L10 | Phase 8 is split into 8A (infrastructure, conformal, MCS, regime, data path, frozen pre-registration) and 8B (challengers, one EXP-001 run, results, web Lab screen). | Confirmed (owner request, 2026-10-27) |
| L11 | The EXP-001 runner refuses to start on data labelled SAMPLE/synthetic, if the spec hash differs from the ledger lock, or if the holdout was already opened. | Proposed |
| L12 | Proposed spec defaults for EXP-001 (owner to approve or change in 8A): H1 bars, horizon 24, primary metric QLIKE, secondary RMSE and interval coverage, model confidence set at 10%, split 60/20/20 with embargo = horizon (L2, L3), holdout opened once, an explicit cap on variants tried. | Proposed |

## Lab decision from the Phase 8A feasibility check (2026-10-27)

| # | Decision | Status |
|---|---|---|
| L13 | Challenger models (minimamba, neuralforecast, Chronos) cannot run in the Mac venv (see PROGRESS 8A feasibility). Proposed: build all 8A infrastructure and the frozen spec on the Mac as planned; run the neural challengers in a separate Linux environment (rented CPU/GPU, Colab, or the Claude sandbox if it has enough CPU time), exchanging data and results as Parquet/JSON files with their hashes recorded in the ledger. The Mac keeps HAR, GARCH, MCS, conformal and the web app. Alternative the owner may choose: change the EXP-001 question so that it needs no torch (not recommended: it drops Mamba, the point of the experiment). | Proposed |

## Phase 8A answers (owner decisions, 2026-10-27)

Numbering follows the existing log (L10 confirmed; L11 and L12 proposed; L13 proposed). Adjust L14 and L15 if those numbers are already taken.

### L12: EXP-001 default specification: CONFIRMED
Recorded as the experiment's initial configuration, not as universally optimal settings.

| Item | Value |
|---|---|
| Forecast input timeframe | H1 bars |
| Forecast horizon | 24 hours |
| Primary metric | QLIKE |
| Model confidence set level | 10% |
| Partition | chronological 60/20/20 train/validation/holdout |
| Holdout access | one explicit, logged evaluation call, only after the spec and model selection are frozen |

Safeguards:
- Leakage controls at every partition boundary must cover the 24-bar horizon (purge or embargo of at least 24 bars).
- Logging access to the holdout is necessary but not sufficient. A second open must be refused by the runner, and results seen on the holdout must not feed back into model or spec changes. A changed spec is a new experiment with a new ID.
- To check before freezing: `lab/src/sx_lab/partition.py` must implement exactly this split and the purge. This is not yet verified.

### L13: Where neural models run: AMENDED (supersedes the Proposed text)
- Mac (Intel x86_64): data preparation, Naive/HAR/GARCH baselines, evaluation, reporting, development.
- Linux: initial target for MiniMamba execution.
- MPS/GPU: not a requirement for EXP-001.
- Spike finding (see PROGRESS entry): PyTorch 2.14.1 and minimamba 1.0.1 do run on the Mac from a conda-forge environment. Throughput is about 3,000 tokens/s for a tiny model, so the Mac is a viable fallback or smoke-test host for small configurations.
- Revisit trigger: if the frozen spec fixes a small model (about 64 dimensions, 2 layers) and short context (24 to 64 bars), running on the Mac becomes practical. Larger configs, long context or a large search budget stay on Linux.
- conda-forge Intel-Mac builds may stop being published. Whatever environment runs the experiment must have exact versions and hashes recorded in the ledger.

### L14: Real data source for EXP-001: PROPOSED to CONFIRMED
- OANDA practice is the primary operational source (bid, ask, mid; closed candles; UTC timestamps).
- Dukascopy is retained for historical research and cross-checking, subject to data-quality and timestamp validation.
- Phase 8A uses a frozen, versioned dataset. Neither provider is treated as verified just because its module exists.
- Before the first real-data experiment, verify actual output, coverage, missing bars, timezone handling and reproducibility. The runner must refuse sample or synthetic data (L11).

### L15: Model scope for EXP-001: CONFIRMED
| Model | Role |
|---|---|
| Naive | required reference baseline |
| HAR | strong interpretable volatility baseline |
| GARCH | classical volatility baseline |
| MiniMamba | initial neural challenger |

NeuralForecast and Chronos are deferred. Their install and runtime compatibility are unverified. The research question stays: does MiniMamba improve volatility forecasting over HAR and GARCH on the specified evaluation? A tie or a loss is a valid result.

### 8A scope boundary
In scope: infrastructure, data provenance, chronological partitions, evaluation safeguards, the experiment specification and dependency verification.
Out of scope: model training. No training until those foundations are tested and EXP-001.yaml is owner-approved and hash-locked.

## Phase 8A build decisions (2026-10-27)

**Interpretation of the owner's "proceed 8A" (made by Claude, owner may revert).** The owner did not answer the four questions in the status message. Following the precedent of X15, "proceed" was taken as confirming: L3 (embargo >= horizon), L4 (per-bar variance scale), L5's replacement by conformal, L11 (runner refuses sample/synthetic data, a changed spec hash, or a second holdout open), and L13 as amended. For real data (L14) the importer was built and tested on fixtures only; no real file was supplied, Dukascopy was not built (`dukascopy.py` is still empty).

| # | Decision | Status |
|---|---|---|
| L16 | Gap policy `trading_time_windows_v1` (`lab/features/gaps.py`): a return spanning a gap is excluded from every window and from the target; the bar after a gap is not a row; windows and the horizon count valid bars (trading time); `target_known_at` is the close of the bar ending the window. An unexpected gap longer than the `sx_data.quality` tolerance (3 bars), duplicates, off-grid or out-of-order bars are REFUSED, not bridged. Equals `make_dataset` exactly on gap-free data (tested; the owner's 7B numbers reproduce). | Proposed |
| L17 | Conformal (`calibration/conformal.py`): score ln(y/f), two-sided split conformal with finite-sample ranks; calibrate on the first half of validation, report coverage on the later half with an embargo equal to the horizon between them. Guarantee needs exchangeability, which volatility does not satisfy: coverage is measured and reported, never assumed. `make_forecasts(..., conformal=...)` uses it; without it the 7B band (L5) is unchanged. | Proposed |
| L18 | Model confidence set (`evaluation/model_confidence_set.py`): `arch.bootstrap.MCS`, stationary bootstrap, QLIKE losses per row, block size >= horizon (refused below), fixed seed from the spec, default level 0.10 (L12). | Proposed |
| L19 | Regimes: 2-regime Markov switching on a log-variance series, parameters fitted on TRAINING only, probabilities from `MarkovRegression(new).filter(params)` (filtered, never smoothed). statsmodels 0.15.0 has no `results.apply`. Deterministic start values. Non-convergence raises. Change points (ruptures PELT) are offline and tagged retrospective. | Proposed |
| L20 | Spec and lock mechanics (`spec.py`, `cli_experiment.py`): hash = SHA-256 of canonical JSON of the whole parsed spec; `lock` and `open-holdout` need status `approved`, an approval block, a provenance sidecar whose file hash still matches, a non-sample label, and spec data fields equal to the file. `open-holdout` also needs `--reason` and `--confirm-spend-holdout`, and works once. `EXP-001.yaml` is a DRAFT; it cannot be locked until real data exists and the owner approves it. | Proposed |

**L19 amendment (2026-10-27, after the owner's `pip install -e lab` failed):** `ruptures` 1.1.10 requires Python < 3.14 and the owner runs 3.14.3, so it is not a dependency. Offline change points use an in-house exact PELT with an L2 cost (`regime/changepoints_offline.py::pelt_l2`), tested against a brute-force oracle. `ruptures` is an optional cross-check extra (`pip install -e "lab[crosscheck]"`, Python < 3.14 only). Still retrospective-only. Lesson: a library's Python-version bound must be checked against the OWNER's interpreter (3.14.3), not the sandbox's (3.12).

### 8B decisions (2026-10-28, made by Claude while building; owner may revert; all PROPOSED)
| ID | Decision | Status |
|---|---|---|
| L21 | The locked EXP-001 spec fixes the MiniMamba size but not how it is trained. Training choices fixed in code (`models/minimamba_vol.py::TrainConfig`) before any validation score was seen and never tuned: 8 epochs, batch 64, AdamW lr 1e-3, weight decay 1e-4, grad clip 1.0, QLIKE loss on log-variance (head on the last step), no early stopping, no dropout, features standardised on train, rv/range/ATR logged. "MiniMamba" in the model confidence set is the mean of the log-variance forecasts of seeds 1, 2, 3; no seed is selected; per-seed scores are diagnostics. Each seed is logged as a ledger trial (study EXP-001), so variants tried = 3 of the 20 allowed. | **Confirmed** by the owner 2026-10-28 (accepted as written; any change to the training recipe is a new pre-registered experiment, EXP-002) |
| L22 | The spec does not say whether win/tie/loss is judged on validation or on the holdout. The report states both and uses the HOLDOUT outcome as the headline once it exists, because the holdout is the untouched sample. The spec's `inconclusive` rule (added before the lock) covers any case the three rules miss. | **Confirmed** by the owner 2026-10-28 (accepted as written; any change to the training recipe is a new pre-registered experiment, EXP-002) |
| L23 | Two commands: `sx-lab exp001-validate` (checks lock, pins and data; trains 3 seeds on train; scores validation; MCS; conformal; saves weights and logs their hashes plus the model choice) and `sx-lab exp001-holdout --reason ... --confirm-spend-holdout` (re-verifies every hash and that baselines reproduce their validation scores, only THEN opens the holdout, writes the frame to disk at once, scores the same weights). Validation runs once per spec hash. `sx-lab exp001-report` writes `EXP-001_mamba_vs_har.md` from the JSON files. Conformal bands are calibrated on the first half of validation; validation coverage is measured on the later half after the embargo; holdout coverage on all holdout rows. | **Confirmed** by the owner 2026-10-28 (accepted as written; any change to the training recipe is a new pre-registered experiment, EXP-002) |
| L24 | Phase 8C web surface for EXP-001. The API serves the stored stage JSON read-only (`GET /lab/exp001`, field whitelist, `environment` dropped, refuses mixed spec hashes). The Lab screen has a Data tab and an EXP-001 tab that shows the holdout (headline, L22) and the validation result side by side, MCS membership, measured coverage, variants tried (n of 20), and per-seed training loss vs validation QLIKE. The Inspector Forecast tab says plainly that no live forecast exists and summarises EXP-001; it never shows a probability. Nothing in the web app computes or retypes a result. | **Confirmed** by the owner 2026-10-28 ("proceed with Phase 8C") |
| L25 | **Lab dataset management (owner request, 2026-10-28).** Datasets can be deleted from the Lab Data tab. Delete moves the file and its provenance record to `<data folder>/.trash` (recoverable; restore never overwrites); "Delete for good" is a separate confirmed step. A dataset is refused for deletion while its data version or file name appears in any `lab/experiments/**` file (locked specs, records, ledger) or `assistant/outputs/model/*` file. The protection is a text match, not a registry: a file referenced only elsewhere (for example a note outside those folders) is not protected. |

## Phase 9A decisions (2026-10-28, made by Claude while building; owner may revert; all PROPOSED)

| ID | Decision |
|---|---|
| M1 | **Label.** Triple barrier on H1 mid prices: entry = close of the decision bar; target 1.5 x ATR(14) in the setup direction, stop 1.0 x ATR, time barrier 24 bars. Label 1 = target first; 0 = stop first or time ran out; a bar touching both counts as STOP (conservative); rows without 24 future bars get no label. Barrier multiples are my provisional numbers, untuned, no costs (diagnostic only, principle 9). |
| M2 | **Decision time.** The first bar whose close is at or after the setup's `known_at`. Only directional setups (bullish or bearish) are scored; neutral ones are skipped. |
| M3 | **Purge gap = 72 bars = label horizon 24 + feature look-back 48**, written into `ProtocolSpec` (`purge_bars`, refused if below horizon + look-back). Reasoning: a train row's label reads bars up to `i + 24`; a validation row's features read at most 48 bars back (every window and the setup age are capped at 48). With a 72-bar gap no train label window shares a bar with any validation feature window, and the same between validation and holdout. `assert_purged` checks this on the actual rows. EXP-001 used an embargo of 24 because its target was a 24-bar window only; the scorer has a longer data dependency, so it needs a longer gap. |
| M4 | **Score = rank, not a probability.** `rank_score` (0 to 100) is the share of reference scores (the validation-period raw scores saved with the model) that are not above this setup's raw score. Every `ScoredSetup` carries at least one SHAP reason and the labels Exploratory, Not validated, Retrospective, or it refuses to exist. |
| M5 | **Selection and metrics.** 5 LightGBM variants (grid in `protocol.py`), chosen by validation AUC; reported with n, base share and the share of historical setups whose target came first among the top-scored fifth. AUC interval is an iid bootstrap and says it is optimistic (overlapping labels). No calibration step, because nothing is shown as a probability. |
| M6 | **Negative controls.** Shuffled labels: 20 shuffles, each repeating the SAME best-of-grid selection, so the range includes the luck of picking the best variant (a first version without this made a random-walk result look like skill; found in the smoke run). Leaked feature: a future-return column is added; the scorer must look excellent AND the leak scan (single-feature AUC above 0.85) must flag it and must not flag any real feature. |
| M7 | **Verdict rules** (stated before any real run): both periods above the shuffled range = Exploratory only; holdout above but validation not = inconsistent, treat as null, never report the holdout alone; validation above but holdout not = did not hold up; neither = NULL. |
| M8 | **Holdout reuse policy.** The holdout id is a hash of its rows. Opening needs a lock whose spec hash, config hash, candle data version and split hashes all match; the opening is written to the ledger before data is returned; a second opening is refused; a lock after opening is refused. A later experiment needs NEW holdout rows (later data); the spent holdout may then be used only as validation data under a new spec that says so. Process rule, not security (same limit as L-3). |
| M9 | **File names follow the code, not the plan text.** The repo already had `labels_triple_barrier.py`, `train_lgbm.py`, `explain_shap.py` (the plan says `labels.py`, `train.py`, `reasons.py`). I kept the existing names and added `protocol.py`, `controls.py`, `windowed.py`, `run.py`. Setups on a long history are computed on overlapping windows (240 warm-up + 240 new bars) because the full replay is quadratic (issue 27); a setup near a window start sees only 240 bars of history, so grouping that needs longer history can differ from a single full run (issue 29). |
| M10 | **Lab badge (X17), as built.** On the Lab screen the top-bar `Sample data` badge, the footer `SAMPLE DATA - NOT LIVE` text and the footer last price are hidden (the price would otherwise appear with no label). The footer says each Lab panel shows its own provenance. The Data tab got a `Source label` column (each dataset's own label, or `No label recorded`); the EXP-001 panel already shows its data label. Other screens unchanged. The API-unreachable banner (a real error) is still shown on every screen. |


## Phase 9B decisions (2026-10-28, made by Claude while building; owner may revert; all PROPOSED)

| ID | Decision |
|---|---|
| S1 | **H1 only.** The 9A scorer was trained and validated on H1 bars, so `build_suggestions` refuses any other timeframe. The `Suggestion` contract is unchanged (no contract change in 9B); only the API envelope is new (CONTRACTS.md). |
| S2 | **Which setups become suggestions.** Directional, causal setups whose decision bar (M2) is among the newest 6 bars at `as_of`, with lifecycle `fresh` or `tested` at `as_of` (computed with `lifecycle_at`, not the stored value), best 10 by rank. 6 and 10 are my provisional numbers. |
| S3 | **Levels.** Entry = close of the decision bar; stop 1.0 x ATR and target 1.5 x ATR against and with the setup direction, the same multiples the 9A labels used (M1). Provisional, untuned, mid price, no costs. They are reference levels, not a recommendation. |
| S4 | **Evidence rule (`suggestions/evidence.py`).** Reasons are: the setup's `plain_text`, the scorer's SHAP reasons (all linked to that setup's id), and, only if a Lab `Forecast` is supplied, one claim linked to the forecast id. Every `evidence_id` must be a known setup or forecast id of THAT suggestion; otherwise the suggestion is rejected and listed under `rejected` (never silently kept or dropped). Claim text matching probability wording (`probab`, `chance`, `likel`, `odds`, `win rate`, `%`) is refused. |
| S5 | **No forecast is attached yet.** The Lab has produced no live `Forecast` (EXP-001 is an experiment result, not a Forecast), so the API sends none and `forecast_id` stays `null`. The engine supports a Forecast (tested) and refuses one issued after `as_of`. EXP-001 is never used as evidence. |
| S6 | **Gates are advice.** The engine runs the same gate classes the paper runner builds from the frozen rule set and shows each result. The API holds no paper account state, so the open-trades and daily-loss gates are checked against "no orders, zero P&L" and each says so in its detail text. The runner applies the gates again at order time. 9B adds NO order path (no suggestion-to-order function), so the "gates on every order path" rule is unchanged and is revisited when the Paper screen is built. |
| S7 | **A null 9A result does not hide suggestions, but is shown above them.** The screen always shows the 9A reading (validation vs the shuffled-label range, holdout verdict if opened, controls, variants tried). With no 9A result the list is empty and says why. If the owner prefers that a null result hide the list entirely, change `build_payload`. Open question for the owner. |
| S7a | **Decided by the owner 2026-10-28 (polish pass): keep the list, mute the rank.** The rank wording says `Position N of 100 ... 9A found no ranking skill` unless the holdout was opened and both periods beat the shuffled range (`rankDemonstrated` in `suggestions/format.ts`, keyed on the 9A verdict text `Both periods rank above`). Never says probability. |
| S8 | **Data source.** `/suggestions` uses the same data source as `/premarket`: today the frozen SAMPLE fixture, so suggestions in the browser are computed on sample bars, with the scorer trained on real data. The payload and the screen carry the source label. |


## Phase 9C-1 decisions (2026-10-28, analyst; made by Claude while building from the owner's `Spekrym_Zero_Cost_Analyst_Architecture.md`; owner may revert; all PROPOSED except A1)

| ID | Decision |
|---|---|
| A1 | **P6 resolved (owner, 2026-10-28: "start with these", Groq and Gemini keys supplied).** The analyst runs on a strict $0 budget through a provider-independent interface (`analyst/provider.py`) and a quota-aware router (`analyst/router.py`). Neither Pydantic AI nor the Anthropic SDK is used (the Anthropic API is paid); an Anthropic adapter could be added later behind the same interface, only if the owner chooses to pay. Groq first, Gemini second. Cloudflare Workers AI and OpenRouter are not built (9C-2 or later, only after testing). |
| A2 | **Approved-model gate.** A model can be used only if it is listed in `analyst/approved_models.json` AND the owner has set `owner_confirmed_free: true` (after checking the provider console shows a free plan with no billing). Shipped with both set to `false`: the CLI refuses to call until the owner flips them. No code path can reach an unlisted or paid model, enable billing or buy credits. |
| A3 | **No provider JSON mode in 9C-1.** The two providers document different structured-output shapes and per-model support that I could not exercise from the sandbox, so the prompt asks for one JSON object and OUR code parses and validates it (`validate.py`). Native JSON or schema modes can be added later per model after a live test. |
| A4 | **Failure policy.** One provider answers per request (first valid answer wins; others are not called). 429: cool the provider down for `Retry-After` (default 60 s, cap 24 h). 5xx, timeout or network error: cool down 30 s and fail over, never retry the same provider (a timeout may have used quota). 401/403 and other 4xx: disable the provider for the process. Invalid output: ONE repair request per brief in total, then the next provider. Maximum calls per brief = providers + 1. All failed: status `deferred`, no brief invented. Cooldowns are in memory only; persistence is 9C-2. |
| A5 | **Evidence rules for briefs.** Every claim needs at least one id that exists in the packet; an unknown id rejects the whole reply (one repair allowed). Probability wording (reuses the 9B check, which also refuses `%`) and trade-instruction wording (buy, sell, go long/short, enter, place an order; "buy-side/sell-side liquidity" allowed) reject the reply. A number in a claim that does not appear in the cited items marks that claim `unverified` (shown with a note), because a valid id does not prove a claim. Every brief is labelled Exploratory and Not validated and records the writing provider and model. |
| A6 | **Evidence packet.** Built only from a `PremarketAnalysis` (closed bars; every item `known_at <= as_of`, enforced): last close, the D/H4 checklist, and up to 12 non-broken setups nearest to the last close. Input is bounded to 24,000 characters per request and output to 2,000 tokens; larger input is refused, not trimmed. |
| A7 | **Model ids are unverified defaults.** `openai/gpt-oss-20b` (Groq) and `gemini-3.8-flash` (Gemini) were taken from the providers' current documentation pages (2026-10-28), not tested against the owner's accounts. `analyst.run check` lists what each key can see. Change with `SX_GROQ_MODEL` / `SX_GEMINI_MODEL`, and add the id to `approved_models.json`. |
| A8 | **Data terms: OPEN.** The evidence packet (levels, setups, checklist text) is sent to third-party providers whose free tiers may allow use of prompts for improvement. Only the frozen SAMPLE data is used in 9C-1. The owner has not yet said whether real data may be sent; read each provider's terms first. |
| A9 | **Secrets.** Keys come from `.env` (`GROQ_API_KEY`, `GEMINI_API_KEY`) through `Settings` as `SecretStr`; the Gemini key goes in a header, never a URL; error text is scrubbed of the key; the routing log holds no prompts or keys. The owner pasted both keys into the chat on 2026-10-28: treat them as exposed and rotate them. |


## Phase 9C-2 decisions (2026-10-28, made by Claude while building; owner may revert; all PROPOSED)

| ID | Decision |
|---|---|
| A10 | **Persisted provider state** in a small SQLite file (`assistant/outputs/analyst/state.db`, stdlib `sqlite3`), one row per provider and model: cooldown, disable reason, UTC-day request and token estimates, last error, last success. Wall-clock times so it survives restarts. Usage figures are LOCAL ESTIMATES (every request sent is counted, including timeouts); the provider's own 429 stays the real limit. The UTC day is used because the providers' real reset times are unknown here. |
| A11 | **Local daily request cap** per provider (`max_requests_per_day` in `approved_models.json`, shipped as 50, provisional and unreviewed). A provider at its cap is skipped before any call and the router fails over. It is a safety brake, not the provider's quota. |
| A12 | **A disable lasts until the key changes or the owner resets it.** A 401/403 or other 4xx disables a provider across restarts. A short hash of the key (8 hex characters of SHA-256) is stored so that a replaced key clears a stale disable automatically; `analyst.run reset --provider X` clears it by hand. The hash is never returned by the API or written to the routing log. |
| A13 | **Spend discipline in the service.** A saved brief for an unchanged evidence packet (same hash) is returned without any call unless `force`. Only one generation runs at a time; a second request gets `busy`. `GET /analyst/status` and `GET /analyst/brief` never call a provider; only `POST /analyst/brief` can. The routing log (`routing.jsonl`) has one line per attempt with a shared `route_id`, so failovers are visible; it holds no prompts, replies or keys. `.env` model overrides (`SX_GROQ_MODEL` and so on) are now read (9C-1 read only the real environment). |
