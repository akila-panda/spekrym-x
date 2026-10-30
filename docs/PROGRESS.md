# Progress

**Next action (2026-10-28, dataset management): the Lab Data tab can now delete datasets (to a recoverable trash), restore, delete for good, and shows an `In use` lock on files a locked experiment or saved model uses (L25). Owner restarts the API (new DELETE route and CORS), reloads the Lab screen and tries it on the 1-year file, NOT on `eurusd_h1.parquet` (it is locked). P6 still blocks 9C. See 'Dataset management' at the end.**

**Next action (2026-10-28, 9B polish): chart label overlap and the flat weekend stretch fixed, rank muted under a null 9A (S7a). Owner re-checks the Suggestions screen in the browser. P6 still blocks 9C. See 'Phase 9B polish' at the end.**

**Next action (2026-10-28, 9B bug fix): Phase 9A is RUN and its result is NULL (holdout spent). Phase 9B had one real bug, fixed here: `/suggestions` sent `forecast_id: null`, the web contract rejected it, so the Suggestions screen showed nothing. Fix: the API now uses `to_wire()`. Owner: unzip, restart the API, reload the Suggestions screen (9B done-when). Then decide S7 (null result and the suggestion list) and P6. 9C only after P6. See 'Phase 9B fix and 9A result' at the end.** (Older notes follow.)

**Next action (2026-10-28, docs-only update): Phase 8 is CLOSED PENDING the owner's commit of the experiment records and the close-out checks (X16). Phase 9 is split into 9A (model and scorer), 9B (suggestions and evidence), 9C (analyst) (X17). Start 9A only when the owner says go; confirm P11 first (the Lab badge fix is confirmed, presentation-only, folded into 9A). P6 must be decided before 9C.** (Older notes follow.)

**Next action (2026-10-28, latest): Phase 8C is built (web Lab EXP-001 tab + Forecast tab, API `/lab/exp001`); the owner runs the checks in 'Phase 8C notes' at the end, then looks at the Lab screen with the API running. Phase 9 only when the owner says go AND decides P6.** (Older notes follow.)

See `docs/DEVELOPMENT_PLAN.md` for the full phase plan and handoff notes. **New session: read section 0 of that file first.**

**Next action (2026-10-28): Phase 8B code is built; the owner runs `exp001-validate` then `exp001-holdout` (see 'Phase 8B build notes' at the end). (Older: see 'START HERE FOR PHASE 8B'.) EXP-001 is LOCKED. Phase 8B (challengers and the one EXP-001 run) is next, only when the owner says go.** (Older notes follow.) **Next action:** Phase 6B is verified; Phase 7 only when the owner says go. (Older note follows.) **Next action:** wait for the owner. Phase 4 and the pre-Phase-5 pass are built. Phase 5 starts when the owner says go; its data source is frozen fixtures labelled `SAMPLE DATA — NOT LIVE` (owner, 2026-10-27). Open for the owner: (1) run the checks in "Pre-Phase-5 notes" on the Mac; (2) ~~X14 deviation~~ approved 2026-10-27; (3) ~~I15 numbers~~ provisional defaults kept; (4) first real OANDA practice run (issue 18, account access unconfirmed); (5) Phase 1 visual review and P8.

| Phase | Scope | Status |
|---|---|---|
| 0 | Scaffold, foundation docs, web app v0 on sample data | Done |
| 1 | Web: fix bands, Cmd+K, presets, replay, tests | Built 2026-10-26, all automated checks green. Awaiting owner visual review. See "Phase 1 notes" below |
| 2 | `core/` contracts, causality harness, ledger | Built 2026-10-26, all automated checks green. See "Phase 2 notes" below |
| 3 | `data/` OANDA practice client, resample, quality | Built 2026-10-26, owner re-ran the suite on Python 3.14 (176 passed, ruff clean). **Never run against the real OANDA API.** See "Phase 3 notes" below |
| 4 | `assistant/ta` causal adapters | Built 2026-10-27. Sandbox: 283 passed. **Owner's Mac (Intel, Python 3.14.3): 283 passed, 0 skipped, 2026-10-27.** `ruff` not yet run by the owner. See "Phase 4 notes" below |
| 4.5 | Pre-Phase-5 pass: P10 (X14), I10 approved, I15 definitions, issue 27 speed-up | Built 2026-10-27. Sandbox: 430 passed, ruff clean. **Not yet run on the owner's Mac.** See "Pre-Phase-5 notes" below |
| 5 | Premarket builder, API, connect web | Built (5A and 5B), see notes below |
| 6A | Paper simulator core (`assistant/paper`) | Built 2026-10-27. Sandbox: 12 new tests passed, ruff clean. Owner's Mac: 473 passed, ruff clean, live-mode refused. See "Phase 6A notes" |
| 6B | Risk gates, frozen rules, runner | Built 2026-10-27. Sandbox: 14 new tests (26 with 6A) passed, ruff clean. Owner's Mac: 487 passed, ruff clean, freeze hash and changed-rules refusal checked. See "Phase 6B notes" |
| 7 | Lab foundations and baselines | Built (7A and 7B), owner-verified, see notes below |
| 8A | **Done 2026-10-28: real data imported, EXP-001 approved and locked** (owner-run, Mac). See "EXP-001 lock" at the end |
| 8B | Lab challengers and EXP-001 run | **Code BUILT 2026-10-28, run NOT done.** See "Phase 8B build notes" at the end |
| 8 | EXP-001 run once: validation LOSS, holdout TIE. **Closed pending** (1) commit incl. `lab/experiments/EXP-001_records/` and (2) backend pytest, ruff and web checks (X16). Backlog items in plan section 5b | Closed, pending owner commit and checks |
| 8C | Phase 8 close-out: EXP-001 result recorded, web Lab EXP-001 tab, Forecast tab | **Built 2026-10-28.** Web: 81 tests passed, tsc, eslint and build clean in the sandbox; API 34 passed, ruff clean. Owner has not run it. See "Phase 8C notes" |
| 9A | `assistant/model`: labels, features, LightGBM, SHAP, scorer (no LLM) | Built and RUN on real data 2026-10-28. Holdout opened once: NULL (AUC 0.506). See 'Phase 9B fix and 9A result' |
| 9B | Suggestions engine, evidence links, Suggestions screen | Built. Screen bug (null `forecast_id`) fixed 2026-10-28; owner review of the screen still open |
| 9C | Analyst (LLM brief, debate) | Not started. Blocked on P6 |
| 10 | Review, hardening, docker | Not started |

## Phase 1 notes (2026-10-26)

Verified in the sandbox (`apps/web`): `npm run typecheck`, `npm run lint`, `npm test` (4 files, 46 tests) and `npm run build` all pass.

Not verified (no browser in the sandbox): how the chart looks after the level-label change, replay on the real chart, print layout of step 6, and the Playwright smoke test (`npm run e2e`, written but never run). The owner confirmed the session bands render (screenshot, dark mode).

Built: session-bands primitive; level-label primitive with de-collision (names in the pane, prices on the axis); sample levels separated to about 5 pips; Cmd/Ctrl+K palette (cmdk); layer presets and proximity ranking; inspector tabs (Insight, Evidence, Forecast placeholder); timeline from `known_at`; causal replay (bars, bands, objects); step 6 printable plan; zod contracts in `src/contracts/`; zustand store; ESLint, Vitest, Testing Library, Playwright config.

Deliberately not built:
- Instrument and timeframe switching in the palette: decisions P3 and P4 are still Proposed.
- TanStack Query: the plan says add it once the API exists (Phase 5).
- Click-to-zoom on an object (UI_DESIGN mentions it; not in the Phase 1 plan list).
- Radix primitives: not needed yet; tabs are hand-built with ARIA roles and arrow keys.

## Phase 2 notes (2026-10-26)

