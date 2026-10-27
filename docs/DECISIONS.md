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
| P6 | LLM analyst | Pydantic AI or the Anthropic SDK directly. Decide when `analyst/` starts. |
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
