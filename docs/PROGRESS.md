# Progress

See `docs/DEVELOPMENT_PLAN.md` for the full phase plan and handoff notes. **New session: read section 0 of that file first.**

**Next action:** Phase 6B is verified; Phase 7 only when the owner says go. (Older note follows.) **Next action:** wait for the owner. Phase 4 and the pre-Phase-5 pass are built. Phase 5 starts when the owner says go; its data source is frozen fixtures labelled `SAMPLE DATA — NOT LIVE` (owner, 2026-10-27). Open for the owner: (1) run the checks in "Pre-Phase-5 notes" on the Mac; (2) ~~X14 deviation~~ approved 2026-10-27; (3) ~~I15 numbers~~ provisional defaults kept; (4) first real OANDA practice run (issue 18, account access unconfirmed); (5) Phase 1 visual review and P8.

| Phase | Scope | Status |
|---|---|---|
| 0 | Scaffold, foundation docs, web app v0 on sample data | Done |
| 1 | Web: fix bands, Cmd+K, presets, replay, tests | Built 2026-10-26, all automated checks green. Awaiting owner visual review. See "Phase 1 notes" below |
| 2 | `core/` contracts, causality harness, ledger | Built 2026-10-26, all automated checks green. See "Phase 2 notes" below |
| 3 | `data/` OANDA practice client, resample, quality | Built 2026-10-26, owner re-ran the suite on Python 3.14 (176 passed, ruff clean). **Never run against the real OANDA API.** See "Phase 3 notes" below |
| 4 | `assistant/ta` causal adapters | Built 2026-10-27. Sandbox: 283 passed. **Owner's Mac (Intel, Python 3.14.3): 283 passed, 0 skipped, 2026-10-27.** `ruff` not yet run by the owner. See "Phase 4 notes" below |
| 4.5 | Pre-Phase-5 pass: P10 (X14), I10 approved, I15 definitions, issue 27 speed-up | Built 2026-10-27. Sandbox: 430 passed, ruff clean. **Not yet run on the owner's Mac.** See "Pre-Phase-5 notes" below |
| 5 | Premarket builder, API, connect web | Not started |
| 6A | Paper simulator core (`assistant/paper`) | Built 2026-10-27. Sandbox: 12 new tests passed, ruff clean. Owner's Mac: 473 passed, ruff clean, live-mode refused. See "Phase 6A notes" |
| 6B | Risk gates, frozen rules, runner | Built 2026-10-27. Sandbox: 14 new tests (26 with 6A) passed, ruff clean. Owner's Mac: 487 passed, ruff clean, freeze hash and changed-rules refusal checked. See "Phase 6B notes" |
| 7 | Lab foundations and baselines | Not started |
| 8A | Lab infrastructure and frozen EXP-001 spec | Not started |
| 8B | Lab challengers and EXP-001 run | Not started |
| 9 | Model, analyst, suggestions | Not started |
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