Verified in the sandbox (Python 3.12.3, fresh venv from `core/pyproject.toml`, exact pins):
- `pytest`: 115 passed (core 104, causality 11), about 1 second.
- `ruff check .`: all checks passed.
- `mypy --strict` on `core/src` with pandas and pyarrow stubs ignored: no issues in 17 files. mypy is a one-off check; it is not adopted or configured in the repo.
- `pip-audit` on the installed project dependencies: no findings (only the venv's own `pip` 24.0 was flagged).
- Mutation checks: eight deliberate breakages (harness ignoring value changes or `known_at`, ledger `verify` and tail check disabled, guard allowing `live`, ids accepting floats, `data_version` ignoring floats, optional evidence) were each caught by at least one test.
- One-off cross-language check: Python `to_wire()` output for all six contracts (96 fixture candles, optional fields omitted, ledger lines) parses with the zod schemas in `apps/web`. The throwaway test was not kept.
- Web app: only change is removal of the stray `apps/web/src/panels/__init__.py`. Re-run afterwards: typecheck, lint, 46 tests and build all pass.

Built: `sx_core.contracts` (six pydantic models, deterministic ids, `to_wire()`), `clock.py` (timeframes, `available_at`, `known_at_after_bars`, `is_known`, configurable sessions), `causality.py` (prefix-equality harness) plus pytest plugin (`assert_causal` fixture, registered in root `conftest.py`), `storage.py` (Parquet, content-based `data_version`), `ledger.py` (append-only JSONL, hash chain, `verify`), `labels.py`, `config.py` (paper-mode guard), frozen fixtures in `tests/fixtures/`.

Not verified:
- Python 3.11 (the declared minimum). Only 3.12.3 was available. Code uses 3.11 features only (`datetime.UTC`, `StrEnum`), but it has not been run on 3.11.
- macOS / Apple Silicon. The ledger uses `fcntl.flock`; behaviour under two concurrent processes was not tested (single-process only).
- Windows (the ledger lock is skipped there; not a target platform).

Deliberately not built:
- Market holidays and weekend close in `clock.py`. Gaps are detected from data in Phase 3.
- A permanent Python-to-zod agreement test. Today agreement is checked by hand once. A shared golden-fixture test on the web side would make it permanent; it touches web code, so it is left for you to approve.
- Web-side use of any of this. The web app still runs on sample data.

## Phase 3 notes (2026-10-26)

Decisions applied (owner, 2026-10-26): daily bars at 00:00 UTC (X10), EUR/USD (X11), M15/H1/H4/D (X12). The owner also proposed DST-aware London and New York sessions and an Asia/Colombo display timezone; recorded as P9 and **not built** (it changes Phase 2 `clock.py` and belongs with Phase 4 `sessions.py`).

Verified in the sandbox (Python 3.12.3, fresh venv, exact pins plus `httpx==0.28.1`):
- `pytest`: 176 passed (core 104, causality 11, data 61), about 7 seconds.
- `ruff check .`: all checks passed.
- `mypy --strict` on `core/src` and `data/src`: no issues in 28 files (one-off, not adopted).
- Python 3.11.17 one-off: the same 176 tests pass, but only with `numpy==2.4.6`; the pinned `numpy==2.5.4` does not install on 3.11 (known issue 19).
- `pip-audit` on installed packages: no findings (only the venv's own `pip` 24.0).
- Mutation checks: 21 deliberate breakages (forming bar emitted, bid/ask from the wrong bar, New York 17:00 daily alignment, high taken from close, incomplete source bars kept, duplicates allowed, weekend gap not recognised, stale check ignoring the closure, crossed quotes ignored, `includeFirst` always true, forming candle kept, live host allowed, token in an error message, H4/D fetch allowed, paper guard skipped, open taken from bid, microseconds dropped, incomplete bars cached, old bars winning a merge, instrument path traversal, rebuild building nothing) were each caught by at least one test. The first run missed "incomplete source bars kept"; a test was added and it is now caught.
- Web app (untouched): `npm ci`, typecheck, lint, 46 tests and build all pass.
- The resampler passes the Phase 2 prefix-equality harness (M15 from M1, H4 and D from H1), and a deliberately forward-looking resampler is caught by it.

Built: `data/pyproject.toml`; `sx_data` modules `errors`, `oanda_parse`, `oanda_rest`, `resample`, `quality`, `cache`, `pipeline`, `cli`; fixtures `tests/fixtures/oanda/eurusd_m1_oanda_shape.json` and `tests/fixtures/eurusd_h1_week.json` (both **synthetic**, seeded by `scripts/make_data_fixtures.py`, hash-pinned by a test); 61 tests in `data/tests/`.

Not verified:
- Anything against the real OANDA practice API. The sandbox has no route to it (the proxy answers 403) and no token was available. The request parameters, response shape, 5000-candle cap, `includeFirst` paging and rate-limit behaviour are from memory of OANDA's docs. The mock server in `data/tests/test_oanda_rest.py` encodes that memory, so passing tests prove the code matches the mock, not OANDA.
- Real-data quality: gap tolerance and the weekly closure window are assumptions.
- macOS / Apple Silicon.

Deliberately not built: `dukascopy.py` and `calendar_pilot.py` (optional later per the plan; left as empty placeholders), DST-aware sessions (P9), a market holiday calendar, incremental polling of the live feed.

To try it on real data (needs your practice token in `.env`): `python -m sx_data.cli sync --instrument EUR_USD --days 2`. It writes Parquet under `data/src/sx_data/cache/` (gitignored) and prints a `data_version` and a quality line per timeframe.

### Owner verification of Phase 3 (2026-10-26, from the owner's terminal)
- Python 3.14 in `.venv`; `python -m pip install -e "core[dev]" -e data` succeeded (httpx 0.28.1, httpcore 1.0.9, h11 0.16.0, anyio 4.15.1, idna 3.20, certifi 2026.10.23).
- `python -m pytest -q`: 176 passed in 10.04 s. `ruff check .`: all checks passed.
- `python -m sx_data.cli sync` refused to start with `TradingModeError ... got None` because `.env` did not exist yet. That is the paper-mode guard working. The owner then created `.env` from `.env.example`. The token step and the real-feed run are still pending.
- Small improvement to consider when next touching `cli.py`: print the `TradingModeError` as a one-line message instead of a traceback.

## Phase 4 notes (2026-10-27)

Owner answers: P9 approved (DST-aware sessions, Asia explicit, tests across UK/US clock-change weeks); real OANDA run skipped and kept outstanding; Python minimum raised to 3.12 with `numpy==2.5.4` kept.

Verified in the sandbox (Python 3.12.3, a **fresh venv** built from `pip install -e "core[dev]" -e data -e "assistant[dev,retro]"` plus `pip install --no-deps smartmoneyconcepts==0.0.27`, so without numba, exact pins):
- `pytest -q -rs`: **283 passed, 0 skipped** (176 earlier + 30 for DST sessions + 77 for `assistant/ta`), about 27 s.
- `ruff check .`: all checks passed.
- Web (`apps/web`, untouched): `npm run typecheck`, `lint`, `test` (4 files, 46 tests) and `build` all pass.
- `pip-audit`: nothing in the project's packages; only the venv's own `pip 24.0`.
- Mutation checks (break the code on purpose, expect a failing test): replay `known_at` one bar early, keep forced edge swings, session `known_at` at the window start, lifecycle using unclosed bars, London on fixed UTC (no DST): all five **caught**. Removing the ATR gate was **not** caught (redundant, issue 32).
- Hand-labelled day: the expected setups in `tests/fixtures/ta/labelled_day_expected.json` were derived by hand from the library definitions **before** the adapter was run, and then matched the output exactly (9 of 9). Fixtures are SYNTHETIC and hash-pinned.

Built:
- P9 / X13: `core/src/sx_core/local_sessions.py` (re-exported from `clock.py`), `LocalSessionConfig` with per-date DST conversion, overlap allowed, nonexistent and ambiguous local times raise, `utc_equivalent` to reproduce the old fixed sessions, `to_display_time` for Asia/Colombo. Tests cover the UK-only and US-only weeks in March and October/November 2026.
- Python 3.12: `requires-python` and ruff target; one ruff fix (PEP 695 generic in `clock.py`).
- `assistant/ta`: see section 3 of the plan. All SMC objects go through the replay wrapper; the library is **not** used with one call on the full series. A test shows that naive use is caught by the harness.
- Causality: the Phase 2 harness (every prefix) passes for sessions (two fixtures), the SMC adapter (labelled day, liquidity day, 40 random-looking bars), the candle adapter (fixed causal levels) and the whole `analyze_causal` pipeline (40 bars, non-vacuous). Trendlines are **expected to fail** the harness; a test asserts that, and that `require_causal` refuses them.

Not verified / not done:
- Nothing had run on the owner's Mac when this was written. The Mac is Intel; the first install failed on llvmlite and the packaging was changed (smartmoneyconcepts installed `--no-deps`, issue 25).
- Real data: none. All fixtures are synthetic (issue 26).
- Session hours, candle-pattern thresholds are my assumptions (I10, I15).
- The web app was not touched, so none of this shows on screen yet (Phase 5).
- No CI exists in the repo, so none was changed.

**Owner ran on the Mac (Intel, Python 3.14.3) 2026-10-27: 430 passed, 0 skipped (62 s); `ruff check .` clean; benchmark: 96 bars 0.42 s fast vs 1.76 s library (4.2x), 768 bars 9.5 s, `same` True.** Owner decisions after that: X14 approved with safeguards; I15 provisional defaults kept. Original instructions were:
1. `python -m pip install -e "core[dev]" -e data -e "assistant[dev,retro]"`
2. `python -m pip install --no-deps smartmoneyconcepts==0.0.27` (needed on an Intel Mac: numba/llvmlite cannot install there; verified in a fresh sandbox venv with no numba, 283 passed)
3. `pytest -q -rs` (expect 283 passed, no skips) and `ruff check .` (expect "All checks passed!").

### Owner verification of Phase 4 (2026-10-27, from the owner's terminal)
- Mac: Intel (x86_64), Python 3.14.3 in `.venv`, Node v22.21.1.
- First install attempt failed building `llvmlite` (no Intel-Mac wheel; needs LLVM). Fixed by installing `smartmoneyconcepts==0.0.27` with `--no-deps` (it never imports numba); see known issue 25.
- Second attempt: `pip install -e "core[dev]" -e data -e "assistant[dev,retro]"` then `pip install --no-deps smartmoneyconcepts==0.0.27` succeeded (TA-Lib 0.8.2 cp314 Intel wheel, trendln 0.1.18, scipy 1.18.1, scikit-image 0.26.0, matplotlib 3.11.2).
- `pytest -q -rs`: **283 passed in 33.67 s, no skips.**
- Not yet reported by the owner: `ruff check .`, the web checks, the Phase 1 visual review.
- Stray files cleaned up by the owner: an accidental `tmp/orig/` folder from a faulty first zip (removed); `spekrym-x-optimized.zip` sits in the repo root and should be moved out.

## Pre-Phase-5 notes (2026-10-27)

Owner decisions (2026-10-27): P10 approved (previous completed trading day; Monday uses Friday; weekends and holidays look back; incomplete days never used; limit on lookback; per-instrument calendar); I10 approved as strategy-defined windows; I15 definitions approved but numbers deferred; issue 27 handled as a separate prerequisite; Phase 5 uses frozen fixtures labelled `SAMPLE DATA — NOT LIVE`.

Verified in the sandbox (Python 3.13.17, fresh venv: `pip install -e "core[dev]" -e data -e "assistant[dev,retro]"` plus `pip install --no-deps smartmoneyconcepts==0.0.27`):
- Baseline before changes: 283 passed, ruff clean.
- After: `pytest -q -rs` **430 passed, 0 skipped** (62 s); `ruff check .` all checks passed.
- Python 3.12 (the declared minimum) was **not** available in the sandbox; Python 3.13 was used. The owner's Mac runs 3.14.3.
- Web app: untouched, **not re-run** in this pass.
- Mutation checks (break the code on purpose, expect a failing test): swing tie rule, BOS comparison, float32 level, BOS removal rule, FVG index (5 of 5 caught); fixed 21:00 close, weekends as trading days, incomplete day accepted, lookback ignored, last bar not required, known_at at midnight (6 of 6 caught); candle-metrics strict/inclusive on both comparisons, equal wicks, zero body, zero range (5 of 5 caught).

Built:
- **P10 / X14.** `sx_core.trading_calendar`: `TradingCalendar` (weekdays, Friday close in New York time converted per date, holidays), `FX_CALENDAR` registered for the seven majors, `calendar_for`, `reference_day`. `ta/sessions.py`: previous-day levels per complete trading day with `known_at` at the end of the trading window; `previous_day_levels(candles, on, calendar, max_lookback)`. Tests: Monday after a normal weekend, Tuesday to Friday, Saturday and Sunday dates, missing Friday bar, Friday missing its last pre-close bar, bars after the Friday close ignored, Sunday-evening stub ignored, incomplete midweek day, holiday not using the lookback, lookback limit, no data, the UK/US clock-change weeks (Friday close 21:00 or 22:00 UTC), unknown instrument, a Sunday-to-Thursday calendar, causality via the harness. Fixtures are generated by formula in the test file (each day has a distinct high), not stored.
- **I10.** No code change; a test now pins the approved defaults. `[start, end)`, overlap and clock-change tests already existed.
- **I15.** `ta/candle_metrics.py` (measurements, `CandleRules`, `is_doji`, `pin_bar`, `is_engulfing`; strict vs inclusive per rule; zero-range handled) with 19 boundary tests. Not wired into the pipeline. `candles_talib.py` only gained named default constants.
- **Issue 27.** `ta/smc_fast.py` plus `engine="fast"|"library"` in `smc_setups`. Output identical to the library path (91 oracle tests: every prefix of 16 random series with ties and swing lengths 1 to 3, fixtures, and the claim that adding a bar never changes older FVGs). Timings are in known issue 27.

Not verified / not done:
- Nothing ran on the owner's Mac or on Python 3.12.
- Timings are from the sandbox; the Mac will differ.
- Trading-calendar assumptions (17:00 New York close, no daily break, empty holiday list) are mine, not checked against OANDA's real schedule (no real data has ever been fetched, issue 18). `data/sx_data/quality.py` still uses its own closure window (Friday 20:00 to Sunday 23:00 UTC, issue 20); the two are not unified.
- Order blocks and liquidity still run through the library (the remaining replay cost).
- `candle_metrics` thresholds are unapproved defaults.

**Owner ran on the Mac (Intel, Python 3.14.3) 2026-10-27: 430 passed, 0 skipped (62 s); `ruff check .` clean; benchmark: 96 bars 0.42 s fast vs 1.76 s library (4.2x), 768 bars 9.5 s, `same` True.** Owner decisions after that: X14 approved with safeguards; I15 provisional defaults kept. Original instructions were: `python -m pytest -q -rs` (expect 430 passed, no skips), then `ruff check .` (expect "All checks passed!"), then optionally `python scripts/bench_smc_replay.py 96` to see your own timings.

## Phase 5A (2026-10-27): backend premarket + API (web untouched)

Built: `premarket/data_source.py` (interface + `FixtureSource`), `bias_checklist.py`, `builder.py`, `chart_payload.py`; `apps/api` (`create_app` factory, `/health`, `/premarket`, empty placeholders, CORS for Vite ports 5173-5175, paper-mode guard at startup); fixture `tests/fixtures/premarket/eurusd_m15_sample.json` made by `scripts/make_premarket_fixtures.py`; tests `assistant/tests/test_premarket.py` (12) and `apps/api/tests/test_api.py` (12); `apps/api/tests` added to pytest `testpaths`. Decisions I19 to I21; payload documented in CONTRACTS.md.

Run in the sandbox (Python 3.12.3, fresh venv): only the 24 new tests (all passed) and `ruff check .` (clean); a real `uvicorn` run answered `/health` and `/premarket` with the sample label. The FULL suite (430 + 24 expected = 454), the web checks and Python 3.14 on the owner's Mac were NOT run by me. A live-mode start refusal was covered by tests only (my manual attempt ran under the wrong interpreter, so it proved nothing).

Not verified / limits: fixture is synthetic, so the TA objects and checklist wording say nothing about real EUR/USD (issue 26). The payload has no zod mirror yet (5B). The weak spot: sessions on the fixture were not inspected visually. Build time for one payload was about 1 s here; the cache is per process.

Next: Phase 5B (web hookup, multi-timeframe strip, ATR distances, `report_plotly.py`). Wait for the owner.

### Owner verification of Phase 5A (2026-10-27, Mac, Intel, Python 3.14.3)
- `pytest -q -rs`: **454 passed** (70 s), 0 skipped; one warning (starlette says `httpx` in its test client is deprecated in favour of `httpx2`; not acted on).
- `ruff check .`: all checks passed.
- `uvicorn sx_api.main:create_app --factory --port 8000`: started; browser `GET /health` and `GET /premarket` both 200, sample label shown, `live:false`, `as_of` 2026-10-26T12:00:00Z, candles from 2026-10-23.
- `GET /` returns 404 (no route; expected). A small landing route is planned for 5B.
- `SX_TRADING_MODE=live` start: refused with `TradingModeError ... refusing to start` (the safety guard works on the owner's machine).
- Still not run by the owner: the web checks (the web app was not touched in 5A).

## Phase 5B (2026-10-27): web hookup, daily and H4 context, ATR distances, static brief

Built: web `Dataset` layer (`data/dataset.ts`, `fromApi.ts`, `DataProvider.tsx`), zod mirror `contracts/premarket.ts`, `api.ts` (fetch + validation), `layers/atr.ts`, `components/MtfStrip.tsx`; Workspace, Chart (remounted per dataset), Inspector (ATR distance, state, real setup id), SessionObjects, Timeline, ReplayBar, Stepper, CommandPalette, SessionPlan and App read the dataset; status banner and footer show the data label; `main.tsx` wraps the app in `QueryClientProvider` + `DataProvider`. Python: `premarket/report_plotly.py` (`build_figure`, `write_brief`), extra `assistant[report]`, API landing route `GET /`. Decisions I22 to I24.

Run in the sandbox (Python 3.12.3, Node from the sandbox): web `typecheck`, `lint`, `vitest` (7 files, **63 passed**: 46 before plus 17 new) and `build` all passed; Python: only the new tests (17 across `test_premarket_report.py` and `apps/api/tests`) passed and `ruff check .` clean. The FULL Python suite (expected 459 = 454 + 4 report + 1 root route), the Playwright smoke test and a real browser look at the screens were NOT run by me.

Not verified / limits: PNG and PDF export of the brief (needs Chrome; only the figure and HTML were tested). The chart was never rendered in a real browser (jsdom has no canvas; Chart is mocked in app tests), so how the API data looks on the chart (bands, label overlap, 12 levels) is unseen. ATR not cross-checked with TA-Lib. The API serves one fixed `as_of` (the newest bar), so the web has no as_of picker; replay works inside it. Other setup kinds are not drawn (issue 36). The bundle is 528 kB (Vite warns above 500 kB).

Next: owner review of the screens, then Phase 6 (paper trading) only when the owner says go.

### Owner run of Phase 5B (2026-10-27, Mac, Intel, Python 3.14.3)
- Web: `npm ci`, `typecheck`, `lint`, `test` (**63 passed**) and `build` all passed (chunk-size warning, 528 kB, expected).
- Static brief: `write_brief(..., 'brief.png')` worked on the Mac (Chrome present); the PNG shows the title, the `SAMPLE DATA — NOT LIVE` label, session bands, dashed levels, the D/H4 facts and the disclaimer. The level text labels could not be read in the owner's screenshot (zoomed out); unconfirmed.
- API start failed once with `TradingModeError ... (got None)`: the command was run from `apps/`, and the factory looked for `.env` only in the working directory. Fixed after this run: `sx_api.main.find_dotenv` searches the working directory and its parents (two tests added).
- `ruff check .` printed 70 findings (import order, RUF100, RUF007, RUF022, PYI034) in files from earlier phases. These rules are not in the repo's configured rule set, so the command may have used another config or another ruff; cause not yet established (the top of the output was cut off).
- Not yet reported: full `pytest` (459 expected), API + web together in the browser, the offline-fallback banner, Playwright.

### Housekeeping (2026-10-27): ruff config restored
- Owner ran the full suite on the Mac: **461 passed**, 0 skipped (2 more than the 459 expected: the `find_dotenv` tests).
- `ruff check .` printed 70 findings because the repo-root `pyproject.toml` was absent (also `README`, `Makefile`; same in two zips). Cause confirmed by reproducing the 70 findings in the sandbox with ruff 0.17.2 and no config.
- Reconstructed root `pyproject.toml` (decision I25). With it, `ruff check .` in the sandbox: **All checks passed**. Full pytest was not re-run by me (config only sets testpaths); owner to run it.
- Still missing and not recreated: root `README` and `Makefile`. Web checks, browser look and Playwright still unreported by the owner.

## Phase 6A notes (2026-10-27)

Owner confirmed before this: 461 passed, ruff clean with the restored config, web typecheck, lint, 63 tests and build all green. Phase 6 was split into 6A and 6B (X15).

Built: `paper/broker.py`, `orders.py`, `sim_broker.py`, `tracker.py`, `replay.py`; fixture `tests/fixtures/paper/scripted_day.json` (synthetic, expectations computed by hand: A long target +14.8, B short target +9.9, C never fills, D long stop -8.4); `assistant/tests/test_paper_sim.py` (12 tests). Decisions X15, I26 to I28. No contract change.

Run by me (owner asked me not to spend effort on test runs): only the 12 new tests (passed, in a venv with `core` installed and `assistant/src` on the path) and `ruff check .` (clean). The full suite (473 expected), Python 3.14 on your Mac and the web app were not run by me; the web app was not touched.

Not verified / limits: see known issue 38. Fill rules are my assumptions (I26), not a model of any real broker. Nothing has used this against real quotes.

### Owner verification of Phase 6A (2026-10-27, Mac, Intel, Python 3.14.3)
- `pytest -q assistant/tests/test_paper_sim.py`: 12 passed. Full `pytest -q`: **473 passed**, 1 warning (starlette/`httpx`), 67 s. `ruff check .`: all checks passed.
- `SX_TRADING_MODE=live` with `SimBroker()`: refused with `TradingModeError ... refusing to start`.
- Not run by the owner: web app (untouched in 6A). Next: Phase 6B only when the owner says go.

## Phase 6B notes (2026-10-27)

Built: `suggestions/risk_gates.py` (news blackout, max open trades, daily-loss halt), `rules/ruleset.py` (rule set, hash, lock, freeze CLI), `rules/frozen/paper_v1.json` plus its `.lock`, `paper/runner.py` (`PaperRunner`); `assistant/tests/test_paper_runner.py` (14 tests). Decisions I29 to I31. No contract change. The OANDA practice backend was not built (account access unconfirmed).

Run by me (owner asked me not to spend effort on test runs): the 14 new tests plus the 12 from 6A (26 passed, venv with `core` only and `assistant/src` on the path) and `ruff check .` (clean). The first run of the new tests found a bug in one of my own tests (a fill I expected to stay pending); fixed. The full suite (487 expected), Python 3.14 on the Mac and the web app were not run by me; the web app was not touched.

Not verified / limits: see known issue 39. Gates only ever saw synthetic quotes.

To freeze a new rule file: `python -m sx_assistant.rules.ruleset freeze <file>`; the shipped lock was made that way.

### Owner verification of Phase 6B (2026-10-27, Mac, Intel, Python 3.14.3)
- `pytest -q` on the two paper test files: 26 passed. Full `pytest -q`: **487 passed**, 1 warning (starlette/`httpx`), 75 s. `ruff check .`: all checks passed.
- `python -m sx_assistant.rules.ruleset freeze ...paper_v1.json` printed `d68cfd76737f9ddf151c0a53e8ba44af3ae8b09f66f3aaa762e7752687ceae58`, matching the shipped lock.
- A copy of the rules with `max_open_trades` changed to 9: `PaperRunner` refused with `RulesError: rules changed since they were frozen; refusing to run`.
- Not run by the owner: web app (untouched). Phase 6 (6A and 6B) is complete on the simulator; OANDA practice backend still not built. Next: Phase 7 only when the owner says go.

## Chart zone pass (2026-10-27): FVG, order blocks, BOS/CHoCH drawn

Built (web only; no Python or API change): `components/zonesPrimitive.ts` (new series primitive), `Chart.tsx` (zones effect, replay clipping), `data/fromApi.ts` (maps `fvg`, `order_block`, `bos`, `choch` to objects with extent, tag, orientation), `data/sample.ts` (Obj type), `layers/presets.ts` + `visibility.ts` (separate zone cap), `layers/timeline.ts` (own entry per zone), `SessionObjects.tsx` (scrollable list, updated note), `Inspector.tsx` (zone price range, real kind). Tests in `data/fromApi.test.ts`. Decisions I32, I33.

Run by me (Node in the sandbox, after `npm ci`): `typecheck`, `lint`, `vitest` (7 files, **66 passed**: 63 before plus 3 new, one rewritten) and `build` all passed. The Python suite was not touched or run.

Not verified: how it looks. jsdom has no canvas, so the primitive's drawing was never rendered by me or by a test; box and line placement, tag overlap and the faded look need your eyes. Playwright not run. Limits: see known issue 36.

### Chart zone pass: owner's first browser look (2026-10-27) and fix
- Owner ran the zip: web `typecheck`, `lint`, 66 tests and `build` passed on the Mac; API and web ran together (`GET /premarket` 200).
- Screenshot (Premarket, step 3) showed a **bug of mine**: I gave every FVG and order block its own timeline entry, so about 50 buttons filled the middle of the page and the chart was pushed off the screen. My tests could not see this (jsdom has no layout). Fixed (I34): zones are off the timeline, BOS/CHoCH stay, and the timeline scrolls in a short box. After the fix: typecheck, lint, 66 tests and build pass in the sandbox. **Not yet seen again in a browser; the chart and zones themselves have still not been seen by anyone.**
- Also visible in the screenshot: the objects panel hides 3 of 6 session levels under the Premarket preset ("not drawn: preset"), as designed.


## Phase 7A notes (2026-10-27): Lab foundations, part 1

Phase 7 is split (owner request, 2026-10-27). **7A (this build):** partition with governed holdout, causal features and target, metrics, naive baselines, one frozen synthetic fixture. **7B (next, only when the owner says go):** HAR, GARCH (`arch`), negative controls, purged-CV cross-check, Optuna search with every trial in the ledger, `sx-lab` CLI, `Forecast` JSON records.

Built: `lab/pyproject.toml` (was empty), `sx_lab/partition.py`, `features/volatility.py`, `features/dataset.py`, `evaluation/metrics.py` (QLIKE, RMSE, interval coverage), `baselines/{base,naive}.py` (persistence, historical mean), `scripts/make_lab_fixtures.py`, fixture `tests/fixtures/lab/eurusd_h1_synth_1000.json` (SYNTHETIC GARCH, hash-pinned), 24 tests in `lab/tests/`. Decisions L1 to L4 (see `docs/DECISIONS.md` appendix).

Run by me (owner asked me not to spend effort on test runs): only the 24 new Lab tests (24 passed) and `ruff check` on the new files (one E501 found and fixed afterwards; that edit was not re-run by me), in a fresh venv with Python 3.12.3, pandas 3.0.2, numpy 2.4.4 (the repo pins pandas 3.1.0 and numpy 2.5.4; not installed here). The FULL suite, Python 3.14 on the Mac and the web app were NOT run by me; the web app was not touched.

Not verified / limits: see Lab known issues L-1 to L-7 in `docs/DEVELOPMENT_PLAN.md` (appended). No baseline has been scored on real data; no ranking of baselines is claimed.

Owner commands are in the delivery message. Next: Phase 7B only when the owner says go.

## Phase 7B notes (2026-10-27): Lab foundations, part 2

Built: `baselines/har.py` (OLS HAR-style), `baselines/garch.py` (`arch` used to ESTIMATE only; our own recursion forecasts), `evaluation/negative_controls.py` (shuffled labels, leaked-feature guard), `evaluation/purged_cv_crosscheck.py`, `search/optuna_search.py` (every trial logged to the ledger as `lab.trial`), `records.py` (contract `Forecast` records), `cli.py` (`python -m sx_lab.cli run | evaluate | search | report`, also `sx-lab` after `pip install -e lab`). Pins added to `lab/pyproject.toml`: `arch==8.0.0`, `optuna==5.0.0`. 17 new tests (41 Lab tests in total). Decisions L5 to L9.

Run by me (owner asked me not to spend effort on test runs): `pytest lab/tests` **41 passed** and `ruff check lab` clean, in a fresh venv with Python 3.12.3 and the repo's own pins (pandas 3.1.0, numpy 2.5.4), plus `pip-audit` (nothing except the venv's own `pip` 24.0) and one `evaluate` run of the CLI on the synthetic fixture. The FULL suite, Python 3.14 on the Mac and the web app were NOT run by me; the web app was not touched. No mutation checks this time.

What the one `evaluate` run showed (SYNTHETIC data, 147 validation rows, no ranking claimed): validation QLIKE historical_mean 0.101, persistence 0.195, har 0.105, garch11 0.091. The purged CV cross-check ordered the models differently (har best, then persistence, garch11, historical_mean), so the single-split ranking is not stable. The shuffled-label control FAILED for HAR (the label-shuffled fit was not worse), meaning HAR shows no measurable skill over a constant on that split; the leak guard PASSED (flagged only the planted leak).

Not verified / limits: see Lab known issues L-8 to L-15 in `docs/DEVELOPMENT_PLAN.md` (appended). Nothing has run on real data. I checked `arch` behaviour by cross-test (our GARCH recursion equals `arch`'s own forecast to 1e-6) and read the source only for `convergence_flag`; I did not read all of `arch` or `optuna`.

Phase 7 "done when" is only partly met: baselines run and the negative controls and variants count work, but not on real data (issues 18, 24). Next: Phase 8 only when the owner says go.

### Fix after the owner's run of 7B (2026-10-27, Mac, Intel, Python 3.14.3)
- Owner ran: `pip install -e lab` ok; `pytest lab/tests` **41 passed** (60 s); `ruff check .` clean; `evaluate`, `search` (12 trials, 6 distinct) and `report` ran and matched the sandbox numbers (validation QLIKE historical_mean 0.10148, persistence 0.19501, har 0.10507, garch11 0.09123; purged CV order differs from validation order; shuffled-label control FAIL, leak guard PASS).
- Full `pytest -q` FAILED at collection: `assistant/tests/test_ta_candles_talib.py` and `test_ta_normalize.py` did `from conftest import D0` and got `lab/tests/conftest.py` (pytest imports every `conftest.py` as the top-level module `conftest`). My bug, from adding a conftest in 7A.
- Fix: `lab/tests/conftest.py` deleted; fixtures moved to `lab/tests/lab_fixtures.py` and registered under private names imported by each test module. Sandbox after the fix: `pytest lab/tests` 41 passed, `ruff check lab` clean, and collecting the two failing assistant files together with `lab/tests` no longer fails on `from conftest import D0` (it stops later only because the sandbox venv lacks `sx_assistant`). The full suite is NOT re-run by me.
- Lesson for later phases: never add a `conftest.py` under a new test folder in this repo; use a uniquely named helper module.

## Phase 8 split (2026-10-27, docs only)

Phase 8 is divided into **8A** (conformal intervals, model confidence set, regime tools, real-data path and gap policy, lock/open-holdout CLI, frozen EXP-001 spec, PyTorch feasibility spike) and **8B** (minimamba and other challengers, one EXP-001 run, results document, web Lab screen and Forecast tab). Details in `docs/DEVELOPMENT_PLAN.md` (appended section) and decisions L10 to L12. No code was written or run in this step. **Next action:** owner answers the four questions in the plan, then says "go 8A". Phase 8B only after 8A is verified and the spec is locked.

## Phase 8A feasibility result: PyTorch on the owner's Mac (2026-10-27)

- Owner ran on the Mac (Intel x86_64, Python 3.14.3, `.venv`): `python -m pip install torch --dry-run` → `Could not find a version that satisfies the requirement torch (from versions: none)`. **PyTorch cannot be installed in the project venv.**
- Claude checked PyPI metadata from the sandbox (2026-10-27): torch 2.14.1 is the latest; releases 2.12.0 to 2.14.1 publish macOS wheels for Python 3.12 to 3.14 but **none for Intel macOS** (no x86_64 or universal2 wheels). The newest release with an Intel-Mac wheel is **2.2.2**, built for Python 3.8 to 3.12 only.
- Consequence: on this Mac, torch would need Python 3.12 and 2.2.2, which was built before numpy 2 and conflicts with the repo's pins (numpy 2.5.4, pandas 3.1.0). I did NOT test whether torch 2.2.2 plus numpy 1.x runs at all, nor whether `minimamba` works with it. Running the challengers locally is therefore not recommended.
- Not verified: that `minimamba` itself installs and runs anywhere; that the sandbox has enough CPU time for EXP-001.

## Phase 8A feasibility spike: result (2026-10-27)

Question: can the neural challenger run on the owner's machine (Intel x86_64 Mac, macOS 15.7.9)?

| Check | Result |
|---|---|
| `pip install torch` in the project `.venv` (Python 3.14.3) | Fails: no matching distribution. PyTorch stopped publishing macOS x86 wheels after 2.2.x. |
| conda-forge `osx-64` | Provides `pytorch-2.14.1-cpu_mkl_py314`. Dry run and install succeeded. |
| Environment | Miniforge env `spekrym-torch`: Python 3.14.10, torch 2.14.1, numpy 2.5.4 (matches the repo's numpy pin), 4 threads. |
| minimamba | 1.0.1 installs from PyPI without replacing torch or numpy; `pip check` clean; imports. |
| Usable class | `MambaForFeatureExtraction(BaseMambaConfig)`; forward takes `(batch, seq, d_model)` float tensor. Set `use_fast_path=False`. |
| Speed (CPU, training step) | d=64, 2 layers: about 1,260 tokens/s at seq 256; 2,100 to 3,000 tokens/s at seq 24 to 64. Batch size barely changes tokens/s. d=128, 4 layers, seq 512 did not finish one step in several minutes. |

Conclusions:
- The Mac can run a tiny minimamba (smoke tests, small runs). It cannot run larger configs or a search-heavy protocol in practical time.
- Cost scales with tokens processed, so the frozen spec should fix a small model and short context if the Mac is to be used.
- conda-forge may stop building Intel-Mac packages; pin exact versions and record hashes.
- The repo's dependency set was not installed into this environment. Compatibility with the repo's pins (pandas 3.1.0 and the lab packages) is untested.

Housekeeping: baseline commit `2e509be` ("Baseline snapshot before Phase 8"), 295 files; `spekrym-x-optimized.zip` excluded via `.gitignore`.

Not yet verified: the repo's full-suite result after the 7B fix (expected 528 passed); `lab/experiments/EXP-001_mamba_vs_har.md` and `lab/src/sx_lab/models/minimamba_vol.py` were empty when checked.

## Phase 8A build notes (2026-10-27)

Built (Python only; web, API and paper untouched): `lab/features/gaps.py` (gap policy, closes L-2 on synthetic evidence), `data/sx_data/importer.py` (CSV/Parquet import with quality checks and a provenance sidecar), `lab/calibration/conformal.py`, `lab/evaluation/model_confidence_set.py`, `lab/regime/markov_switching.py`, `lab/regime/changepoints_offline.py`, `lab/spec.py`, `lab/cli_experiment.py` (`sx-lab import | spec-hash | lock | open-holdout`), `lab/experiments/prereg/EXP-001.yaml` (DRAFT). Changed: `lab/cli.py` (gap-aware dataset everywhere, conformal band in `run`, new commands), `lab/records.py` (optional `conformal`), `lab/pyproject.toml` (statsmodels 0.15.0, ruptures 1.1.10, pyyaml 6.0.3). Decisions L16 to L20. Tests added: 27 (`lab/tests/test_gaps.py`, `test_conformal_mcs.py`, `test_regime.py`, `test_spec_lock.py`, `data/tests/test_importer.py`).

Run by me (sandbox, Linux x86_64, Python 3.12.3, pandas 3.1.0, numpy 2.5.4): `pytest lab/tests data/tests` **130 passed**; `ruff check .` clean; full `pytest -q`: **544 passed, 1 failed, 2 skipped**. The failure is `core/tests/test_config.py::test_repo_env_example_is_paper_and_loads`: the zip has no `.env.example` (not caused by 8A). The skips are the optional plotly and trendln extras, not installed in my venv. `sx-lab evaluate` on the synthetic fixture reproduces the owner's 7B numbers (historical_mean 0.10148, persistence 0.19501, har 0.10507, garch11 0.09123). `pip-audit` was not run on the new packages. Web checks were not run (not touched).

Phase 8A "done when" status: (1) spec locked: **NO** (draft; needs real data and owner approval); (2) conformal and MCS tests pass: yes; (3) real-data path loads a quality-checked dataset: **only on a fixture-derived CSV**, no real file has been imported; (4) feasibility spike recorded: yes (see above). 8B must not start until (1) and (3) are met.

Owner actions to finish 8A: supply a real EUR/USD H1 file (or say which provider route); run `sx-lab import`; read the quality line; review and edit every value in `EXP-001.yaml` (PROPOSED items especially); fill `data.*` from the provenance sidecar; set `status: approved` and the approval block; run `sx-lab lock`.

Housekeeping done: removed a duplicated "8A feasibility spike" section here and a duplicated "Phase 8A answers" block in `DECISIONS.md` (byte-identical copies). `docs/phase8/*.md` still exist as the sources of those notes.

### Fix after the owner's install of 8A (2026-10-27, Mac, Intel, Python 3.14.3)
- Owner ran the zip; `pip install -e lab` FAILED: `ruptures==1.1.10` requires Python < 3.14. My sandbox is 3.12, so I never saw it (I had listed it as unverified, 8A-9). Fix: ruptures removed from required dependencies (optional extra `crosscheck`), `changepoints_offline.py` now has an in-house exact PELT. Sandbox after the fix: `pytest lab/tests/test_regime.py` 6 passed (4.5 s), `ruff check lab` clean. Owner still to run the full suite and the commands in the delivery message.
- Also seen in the owner's terminal: the commit "Before 8A" added `spekrym-x-complete-20261027-145858.zip` (a copy of the repo) to git. Not harmful but it bloats the repo; consider `git rm --cached` on it and adding `*.zip` to `.gitignore`.

## Owner verification and import upgrade (2026-10-28)
- Owner's Mac (Intel, Python 3.14.3), after the 8A zip and fix1: full `pytest -q` **556 passed, 1 skipped** (152 s), `ruff check .` clean, `pip install -e lab` works (statsmodels 0.15.0, pyyaml 6.0.3 satisfied). The skip is the ruptures cross-check (Python < 3.14).
- Data plan: the owner chose the Dukascopy "Historical Data Export" (seen in screenshot: Period 1 Minute/Hour, Timezone UTC, Offer side Bid, EUR/USD). HistData.com only offers M1 and ticks (fixed UTC-5 per third-party descriptions; its own spec page not read), so it needs a resampler that does not exist. Plan: Dukascopy H1, UTC, Bid, about 4 to 5 years, saved OUTSIDE the repo (licence terms not read).
- Phase 8B is paused (owner decision) until real data is imported and EXP-001 is approved and locked.
- Built: `data/sx_data/import_formats.py` (case-insensitive column aliases; time format detected only when exactly ONE candidate format parses every row, else refused, or `--time-format`); `importer.py` now accepts several files (identical overlapping rows dropped, conflicting rows refuse), records `files`, `bars_per_year`, `flat_bars`, `longest_flat_run`; `sx-lab import --source-file F [F ...] --time-format ...` prints a clear REFUSED message instead of a traceback. Sandbox: `pytest lab/tests data/tests` 135 passed, `ruff check .` clean. NOT run on any real file: the alias list and candidate formats are common layouts, not a verified Dukascopy format.
- Removed in this change (was never used by the CLI): the importer no longer reads optional `bid_close`, `ask_close` or `complete` columns.
- Parked idea (owner): Dukascopy embeddable widgets (chart, market summary, economic calendar, market depth, sentiment, and so on). Not planned for any phase. Caveats to settle first: they are third-party scripts/iframes (conflicts with the adapter and CSP rules), their data is not ours (cannot feed Forecast, ledger or paper fills), terms of use unread, and they must carry the honesty labels. A better fit may be our own economic-calendar and sentiment features later.

## OANDA history download (2026-10-28)
- Owner reported Dukascopy's export does not work properly and supplied OANDA practice credentials (account exists, so the Sri Lanka question, issue 24, is probably settled for the practice account; not confirmed by any API call yet). The credentials were pasted into the chat: owner should regenerate the practice token in the OANDA portal. Nothing secret is stored in the repo, docs or zips.
- Env names the CODE reads: `OANDA_TOKEN`, `OANDA_ENV` (must be `practice`), `OANDA_ACCOUNT_ID` (not needed for candles), plus `SX_TRADING_MODE=paper`. `OANDA_API_TOKEN` and `DATA_SOURCE` are NOT read anywhere. Verified in the sandbox: a file with only `OANDA_API_TOKEN` gives "OANDA_TOKEN is empty".
- Built: `data/sx_data/history.py` and the command `python -m sx_data.cli history --start YYYY-MM-DD --end YYYY-MM-DD --out FILE.parquet [--tf H1] [--instrument EUR_USD]`. It uses the existing `OandaClient.fetch_candles` (paging 5000 per request, retries, 0.05 s spacing, practice host only), runs the quality check, writes Parquet plus the same provenance sidecar as the file importer (label `OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED`, `verified: false`, price basis mid with bid/ask closes kept). The importer and history share `build_provenance` and `finalize_dataset` in `importer.py`.
- Sandbox: `pytest data/tests lab/tests` 137 passed, `ruff check .` clean. NOT verified: any real OANDA response (no network route from the sandbox; only a connection error was seen). The client was written from OANDA's documented v20 candles shape and has never run live; how far back practice H1 history goes, and the per-request cap of 5000, are unconfirmed.
- Dukascopy and HistData routes are dropped for now (the Dukascopy importer upgrades from earlier today remain and are harmless).


## Fix: .env paper-mode value not reaching OandaClient (2026-10-28)
- Owner's `sx_data.cli history` run failed with `SX_TRADING_MODE must be exactly 'paper' (got None)`. Cause (found by reading code): `load_settings` merges `.env` and passes the guard, but `OandaClient.__init__` calls `enforce_paper_mode(None)`, which reads only `os.environ`, so values that live only in `.env` were invisible. Fix: `cli.py` passes `env=_guard_env(settings)` to `OandaClient` in both `sync` and `history`. The guard is not weakened: the values still must be exactly `paper` and `practice`.
- Not run by me (owner asked for no test runs; only `py_compile` on `cli.py`). Owner commands are in the delivery message.
- Phase numbering note: the plan's "Phase 8A/8B" is current. The session-bands bug (known issue 1) was fixed in Phase 1 and is not open.

## Fix: silent early stop in OANDA history, and holiday gaps (2026-10-28)
- Owner's run for 2024-10-01 .. 2026-10-27 returned **9,999 bars ending 2026-05-12** (5 months short) with no warning. Likely cause (hypothesis, NOT confirmed against the live API): `OandaClient.fetch_candles` stopped on any page shorter than `page_size`, and a follow-up page (`includeFirst=false`) probably came back one candle short (5,000 + 4,999 = 9,999). Fix: a short page no longer ends the download; it stops only at `end` or when a page adds no new closed bar (costs one extra empty request). Regression test added.
- New guard `history._check_coverage`: refuses a download whose last bar is more than 5 days before min(end, now) ("download stopped early") or whose first bar is more than 5 days after `start` ("history starts late"). A truncated download can no longer pass silently.
- Real OANDA practice H1 showed 4 unexpected gaps over 2 years: Dec 24 21:00 -> Dec 25 22:00 and Dec 31 21:00 -> Jan 1 22:00, in both 2024-25 and 2025-26. `GapRules.holiday_closures` (default True) now treats Dec 25 and Jan 1 closure windows as expected. Assumption: only these two; Good Friday and others stay unexpected until seen.
- Sandbox (Linux, Python 3.12): `pytest data/tests lab/tests` 140 passed, 1 skipped (ruptures); `ruff check data lab` was clean except one E501 fixed afterwards (not re-run). Full suite and the Mac not run. Still not verified: the live API behaviour above.
- Note for locked specs: the gap rules changed, so a dataset's quality verdict can differ from before this change. Record `data_version` and the rules version when locking EXP-001.

## Lab data import dashboard (2026-10-28)
Owner request: a dashboard widget to download different data without the terminal. Built (not a numbered phase; Phase 8B stays paused):
- API: `apps/api/src/sx_api/datasets.py` (request rules, file naming, listing), `jobs.py` (one background import at a time, in memory), `routes/datasets.py` (`GET /lab/datasets`, `POST /lab/datasets/oanda`, `GET /lab/datasets/jobs/{id}`), `main.py` (CORS now allows POST; `create_app(client_factory=, data_dir=)`). The `/lab` placeholder is unchanged.
- Web: `screens/LabScreen.tsx` (Lab nav item), `components/lab/ImportWidget.tsx`, `DatasetTable.tsx`, `lab/importForm.ts` (pure helpers), `labApi.ts`, `contracts/datasets.ts` (zod, mirrors the API by hand).
- Rules: token stays on the server and is never returned; the browser chooses no path (file name built from validated fields, inside `lab/outputs/data`); instruments limited to 7 majors; timeframes M5, M15, M30, H1 (H4/D come from resample); at most about 250,000 bars; an existing file is never overwritten (409); the download goes through `fetch_history`, so the coverage check, quality check and provenance label apply; a refused or failed job saves nothing; error messages never include the token (tested). Paper guard unchanged.
- Run by me (sandbox): API `pytest apps/api/tests` 31 passed (11 new), `ruff check apps/api` clean; web `typecheck`, `lint`, `vitest` (8 files, 73 passed, 7 new) and `build` passed. The page was rendered once in Chromium against the real API with a seeded dataset (dark and light looked right; a table layout fix was applied after that and not re-screenshotted). NOT run: a real download through the widget (no route to OANDA from the sandbox), the full Python suite, the Mac.
- Limits: no progress bar (the OANDA client has no progress hook; shows elapsed time only); finished jobs are forgotten when the API restarts; no delete button (delete files by hand); no CSV/file upload yet; the zod contract and the API agree by hand only. The top bar and footer still show the Premarket sample labels on the Lab screen (existing behaviour).

## EXP-001 lock (2026-10-28)
Run by the owner on the Mac (Intel, Python 3.14.3). Not run by me: the data and ledger live only on the owner's machine.
- Data: `lab/outputs/data/eurusd_h1.parquet` (+ `.provenance.json`), OANDA practice H1, mid price, label `OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED`. 12,864 bars, 2024-10-01T00:00 to 2026-10-26T23:00 UTC; gaps 112 expected, 0 unexpected, not degraded; 0 flat bars. Any EXP-001 result is on this practice feed only. Whether the data file may be committed or shared is unchecked (OANDA terms not read): keep it out of git for now.
- Spec: `lab/experiments/prereg/EXP-001.yaml`, `status: approved`, approved by "Panda" on 2026-10-28. Data fields were filled by `scripts/exp001_prepare.py` from the sidecar. Two pre-lock edits were applied with `scripts/exp001_edits.py`: an `inconclusive` outcome rule (covers the case where only a reference model is in the model confidence set) and fixed seeds 1, 2, 3 in `stopping_rule`.
- Lock: `sx-lab lock` printed `EXP-001 locked: spec 7a541633a9161018 holdout locked | LabPartition(train=7564, validation=2498, holdout=sealed:2498, embargo=24)`. Full spec sha256: `7a541633a9161018c7f46aa80a5664293e26193c06e4439f27a542ffb7dca33c`. The lock is recorded in `lab/outputs/ledger.jsonl` (owner's machine): do not delete or edit it. Any change to the YAML is a new experiment (EXP-002).
- All values marked PROPOSED in the spec (MCS reps/block/seed, conformal alpha 0.2, max_variants 20, MiniMamba size, gap policy `trading_time_windows_v1`) were accepted by the owner as written. Gap rules at lock time: holiday closures only for Dec 25 and Jan 1; other holidays (for example Good Friday) would show as unexpected gaps, none occurred in this window.
- Before 8B: (1) full `pytest -q` and `ruff check .` were last run on the Mac before the history fixes and the Lab import dashboard; rerun. (2) MiniMamba needs torch from conda-forge (Intel Mac has no PyPI wheel); the spec says run on Linux first (L13), and the Mac only handles tiny runs, so decide where the run happens. (3) The holdout stays sealed; `open-holdout` needs `--reason` and `--confirm-spend-holdout` and works once. (4) The OANDA practice token was pasted in an earlier chat and should be regenerated. (5) `lab/experiments/EXP-001_mamba_vs_har.md` is still empty.
- Test fix after the lock (2026-10-28): three tests in `lab/tests/test_spec_lock.py` used the real `EXP-001.yaml` as their "draft" example and failed once it was approved (3 failed, 579 passed). They now use the frozen draft `tests/fixtures/lab/exp_draft_spec.yaml`. Owner's Mac afterwards: full `pytest -q` **582 passed, 1 skipped**. `ruff check .` flagged 3 long lines in `scripts/exp001_edits.py` and `scripts/exp001_prepare.py` (fixed afterwards; ruff not re-run by me).

## START HERE FOR PHASE 8B (handoff written 2026-10-28)

**State:** EXP-001 is APPROVED and LOCKED (spec sha256 `7a541633a9161018c7f46aa80a5664293e26193c06e4439f27a542ffb7dca33c`, ledger `lab/outputs/ledger.jsonl` on the owner's Mac). Data: `lab/outputs/data/eurusd_h1.parquet` plus `.provenance.json` (OANDA practice, H1, mid price, 12,864 bars, 2024-10-01T00:00Z to 2026-10-26T23:00Z, label `OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED`). Split: train 7,564, validation 2,498, holdout 2,498 sealed, embargo 24. Owner's Mac last verified 2026-10-28: full `pytest -q` 582 passed, 1 skipped; `ruff check .` clean. **The data file and ledger live only on the owner's Mac, not in any zip.**

**What 8B must do (plan "Phase 8B" + the locked spec):** build `lab/src/sx_lab/models/minimamba_vol.py` (currently EMPTY, as are `nf_baselines.py`, `chronos_zeroshot.py`, `mamba_ssm_vol.py`, and `lab/experiments/EXP-001_mamba_vs_har.md`); a runner that refuses to start if the spec hash differs from the lock, the data label matches sample/synthetic/not live (L11), the data_version differs, or the holdout is already open; train MiniMamba once per seed 1, 2, 3 on TRAIN, score on VALIDATION; score historical_mean, persistence, HAR, GARCH(1,1) the same way; model confidence set (level 0.10, reps 1000, block 24, method R, seed 20261027); conformal band (alpha 0.2, calibrated on the first half of validation); every trial and seed to the ledger (cap `max_variants` 20); then open the holdout exactly once (`sx-lab open-holdout --reason ... --confirm-spend-holdout`) and write `EXP-001_mamba_vs_har.md` with MCS, coverage, variants tried, labels `Exploratory`, `Not validated`, `Retrospective`. Outcome rules in the spec: win / tie / loss / inconclusive. A tie or loss is a valid result. Optional web Lab/Forecast tab work comes last.

**Locked spec facts for the model:** `d_model 64, n_layer 2, context_bars 48, use_fast_path false`; pins `minimamba==1.0.1`, `torch==2.14.1 (conda-forge)`, `arch==8.0.0`; horizon 24 bars; windows [3, 6, 12, 24, 72, 120]; gap policy `trading_time_windows_v1` (L16); primary metric QLIKE, secondary RMSE and interval coverage. Do NOT edit `EXP-001.yaml` (any change = EXP-002).

**Interfaces to reuse:** `Baseline` protocol in `lab/src/sx_lab/baselines/base.py` (`name`, `fit(train)`, `predict(frame)`; predict never reads `target`); `LabPartition` (`partition.py`: `.train`, `.validation`, `lock_evaluation`, `open_holdout(ledger, spec_hash, reason)`); `features/gaps.py::make_gap_aware_dataset`; `records.py::make_forecasts(model, baseline, train, val, ..., conformal=)`; `evaluation/metrics.py`, `model_confidence_set.py`, `calibration/conformal.py`; `cli_experiment.py::_verified` (checks spec, data_version, label); spec loader `spec.py::load_spec`.

**OPEN DECISION (ask the owner first): where does MiniMamba train?** (1) the Claude sandbox, Linux: not measured, needs a CPU-time check before building; (2) the owner's Mac via the conda-forge env `spekrym-torch` (Python 3.14.10, torch 2.14.1, numpy 2.5.4, minimamba 1.0.1 installed with `pip check` clean; the repo's own pins were NOT installed there, so compatibility with pandas 3.1.0 and the lab packages is untested); about 1,260 tokens/s at seq 256, 2,100 to 3,000 tokens/s at seq 24 to 64, d=64 2 layers; (3) another Linux box the owner controls (you write the run script, the owner runs it and returns Parquet/JSON with hashes). Per L13, files cross environments as Parquet/JSON with hashes recorded in the ledger. If the sandbox or another environment is used, the data and spec must be provided again (the file is not in the repo zip) and the lock must be verifiable there (the ledger travels with it), or the run must happen on the Mac. Resolve this before building.

**Before building, also:** read the `minimamba` 1.0.1 source (shapes, causality of the scan, determinism; the README claims are the author's own); record the torch/minimamba/numpy hashes in the ledger. Use `MambaForFeatureExtraction(BaseMambaConfig)`, forward takes `(batch, seq, d_model)` float. Neuralforecast and Chronos are NOT in EXP-001 (L15). Do not run `npm audit fix --force`. Owner preferences: do not run tests for the owner; give short terminal command blocks, one concern per block; zips unzip from the repo root; owner activates the venv with `source .venv/bin/activate` (no bare `python`).

**Owner to-do not yet done:** regenerate the OANDA practice token (it was pasted in a chat). Keep the data file out of git until the OANDA terms are read.

## Phase 8B build notes (2026-10-28): CODE BUILT, EXPERIMENT NOT RUN
**Decision taken:** "proceed" was read as go; the open compute question was resolved by building the runner to work wherever the data and ledger are. The data file and ledger are only on the owner's Mac, so the run is expected there (conda env `spekrym-torch`). Sandbox measurement (Linux, 2 cores, torch 2.14.1 from PyPI, minimamba 1.0.1): one full-size epoch (7,564 rows, context 48) took 96 s (about 3,800 tokens/s), so 3 seeds x 8 epochs is about 40 minutes there; the Mac was measured earlier at 2,000 to 3,000 tokens/s (about 50 to 75 minutes). Not measured on the Mac with the real model code.

**Built (decisions L21 to L23 in DECISIONS.md):** `lab/src/sx_lab/models/minimamba_vol.py` (MiniMambaVol, MiniMambaEnsemble), `exp001_core.py` (guards, pin check, scoring, outcome rule), `exp001.py` (validate and holdout stages), `exp001_report.py`, CLI commands `exp001-validate`, `exp001-holdout`, `exp001-report` in `cli.py`, optional extra `neural` in `lab/pyproject.toml`. Tests: `lab/tests/test_minimamba_vol.py` (6) and `test_exp001_runner.py` (4); both skip when torch or minimamba are missing, so the main Mac venv is unaffected.

**Verified by me (sandbox, Python 3.13, torch 2.14.1+cu130, minimamba 1.0.1, arch 8.0.0, pandas 3.1.0):** the 10 new tests pass; `pytest lab/tests data/tests` 150 passed, 1 skipped; `ruff check lab data scripts core` clean. The model checks include: output shape and positivity, training loss falls, changing LATER input rows does not change EARLIER predictions (this checks the library's scan and conv causality empirically; I read the conv code but not every scan variant), `predict` ignores the `target` column, same seed gives the same forecast and different seeds differ, history equals concatenation, weight save/load round-trip. The runner test (synthetic fixture, 1 epoch) proves: validate then one-shot holdout then report, refusal without a lock, refusal of a second validate, refusal without validation, refusal when `validation_results.json` is tampered with (holdout stays unopened). **Not verified: any result on the real EUR/USD data, the Mac, the full-size run, or real GARCH convergence on 7,564 rows.** The full repo suite and the web checks were not run (web untouched).

**Known limits:** weights are bitwise-reproducible only on the same machine and thread count (recorded); `torch.load(weights_only=False)` is used on our own files, hashed in the ledger; the first 47 validation rows use the train tail as history and the first 47 holdout rows the validation tail (features only, no targets); if scoring crashes after the holdout is opened the frame is already saved as `holdout_frame.parquet`; NHITS, PatchTST, LSTM and Chronos are NOT built (not in the locked EXP-001 scope, L15); web Lab/Forecast tab for EXP-001 is NOT built; `mamba_ssm_vol.py` stays a stub.

**Owner run order (Mac, conda env `spekrym-torch`, repo root):**
1. `pip install -e core -e data -e lab pytest` then `pip check`.
2. `python -m pytest lab/tests/test_minimamba_vol.py lab/tests/test_exp001_runner.py -q`.
3. `nohup python -m sx_lab.cli exp001-validate --candles lab/outputs/data/eurusd_h1.parquet > lab/outputs/exp001_validate.log 2>&1 &` then `tail -f lab/outputs/exp001_validate.log`.
4. STOP and send the validation output to Claude before the holdout (L21 and L22 are Claude's interpretations; the holdout is one-shot).
5. `python -m sx_lab.cli exp001-holdout --candles lab/outputs/data/eurusd_h1.parquet --reason "EXP-001 one-shot holdout" --confirm-spend-holdout`.
6. `python -m sx_lab.cli exp001-report`, then send `lab/outputs/exp001/*.json` and `lab/experiments/EXP-001_mamba_vs_har.md`.


## EXP-001 RESULT (owner run, Mac, conda env spekrym-torch, 2026-10-28; copied from the terminal log)
Not run by me. The report file and `lab/outputs/exp001/*.json` were NOT sent to this chat; the numbers below are only those printed in the owner's terminal. Coverage, MCS p-values and per-stage sample sizes were not in the log.
- **Validation: LOSS.** MCS included: har; excluded: garch11, historical_mean, minimamba, persistence. QLIKE: har 0.24743, minimamba 0.31305, persistence 0.36010, historical_mean 0.36906, garch11 0.39908. RMSE: har 5.332e-07, historical_mean 6.648e-07, persistence 6.429e-07, garch11 7.259e-07, minimamba 6.892e-07.
- **Holdout (opened once, now spent): TIE.** MCS included: har, minimamba; excluded: garch11, historical_mean, persistence. QLIKE: minimamba 0.38809, har 0.39296, garch11 0.62018, historical_mean 0.58021, persistence 0.63444. RMSE: har 4.875e-07, minimamba 5.036e-07, persistence 5.420e-07, historical_mean 6.943e-07, garch11 7.722e-07.
- Per-seed validation QLIKE (diagnostic): seed 1 0.33482, seed 2 0.39336, seed 3 0.32987. Last-epoch training QLIKE: 0.05201, 0.04065, 0.06572 (training loss far below validation: overfit).
- Variants tried: 3 of 20 (three seeds). Headline per L22 = holdout TIE; validation LOSS reported alongside. L21 to L23 CONFIRMED by the owner. Training took 4,875 s for the three seeds.
- The owner ran the holdout without first sending the validation output (the run order said to stop). Harmless here, but L21 and L22 were confirmed only afterwards.
- A different recipe (early stopping, dropout, smaller model) is EXP-002 with its own pre-registered spec. Do not edit `EXP-001.yaml` and do not reopen the holdout.

## Phase 8C notes (2026-10-28)
**Built:** `apps/api/src/sx_api/exp001.py` and `routes/exp001.py` (`GET /lab/exp001`: reads `lab/outputs/exp001/validation_results.json` and `holdout_results.json`, whitelist of fields, drops `environment`, refuses a holdout without validation or mixed spec hashes; status `not_run | validated | complete`). Web: `contracts/exp001.ts` (zod), `labApi.fetchExp001`, `lab/exp001Format.ts`, `lab/useExp001.ts`, `components/lab/{Exp001Panel,Exp001Stage,Exp001Tab,LabDataTab}.tsx`, `components/ForecastTab.tsx` (replaces the placeholder in the Inspector), `screens/LabScreen.tsx` (tabs Data and EXP-001). Decision L24. L21 to L23 now Confirmed.
**Tests:** `apps/api/tests/test_exp001.py` (3), `apps/web/src/test/exp001.test.tsx` (8), `app.test.tsx` Forecast-tab test now wraps the app in a QueryClientProvider. Fixtures are labelled `TEST FIXTURE - NOT EXP-001 RESULTS` (`tests/fixtures/lab/exp001/`, `apps/web/src/test/fixtures/exp001_payload.json`); they are NOT the real results.
**Verified by me (sandbox):** web `tsc --noEmit`, `eslint src`, `vitest run` 81 passed, `npm run build` ok; `pytest apps/api` 34 passed; `ruff check .` clean. **Not verified:** the full repo pytest suite, Playwright (not run), the screen against the real JSON, light-theme look, the `/lab/exp001` endpoint against the real files on the Mac.
**Known limits:** no regime label or live forecast exists (the Lab never produced one), so the Forecast tab shows EXP-001 only; the 20-variant cap is a constant in `exp001Format.ts` copied from the locked spec; the Lab tab shows whatever the files say (the web does not recompute anything).

### Owner verification of Phase 8C (2026-10-28, Mac, Intel; from the owner's terminal and two screenshots)
- `npm run typecheck`, `npm run lint` clean; `npm test` 81 passed (9 files); `npm run build` ok (two upstream zod comment warnings from Rollup and a chunk-size warning of 552 kB; both harmless, revisit code-splitting in Phase 10). API served on :8000, web on :5175. Lab > EXP-001 renders the real files (screenshots), Data tab present. The backend `pytest -q`, the Forecast tab and light theme were NOT shown, so they are unconfirmed.
- Real coverage figures (nominal 0.800, split-conformal, calibrated on the first 1,249 validation rows), read from the screenshots:
  - Holdout (2,498 rows): HAR measured 0.590, mean width ratio 1.15, worst rolling-50 0.00; MiniMamba measured 0.721, width ratio 2.02, worst rolling-50 0.00.
  - Validation (later half, 1,225 rows): HAR 0.725, width ratio 1.15, worst rolling-50 0.00; MiniMamba 0.781, width ratio 2.02, worst rolling-50 0.16.
  - Both models under-cover on the holdout, and a rolling-50 window with 0.00 coverage exists for both; the exchangeability caveat in the report is borne out. MiniMamba's intervals are about 1.75 times wider than HAR's for the extra coverage.
- Real MCS p-values. Holdout: MiniMamba 1.000, HAR 0.909, persistence 0.020, historical mean 0.000, GARCH 0.000. Validation: HAR 1.000, MiniMamba 0.039, persistence 0.021, historical mean 0.000, GARCH 0.000 (MiniMamba missed the 0.10 level on validation).
- Data version `dv:8db0760d82acfc2a`; spec `7a541633a9161018`; label `OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED`.
- Reading, no more: on the holdout MiniMamba has the lowest QLIKE (0.38809 vs 0.39296) but HAR has the lowest RMSE and the confidence set cannot separate them; validation was a loss; training loss is far below validation. No evidence of an advantage over HAR.
- UI nit: the top bar still says "Sample data" and the status line "SAMPLE DATA - NOT LIVE" on the Lab screen. That refers to the premarket chart sample, not EXP-001, which can confuse. Not changed yet.
- **Phase 8 items NOT built** (not part of the locked EXP-001, L15): `nf_baselines.py`, `chronos_zeroshot.py` (empty files), `mamba_ssm_vol.py` (stub until a GPU exists). `regime/markov_switching.py` and `changepoints_offline.py` have code from earlier phases; they are not shown in the web. Decide with the owner whether to build these or move them.

## Phase 9A notes (2026-10-28): CODE BUILT, REAL-DATA RUN NOT DONE
**Start state found:** Phase 8 closed; P11 confirmed by the owner (recorded as Confirmed in DECISIONS.md, built as M1 to M10); the plan's known issue 1 (session bands) was already fixed in Phase 1, so the "start with the session bands bug" instruction did not apply. The Lab badge fix (X17) was the first 9A item and is done (M10). Owner terminal log showed the 8C/close-out zips unzipped and the EXP-001 records copied to `lab/experiments/EXP-001_records/` (ledger hash identical).

**Built** (`assistant/src/sx_assistant/model/`): `labels_triple_barrier.py`, `features.py` (14 causal features, look-back capped at 48 bars), `windowed.py` (setups on overlapping windows), `protocol.py` (spec, purge gap 72 bars, `ScorerPartition`, sealed holdout through the ledger), `train_lgbm.py` (LightGBM adapter, rank metrics), `controls.py` (shuffled-label and leaked-feature controls), `explain_shap.py` (SHAP adapter with shape and additivity checks), `scorer.py` (rank score + reasons + labels), `run.py` (commands `validate`, `holdout`, `report`). Outputs go to `assistant/outputs/model/` (gitignored, own ledger). Fixtures: `tests/fixtures/model/` made by `scripts/make_model_fixtures.py` (synthetic random walk, no edge). Web: Lab badge fix and a `Source label` column in the Data tab.

**Run by me (sandbox, Linux, Python 3.12.3, lightgbm 4.7.0, shap 0.54.1):** `pytest` on the two new test files, 16 passed (labels by hand, feature prefix stability, bounds on look-back, windowed equals full for a causal producer, purge, holdout governance incl. changed data/spec/second opening, deterministic fit, both negative controls, scorer reasons/labels/no probability wording, save/load); `ruff check .` clean; web `typecheck`, `lint`, `vitest` (10 files, 83 passed, 2 new), `build` OK. One end-to-end smoke of `validate` then `holdout` on the SYNTHETIC fixture (1,800 bars, real TA output, 23 s): the controls behaved, the validation result was inside the shuffled range (null, as it should be on a random walk), the holdout opened once and a second opening was refused, the ledger verified (7 entries).
**Not run by me:** the full repo `pytest`, the API tests, Playwright, anything on real EUR/USD data (the data file lives only on the owner's Mac), the Mac itself, light theme, `pip-audit`. lightgbm's `libomp` need on the Intel Mac is unconfirmed.

**Findings during the build (kept):** (1) a shuffled-label control without the same best-of-5 selection made a random-walk validation AUC (0.5625) look above the shuffled p95 (0.544); after repeating the selection in the control it sits at the shuffled maximum (M6). (2) shap 0.54.1's warning about a list output is wrong for this version (see DEPENDENCIES).

**Known limits (9A):**
- 9A-1 No real result exists. Whether the scorer shows any ranking skill on EUR/USD H1 is unknown; a null result is expected and valid.
- 9A-2 Labels use mid prices, no spread or slippage; a barrier result is not a P&L result.
- 9A-3 Windowed setups (M9) differ slightly from one full replay by design; setups were not compared against a full replay on real data.
- 9A-4 Overlapping label windows make rows dependent; the AUC interval is iid and optimistic. 9A uses one validation split and one seed.
- 9A-5 `known_at` of swing-based setups is honest but late (issue 28); decision time follows it.
- 9A-6 Barrier multiples, grid, 48-bar look-back, feature set and the 20 shuffles are my provisional choices (M1, M3, M5), not owner-reviewed.
- 9A-7 Holdout governance is a process rule (L-3). `run.py` loads the whole candle file, so the code could in principle read holdout rows; the rule is that it does not before `open_holdout`.
- 9A-8 The scorer is not wired into any API route or screen (that is 9B). Nothing calls `Scorer.score` yet except tests.
- 9A-9 The Lab screen still shows the API-unreachable banner text about the offline chart sample when the API is down; the top bar still says `M15` on the Lab screen (premarket chart timeframe). Not changed.
- 9A-10 Intraday sessions in `features.py` use the default fixed UTC session hours (`DEFAULT_SESSIONS`), not the DST-aware ones.

**Owner run order (Mac, repo venv):** install `assistant[dev,model]`, check `import lightgbm`, run the new tests, then `python -m sx_assistant.model.run validate --candles lab/outputs/data/eurusd_h1.parquet` (setups take a few minutes the first time and are cached by data version). STOP and read the validation output and the controls. Only then run `holdout` once with `--confirm-spend-holdout`. Then `report`. Send back `assistant/outputs/model/validation_results.json` and `holdout_results.json`. Do not edit `ProtocolSpec` after validation: a changed spec makes the holdout refuse (new experiment id needed).


## Owner environment fix and 9A run state (2026-10-28, from the owner's terminal)
- `import lightgbm` failed on the Intel Mac with `Library not loaded: @rpath/libomp.dylib` (the 9A "unconfirmed" item is now CONFIRMED). `brew install libomp` failed: Homebrew has no Intel bottles and the Command Line Tools were rejected ("does not support macOS 15"). Fix used: `ln -s /Users/akilaranasinghe/miniforge3/envs/spekrym-torch/lib/libomp.dylib /usr/local/lib/libomp.dylib`; afterwards `import lightgbm, shap` printed `4.7.0 0.54.1`. The link points into the `spekrym-torch` conda env; if that env is deleted LightGBM breaks again.
- The owner ran `sudo rm -rf /Library/Developer/CommandLineTools` and did NOT reinstall (`sudo xcode-select --install` was not completed). Terminal `git`, `brew` and compilers may fail until it is reinstalled; GitHub Desktop and the Python/Node steps are unaffected.
- Owner results afterwards: the 9A tests `16 passed`; full `pytest -q` **601 passed, 3 skipped**, `ruff check .` clean. `python -m sx_assistant.model.run validate ...` had printed `computing setups on windows ... 4320/12864` when the log was pasted; **its output, the controls and the holdout are NOT known to me yet.** The holdout has NOT been opened.

## Phase 9B notes (2026-10-28): CODE BUILT, not run with a real scorer, owner has not reviewed the screen
**Start state:** the owner said "proceed with the next phase" while `validate` was still computing, so 9B was built against the 9A output format, not a 9A result. The API returns an empty list (`no_result`) until `assistant/outputs/model/validation_results.json` exists. The plan's rule that 9B needs a 9A result to READ is therefore met only after the owner's `validate` finishes.
**Built:** `assistant/src/sx_assistant/suggestions/engine.py` (`build_suggestions`, `EngineConfig`, `EngineResult`), `evidence.py` (`make_reason`, `validate_suggestion`, wording check), `gates_view.py` (runs the Phase 6 gate classes as advice); `apps/api/src/sx_api/suggestions.py` and `routes/suggestions.py` (real `/suggestions`, replaces the placeholder; `create_app` got optional `model_dir` and `rules_path`); web `contracts/suggestions.ts`, `suggestions/{suggestionsApi.ts,format.ts}`, `screens/SuggestionsScreen.tsx`, `components/suggestions/{SuggestionCard,ScorerBanner,EvidenceChart}.tsx`, `App.tsx` wiring. Decisions S1 to S8 (DECISIONS.md); API envelope in CONTRACTS.md. No change to the `Suggestion` contract.
**Tests added:** `assistant/tests/test_suggestions_engine.py` (6: claims resolve and levels follow the side; prefix equality on truncated history; unknown evidence, wrong-suggestion evidence, empty reasons and probability wording rejected; forecast claim linked and causal; gates use the frozen rules, blackout blocks, state-unknown note; unfrozen rules and non-H1 refused), `apps/api/tests/test_suggestions.py` (4 plus 1 skipped real-scorer test), `apps/web/src/test/suggestions.test.tsx` (8) with fixtures `suggestions_payload.json` (source label `TEST FIXTURE - NOT REAL SUGGESTIONS`) and `suggestions_empty.json`. `apps/api/tests/test_api.py` no longer lists `/suggestions` among the placeholders.
**Run by me (sandbox, Linux, Python 3.12.3, lightgbm 4.7.0):** new Python tests 10 passed, 1 skipped; `pytest apps/api assistant/tests/test_suggestions_engine.py assistant/tests/test_model_protocol.py assistant/tests/test_paper_runner.py` 65 passed before the placeholder fix and `pytest apps/api` 37 passed, 1 skipped after; `ruff check .` clean; web `typecheck` and `lint` clean, `vitest run` 11 files, 91 passed, `npm run build` OK (bundle 565 kB, the known chunk warning). A bug found by the test run and fixed: a missing scorer file raised a LightGBM error that became a 500; it now returns `model_unavailable`.
**Not run by me:** the full repo `pytest` (owner's last full run was 601 passed before 9B), anything with a REAL scorer or real data (the scorer files only exist on the owner's Mac after `validate`), Playwright, the screen in a browser, light theme, the Mac.
**Known limits (9B):**
- 9B-1 Tested only with a scorer trained on the synthetic fixture. Nothing says the real scorer ranks anything well; the screen shows the 9A reading above the list for that reason (S7).
- 9B-2 Suggestions in the browser are computed on the frozen SAMPLE data (S8); the sample is about 70 H1 bars, so few or no setups may qualify. A real data source is a later item.
- 9B-3 The API recomputes H1 setups on every request (no payload cache) and loads the scorer once per model hash.
- 9B-4 `build_payload` catches `Exception` around loading the scorer so LightGBM's own error type becomes a visible `model_unavailable` message.
- 9B-5 The evidence chart is self-contained (H1 closes, the setup box, entry/stop/target). It is not the main chart: the main chart shows M15 objects whose ids differ from H1 setup ids, so a click-through to the Chart screen is not built.
- 9B-6 No order path from a suggestion exists (S6); the Paper screen (Phase 10) decides how a suggestion becomes an `OrderRequest`.
- 9B-7 The top bar still shows `M15` and the premarket `Sample data` badge on the Suggestions screen (the badge is accurate here; the timeframe text is not).
- 9B-8 Done-when "screen reviewed by the owner" is still open.
**Owner checks (after `validate` finishes and you have read it):** start the API (`python -m uvicorn sx_api.main:create_app --factory --port 8000`), open `http://127.0.0.1:8000/suggestions` (expect `status` `ok`, `model_unavailable` or `no_result`, never an error page), then open the Suggestions screen in the web app.


## Phase 9B fix and 9A result (2026-10-28)
**9A result, from the owner's terminal (holdout, spent once, labels Exploratory / Not validated / Retrospective):** spec `affd7d02...`, config `2af18570...`, data `dv:7f3fd84d9436f1a2`. n 2,648; AUC 0.5062 (iid 95% interval 0.4833 to 0.5259, optimistic because label windows overlap); target-first share 0.387 overall and 0.397 in the top fifth (529 rows); shuffled control (20 shuffles) AUC mean 0.5023, p95 0.5203, max 0.5307, behaved as expected. Verdict printed: **NULL, neither period ranks above the shuffled-label range.** The validation output was not pasted to me, so I have not read it. The holdout is spent; any new scorer test needs a new experiment id.
**Bug (screenshot, Suggestions screen):** the web showed `Suggestions could not be loaded` with zod errors `items.N.suggestion.forecast_id: expected string, received null`. Cause: `apps/api/src/sx_api/suggestions.py` serialised with `model_dump(mode="json")`, which keeps `None` fields; `contracts/suggestion.ts` uses `.optional()`, which accepts a missing key but not null. Phase 9B tests missed it because the only test that serves real items is skipped without a real scorer. The API log shows `/suggestions` returned 200, so the fault was on the contract boundary, not the server.
**Fix:** `s.to_wire()` and `e.to_wire()` (they omit `None`, as `_base.py` documents). The web contract was NOT loosened. Regression test `test_wire_payload_has_no_null_fields_zod_would_reject` added to `apps/api/tests/test_suggestions.py`.
**Run by me (sandbox, Python 3.12, per owner's request to keep testing minimal):** `pytest apps/api/tests/test_suggestions.py` 5 passed, 1 skipped; `ruff check apps/api` clean. NOT run: full pytest, web checks (no web file changed), the screen in a browser.
**Still open:** (1) S7: with a null 9A result the screen still lists suggestions under the null reading; decide whether to hide them; (2) 9B-8 owner review of the screen; (3) P6 before 9C; (4) the two concept images the owner attached (session preparation workspace, Intelligence Canvas) are design references only; nothing was built from them; (5) Command Line Tools were removed on the Mac (see earlier note).


## Phase 9B polish (2026-10-28)
**Owner screenshot findings fixed:** (1) Entry/Stop/Target labels on the evidence chart overlapped: text is now de-collided with `layers/decollide.ts` (lines stay at true prices). (2) A long straight stretch in the price line: x was clock time so the weekend gap was drawn as flat; x is now bar index (gap = one bar width), and the setup box uses the same mapping. (3) S7a: rank text is muted when 9A shows no skill.
**Changed:** `EvidenceChart.tsx`, `SuggestionCard.tsx`, `SuggestionsScreen.tsx`, `suggestions/format.ts`; tests: new `suggestions/format.test.ts` (2), two added to `test/suggestions.test.tsx` (label spacing, gap width).
**Run by me (sandbox):** `npm run typecheck` and `lint` clean; `vitest` on the two suggestion test files 12 passed. NOT run: full web suite, build, the screen in a browser (so how the chart now looks is unverified).
**Limits:** the index axis means the time axis is not to scale across gaps (labels on it are not shown, so nothing misleads, but spacing is by bar). The top bar still says `M15` on this screen (9B-7).


## Dataset management (2026-10-28, owner request after the Lab screenshot)
**Asked:** manage the Lab datasets from the dashboard: delete and more; fix the layout problems.
**Built:** API `DELETE /lab/datasets/{file}` (to `.trash`), `GET /lab/datasets` now also returns `trash` and `in_use` per file, `POST /lab/datasets/trash/{id}/restore`, `DELETE /lab/datasets/trash/{id}` (for good); `apps/api/src/sx_api/dataset_admin.py`; `create_app(experiments_dir=...)`; CORS now allows DELETE (without it the browser blocks the call even though the API works). Web: `DatasetActions.tsx` (Delete, confirm, `In use` lock with the reason), `TrashTable.tsx` (Restore, Delete for good with confirm), `LabDataTab.tsx` wiring, `labApi.ts` calls, zod contract (`in_use`, `trash`, both tolerated when absent).
**Layout fixes:** file names no longer wrap into a narrow column (one line, the table scrolls sideways if needed); the Lab page is wider (`max-w-6xl`); the "file already exists" message now says where to delete it.
**Protection (L25):** checked against the real repo files in the sandbox: `eurusd_h1.parquet` (`dv:7f3fd84d9436f1a2`) shows `in use by prereg/EXP-001.yaml`; the 1-year file is free. On the Mac the saved 9A model files add to the lock.
**Run by me (sandbox):** `pytest apps/api` 46 passed, 1 skipped; 8 new tests in `test_dataset_admin.py` (trash, restore, purge, no overwrite, protection by spec and by model file, path-like names refused, CORS); `ruff check apps/api` clean; web `typecheck` and `lint` clean; vitest on the 3 Lab test files 15 passed (6 new). NOT run: full web suite, build, full repo pytest, the screen in a browser, a real delete on the Mac.
**Known limits:** (1) protection is a text match inside the two folders (L25); (2) the trash has no automatic expiry or size limit; (3) no "rename", "verify now" or "export" action; (4) files with no provenance can be deleted unless their name appears in a protected file; (5) the download job does not check the trash, so a re-download of a trashed range is allowed (the restore then refuses to overwrite it).


## Phase 9C-1 notes (2026-10-28): analyst core BUILT, NOT run against the real providers

**Start state:** P6 decided by the owner (A1). Keys were pasted into the chat; they were NOT written to any file.
**Built** (`assistant/src/sx_assistant/analyst/`): `errors.py`, `provider.py` (interface), `providers/{_http,groq,gemini,fake}.py`, `config.py` + `approved_models.json` (A2), `packet.py` (evidence packet), `brief_types.py`, `validate.py`, `prompts/brief_v1.py`, `router.py`, `brief.py`, `run.py` (CLI: `check`, `brief`, `brief --fake`). `core/config.py` `Settings` got `groq_api_key` and `gemini_api_key` (additive). `assistant/pyproject.toml` lists `httpx==0.28.1`. `agent.py` and `debate.py` stay empty (9C-3). Decisions A1 to A9.
**Tests added** (46, all with mocked HTTP or fake providers): `assistant/tests/test_analyst_{validate,router,providers}.py` and `analyst_helpers.py`.
**Run by me (sandbox, Python 3.13, venv):** the 46 new tests passed; `ruff check assistant core` clean; `core/tests` 145 passed, 1 failed (`test_repo_env_example_is_paper_and_loads`: `.env.example` was not in the handoff zip, so it is not caused by this change); the offline demo `brief --fake` printed PUBLISHED with 3 claims. `test_suggestions_engine.py` could not be collected here (lightgbm not installed in my venv); not related.
**NOT run by me:** any call to Groq or Gemini (the sandbox cannot reach them), so the request and reply field names in the two adapters are unverified against the live services; the full repo suite; the web app (no web change).
**Known limits (9C-1):** (1) cooldowns and usage are in memory only, so a restart forgets them; no daily request counter yet (9C-2). (2) Free-tier limits were not verified: Groq's rate-limit page lists limits for its Developer plan only and does not state Free-plan numbers; Gemini's free-tier numbers were not read. Check both consoles. (3) A brief is built from the frozen sample only; no API route, no web screen, no bull/bear step. (4) The number check is string-level: a correct rounded number is marked unverified, and a wrong claim that reuses a real number can still pass; it is a tripwire, not proof. (5) Reasoning models may spend output tokens thinking; `max_output_tokens` is 2,000 and an empty reply counts as a transient failure. (6) A8 is open.
**Owner run order (Mac, repo venv):** (1) add the two keys to `.env` (not committed); (2) `pip install -e assistant` once (adds httpx pin, already present); (3) `python -m sx_assistant.analyst.run brief --fake` (offline, expect PUBLISHED); (4) check each provider console shows a free plan and no billing, then set `owner_confirmed_free` to true for the model(s) in `assistant/src/sx_assistant/analyst/approved_models.json`; (5) `python -m sx_assistant.analyst.run check`; (6) `python -m sx_assistant.analyst.run brief`. Send back the printed lines (no keys).


### Owner run of 9C-1 (2026-10-28, from the owner's terminal and two screenshots)
`brief --fake` PUBLISHED (3 claims, 0 unverified); the 46 new tests passed on the Mac; `analyst.run check`: Groq key accepted, 11 models visible, `openai/gpt-oss-20b` among them; Gemini key accepted, 46 models visible, `gemini-3.8-flash` among them (so the A7 default ids exist for these keys). `brief` was REFUSED as designed (`owner_confirmed_free` still false). Screenshots: Groq console shows key `FX-x` with 0 API calls; Google AI Studio lists both keys under "Free tier" with a "Set up billing" link (not enabled). The Groq plan and billing were NOT visible in the screenshot. The key endings in the screenshots match the keys pasted into the chat: they have NOT been rotated yet.

## Phase 9C-2 notes (2026-10-28): persisted state, caps, service, API; NOT run against the real providers

**Built:** `analyst/state.py` (`ProviderState`, `MemoryState`, `SqliteState`), `analyst/router.py` rewritten to use a state store, a clock and daily caps, `analyst/log.py` (routing log), `analyst/service.py` (`AnalystService`: status, latest, generate with reuse and a single-flight lock), `config.py` (`caps`, `load_env`), key fingerprints on the adapters, `approved_models.json` (`max_requests_per_day`), `run.py` (new `status` and `reset`, `brief --force`, state kept in `assistant/outputs/analyst/`). API: `apps/api/src/sx_api/routes/analyst.py` (`GET /analyst/status`, `GET /analyst/brief`, `POST /analyst/brief`), `create_app(analyst_dir=, analyst_setup=)`. Decisions A10 to A13. No web change (the brief drawer is 9C-3).
**Tests added:** `assistant/tests/test_analyst_state.py` (13: cooldown survives a restart, counters include timeouts, cap and day rollover, failover on cap, disable persists until key change or reset, health values, reuse and force, unavailable states, failover trail in the log, busy lock, status shows no secrets), `apps/api/tests/test_analyst_api.py` (5).
**Run by me (sandbox, Python 3.13):** the 3 earlier analyst test files plus the 2 new ones, 62 passed; `ruff check assistant apps/api` clean; `brief --fake` run twice (second printed `reused, no call made`). **NOT run:** any real provider call, the full repo suite, the web app, the Mac.
**Known limits (9C-2):** (1) usage and caps are estimates, and the cap number (50) is my provisional choice; (2) real Groq and Gemini free-plan limits are still unread; (3) no Cloudflare or OpenRouter (not built until tested); (4) the packet is still the frozen SAMPLE; real data needs A8 decided; (5) `POST /analyst/brief` rebuilds the premarket analysis every call (a few seconds) before it can reuse a saved brief; (6) SQLite state is single-machine; (7) the SQLite file stores the 8-character key hash, so keep `assistant/outputs` private (it is gitignored).
**Owner steps:** see the end of the 9C-2 message in chat (confirm free plans, set `owner_confirmed_free`, `status`, `brief`, then `brief` again to see the reuse).


## Phase 9C-2 fix (2026-10-28): stale 9C-1 brief file crashed `brief`
**Owner log:** `analyst.run brief` raised `KeyError: 'brief'` at `service.py` line 80 (twice). Cause: `assistant/outputs/analyst/brief_bd989f2e075e7629.json` was written by the 9C-1 `brief --fake` run in the old layout (the brief itself, no `brief` key). 9C-2 found it by packet hash and tried to reuse it. Worse, even a correctly formatted fake brief in that folder would have been reused as if it were a real one.
**Fix:** `AnalystService._read_file` returns the saved file only if it parses, has a `brief` key and was not written by the `fake` provider; otherwise it is ignored and a new brief is generated. `latest()` uses it too (newest valid file first). Test `test_old_layout_and_fake_briefs_are_not_reused` added.
**Run by me (sandbox, Python 3.12):** `pytest assistant/tests/test_analyst_state.py` 12 passed (the 13 I listed earlier were really 12 in this file; the owner's run showed 16 for this file plus the API file); `ruff check` on the two changed files clean. NOT run: any real provider call, the full suite.
**Still the owner's:** confirm free plans in `approved_models.json`; the first real `brief` has not run yet (it was refused, then crashed on this bug).


## Phase 9C-2 fix 2 (2026-10-28): one unconfirmed provider blocked the confirmed one
**Owner log:** with Gemini confirmed and Groq not, `brief` still said UNAVAILABLE for Groq. I had told the owner an unconfirmed provider would be skipped; that was wrong (I had only tested the all-or-nothing case). `build_providers` raised on the first unconfirmed provider.
**Fix:** an unconfirmed provider is now skipped (listed in `skipped`, never called). `ApprovalError` is raised only when no provider is confirmed. Test `test_unconfirmed_provider_is_skipped_when_another_is_confirmed`.
**Run by me (sandbox):** providers, state and router test files and `ruff check assistant`; results in the chat message. NOT run: any real provider call.
