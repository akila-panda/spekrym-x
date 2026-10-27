# Spekrym-FX — New Modules: Repo & Library Research

**Date:** 2026-10-26
**Purpose:** Consolidated findings on external projects that could feed (A) a **Lab module** (volatility / regime forecasting with sequence models) and (B) a **standalone Trade-Assistant module** (technical analysis, premarket analysis on charts, AI/bot suggestions, paper trading) built from new, reputable libraries rather than the existing Spekrym detectors.

**Method and limits (read first).**
- Sources: PyPI pages, GitHub pages and arXiv/Zenodo abstracts, read through a web-fetch tool that summarises pages.
- **Not done:** no package was installed, run, or code-audited. GitHub pages often did not show last-commit dates or release lists, so "actively maintained" is unconfirmed unless stated. Star counts are as displayed on the page.
- Items marked **(unverified)** could not be confirmed from a primary page.
- Before adopting anything: sandbox install, `pip-audit`, licence review, pin versions.

---

## Quick links: every project we plan to add

Links marked † are the canonical project addresses; they were not opened during the research, so check them when you first visit. All others were seen during the research.

### Lab module (volatility / regime forecasting)
| Project | Repo / docs | Package page |
|---|---|---|
| minimamba | [github.com/Xinguang/MiniMamba](https://github.com/Xinguang/MiniMamba) (address given on its PyPI page) | [PyPI](https://pypi.org/project/minimamba/) |
| Mamba (official, `mamba-ssm`) | [github.com/state-spaces/mamba](https://github.com/state-spaces/mamba) | [PyPI](https://pypi.org/project/mamba-ssm/) |
| arch | [github.com/bashtage/arch](https://github.com/bashtage/arch) · [docs](https://arch.readthedocs.org/en/latest/) | [PyPI](https://pypi.org/project/arch/) |
| neuralforecast (Nixtla) | [github.com/Nixtla/neuralforecast](https://github.com/Nixtla/neuralforecast) · [docs](https://nixtlaverse.nixtla.io/neuralforecast/) | [PyPI](https://pypi.org/project/neuralforecast/) |
| Chronos-2 (Amazon) | [Hugging Face model page](https://huggingface.co/amazon/chronos-2) (install name: `chronos-forecasting`) | — |
| MAPIE | [github.com/simai-ml/MAPIE](https://github.com/simai-ml/MAPIE) | — |
| Optuna | — | [PyPI](https://pypi.org/project/optuna/) † · [version page](https://simple-repository.app.cern.ch/project/optuna) |
| MLflow (optional) | — | [PyPI](https://pypi.org/project/mlflow/) † · [overview](https://aiwiki.ai/wiki/mlflow) |
| statsmodels `MarkovRegression` | [docs](https://www.statsmodels.org/v0.14.4/generated/statsmodels.tsa.regime_switching.markov_regression.MarkovRegression.html) | — |
| ruptures (offline labelling only) | [github.com/deepcharles/ruptures](https://github.com/deepcharles/ruptures) · [paper](https://arxiv.org/pdf/1801.00826) | — |
| purged-cross-validation (cross-check only) | [github.com/eslazarev/purged-cross-validation](https://github.com/eslazarev/purged-cross-validation) | — |

### Standalone Trade-Assistant module
| Layer | Project | Repo / docs | Package page |
|---|---|---|---|
| Data | tickterial (Dukascopy ticks, optional) | — | [PyPI](https://pypi.org/project/tickterial) |
| Data | OANDA practice samples (reference for direct REST use) | [github.com/oanda/v20-python-samples](https://github.com/oanda/v20-python-samples) | — |
| TA | TA-Lib | [github.com/TA-Lib/ta-lib-python](https://github.com/TA-Lib/ta-lib-python) | [PyPI](https://pypi.org/project/TA_Lib/) |
| TA / SMC | smart-money-concepts | [github.com/joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts) | — |
| TA | trendln | — | [PyPI](https://pypi.org/project/trendln/) |
| Charts | TradingView Lightweight Charts (JS) † | [github.com/tradingview/lightweight-charts](https://github.com/tradingview/lightweight-charts) † | — |
| Charts | lightweight-charts-python | [github.com/louisnw01/lightweight-charts-python](https://github.com/louisnw01/lightweight-charts-python) · [docs summary](https://docsearch.algolia.com/mcp/docs/repo/louisnw01/lightweight-charts-python) | [PyPI](https://www.pypi.org/project/lightweight-charts/1.0.17/) |
| Charts | Plotly (candlesticks, rectangles) | [candlestick docs](https://plotly.com/python/candlestick-charts/) | — |
| Model | LightGBM | — | [libraries.io page](https://libraries.io/pypi/lightgbm) |
| Model | SHAP † | [github.com/shap/shap](https://github.com/shap/shap) † | — |
| Model | mlfinpy (labelling reference) | [docs](https://mlfinpy.readthedocs.io/en/stable/_sources/Labelling.rst.txt) | — |
| LLM | Pydantic AI † | [github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) † · [comparison article](https://www.mindstudio.ai/blog/agent-sdk-vs-framework-claude-pydantic-ai-production) | — |
| LLM (design reference only) | TradingAgents | [github.com/TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) · [paper](https://arxiv.org/pdf/2412.20138v6) | — |
| Paper trading | ib_async | [github.com/ib-api-reloaded/ib_async](https://github.com/ib-api-reloaded/ib_async) | [PyPI](https://pypi.org/project/ib_async) |
| Paper trading | cTrader Open API (OpenApiPy) | [github.com/spotware/OpenApiPy](https://github.com/spotware/OpenApiPy) · [docs](https://help.ctrader.com/open-api/) | [PyPI](https://pypi.org/project/ctrader_open_api/0.9.1) |

### Pilot / pattern-borrowing (from the first batch)
| Project | Repo | Package page |
|---|---|---|
| forex-pytory (calendar pilot) | [github.com/AtaCanYmc/forex-pytory](https://github.com/AtaCanYmc/forex-pytory) (address from PyPI provenance) | [PyPI](https://pypi.org/project/forex-pytory/) |
| tickerflow (provider-fallback pattern) | [github.com/FaustoS88/tickerflow](https://github.com/FaustoS88/tickerflow) | [PyPI](https://pypi.org/project/tickerflow/) |
| technical-analysis (test oracle only) | — | [PyPI](https://pypi.org/project/technical-analysis/) |

### Evaluated but not planned (for reference)
[QuantAgent](https://github.com/Y-Research-SBU/QuantAgent) · [AgenticTrading](https://github.com/Open-Finance-Lab/AgenticTrading) · [NautilusTrader](https://www.pypi.org/project/nautilus_trader) · [Lumibot](https://pypi.org/project/lumibot/) · [hmmlearn](https://pypi.org/project/hmmlearn) · [TimesFM](https://github.com/google-research/timesfm) · [smtlab fork](https://github.com/smtlab/smartmoneyconcepts) · [genebot](https://pypi.org/project/genebot/)

---

## 0. Context: what the project already has and what the research concluded

- **Research engine ("the Judge"):** locked train/validation/vault split, pre-registered experiments, expectancy net of real bid/ask cost, FDR correction, append-only ledger. The vault has never been opened.
- **Verdict so far (`NO_INTRADAY_EDGE.md`):** every tested EUR/USD intraday family (ORB breakout, fade, session momentum, Asian-range, ICT confluence, ML forecasting) failed to show a durable, cost-surviving edge. Next move recommended: *different information*, not more transformations of the same candles.
- **Frontend:** React/TypeScript, 1,515 tests passing. Scan cockpit, DESK DK0–19 (causal detectors for structure, S/R, FVG, liquidity, S/D, price action; Prepare/Live/Review), and F-track intelligence surfaces F0–F20 (Canvas, regime strip, Scenario Studio, Analytics, Workbench, Brain, Portfolio, Ops, Visual Query, Attention). Next planned phase: F21.
- **Backend already present:** `market_context/` ICT-style detectors, deterministic multi-agent `agents/` coordinator with audit log and an LLM-narrator hook, OANDA data ingestion, `paper_trading/` as an empty stub (Phase E designed but gated on a "GO" verdict).
- **Principles to preserve in any new module:** Judge is the only verdict authority; LLMs/Brain propose, never certify; nothing renders before it was knowable (causality); mock/sample data always labelled; discretionary ≠ validated; no invented probabilities; execution is shadow-only (D6).

---

## 1. First batch of PyPI candidates (12) — evaluation

| Package | What it does | Verdict |
|---|---|---|
| **forex-pytory** 0.1.0 (Jun 2026, Apache-2.0) | Scrapes ForexFactory (+ crypto/energy/metals calendars) into Pydantic `EconomicEvent`; CLI and MCP server | **Pilot only.** Adds calendar context (DK15, high-impact-soon warning, event-day regime filter). Risks: scraping with `cloudscraper` (terms/fragility), one release, one maintainer, inconsistent import paths and version badge. Project already uses the faireconomy JSON feed in `data/fetch_calendar.py`. |
| **tickerflow** 0.2.5 (Aug 2026, MIT) | Async OHLCV `fetch()` with provider fallback chains and caching | **Borrow the pattern** (provider fallback + `feed.degraded` signalling). Forex only via yfinance/paid Finnhub, no bid/ask, so unusable for the Judge. Very young. |
| **technical-analysis** 0.0.7 (BSD-3) | pandas indicators, candlestick helpers, Hurst, autocorrelation, small backtester | **Test oracle only.** Docs contain errors; source repo not linked; do not use its backtester (one-referee rule). |
| **candlecraft** 0.2.0 (MIT) | OHLCV from Binance / Twelve Data + 10 indicators | Skip. Duplicates indicators; forex needs a Twelve Data key. Possible later use: independent price cross-check. |
| **QuantResearch** 2.5.3 (MIT, Alpha) | yfinance download, indicators, matplotlib charts | Skip. |
| **forex-data-extractor** 1.0.0 (MIT) | Playwright scrape of Yahoo Finance, close only | Skip. Close-only; scraping terms unclear. |
| **google-finance-scraper** 1.0.0 (MIT) | Google Finance scraper | **Reject.** First release, unofficial scraping, and the homepage link points to a GitHub account with a random-string name (supply-chain red flag). |
| **Forex-API** 0.1.3 (MIT) | "Small library to fetch forex data" | Reject. Looks like a homework package; import path does not match the package name. |
| **lightningchart-trader** 1.2.0 | Commercial charting library | **Rejected by owner:** needs a licence key. |
| **analysis-tool** 1.0.0 | LHCb particle-physics analysis toolkit (needs ROOT) | Irrelevant. |
| **genebot** 1.1.42 (MIT) | Live trading bot (crypto + OANDA/MT5/IBKR) | **Reject.** Execution bot that would hold broker keys; conflicts with shadow-only authority and the Judge. ~40 releases in 5 days, version inconsistencies, unsupported "production ready" claims. |
| **minimamba** 1.0.1 (MIT) | Pure-PyTorch Mamba (S6) implementation | **Keep for the Lab module** as a CPU-friendly challenger (single maintainer, ~12 tests, self-reported speed table; verify against the official implementation). "Production/Stable" is the author's own classifier. |

---

## 2. Module A — "Lab" (volatility / regime forecasting)

### 2.1 What the evidence says
- **Large benchmark of deep models on daily futures** (arXiv 2603.01820; commodities, equity indices, bonds, FX; 2010–2025): Mamba-family models (Mamba, Mamba2, VSN+Mamba2) performed "moderately" and inconsistently; LSTM/xLSTM hybrids did better (aggregated Sharpe: Mamba 0.64, Mamba2 0.78, VSN+Mamba2 1.10 vs VLSTM 2.40). Caveats: gross of costs; headline numbers average the top 10 of 50 seeds chosen by validation loss; the seed-robustness check did not include the Mamba models.
- **Foundation models** (Chronos, TimesFM, Moirai, TimeGPT): zero-shot performs poorly on finance (arXiv 2511.18578: negative out-of-sample R² for Chronos-large and TimesFM-500M on daily stock returns; finance-specific pre-training needed). arXiv 2606.27100: gains over a random walk are small and sparse, and the authors say it does not show reliable trading alpha.
- **Volatility specifically:** a crypto study (Zenodo 18148216, not peer-reviewed) found HAR/HAR-X generally more stable and competitive than an LSTM. HAN-Mamba (arXiv 2610.10323, Oct 2026) improves on its own earlier transformer on Optiver equity data (RMSPE 0.1965 → 0.1942, 33% fewer parameters) but names no HAR/GARCH baseline; code availability unknown.
- **Blog opinion** (Kinlay, Mar 2026): skeptical Mamba replaces transformers in high-frequency finance; mostly qualitative; no crisis-period testing seen.

### 2.2 Recommended stack
| Project | Role | Facts | Notes |
|---|---|---|---|
| **arch** (Kevin Sheppard) | GARCH/HAR/EWMA baselines; bootstrap; SPA, StepM, Model Confidence Set | v8.0.0, Oct 2025, NCSA licence, one maintainer | Baseline to beat; multiple-comparison tests fit the "variants tried" discipline. |
| **MAPIE** (scikit-learn-contrib) | Conformal prediction intervals → "calibrated" forecast contract | BSD-3, 1.6k stars; README claims time-series support | Which time-series methods exist **(unverified)**. |
| **Optuna** | Hyperparameter search | v5.0.0, Sep 2026, MIT | Every trial must count toward the ledger's variant total. |
| **MLflow** | Run/artifact tracking | 3.14, Jun 2026, Apache-2.0, Linux Foundation | Optional; ledger stays the verdict authority. |
| **state-spaces/mamba** (`mamba-ssm`) | Reference Mamba | 18.7k stars, Apache-2.0, v2.3.2.post1 (May 2026) | Linux + NVIDIA GPU + CUDA; no CPU fallback documented; Mamba-3 source-install only. |
| **minimamba** | CPU-friendly Mamba prototype | see §1 | Cross-check against the official code. |
| **neuralforecast** (Nixtla) | Baseline harness: NHITS, PatchTST, LSTM, TFT, iTransformer, etc. | v3.3.0, Oct 2026, Apache-2.0, 4.3k stars | **No Mamba model** in its list. |
| **Chronos-2** (Amazon) | Zero-shot baseline only | 120M params, Apache-2.0, CPU/GPU, covariates | Do not expect it to win. |
| **statsmodels `MarkovRegression`** | Regime switching | mature (docs found; release page not opened) | Preferred over hmmlearn. |
| **ruptures** | Change-point detection | BSD-2, 2.1k stars; latest release **(unverified)** | **Retrospective** — offline labelling only. |
| **hmmlearn** | HMM regimes | 0.3.3, Oct 2024, BSD, "limited-maintenance mode", Alpha classifier | Avoid; smoothed HMM states also use future data. |
| **purged-cross-validation** (`purgedcv`) | Purged k-fold, CPCV, deflated Sharpe, PBO | MIT, 24 stars, one author, JOSS draft, README discloses AI-assisted code | Cross-check only; the existing engine already has purged walk-forward. |

**Excluded:** TimesFM 3.0 (weights non-commercial; 2.5 and earlier are Apache-2.0 but older).

### 2.3 Causality rule
Change points and smoothed HMM states use future data. Use them only for offline labelling or research. Live features must use filtered (causal) probabilities and pass the `viewAsOf` no-lookahead test.

### 2.4 First experiment (pre-register before running)
Mamba volatility forecast versus HAR and GARCH (`arch`) on QLIKE, compared with a Model Confidence Set, using train/validation only, shuffled-label control, hyperparameter trials counted as variants. **Honest expectation:** it ties or loses; a documented tie is still a useful result.

### 2.5 What a trader can use it for
Volatility/range forecasts for stop width and position size; knowing when to avoid quiet or choppy conditions; judging whether a target is realistic today; event-risk context beside the calendar; a regime label on existing setups; and visible track record (interval coverage, variants tried, whether it beat the baseline). **Not** for buy/sell calls, direction probabilities, auto-trading, or anything labelled "validated" before the Judge says so.

---

## 3. Module B — standalone Trade-Assistant (TA, premarket, bot, paper trading)

Goal as stated: a separate module built from new reputable libraries, not reusing the existing detectors.

### 3.1 Honest framing
- **No high-authority SMC/ICT library exists.** The niche is small; the available libraries are small projects. The reputable parts of the stack are the infrastructure (data, charts, ML, LLM tooling, brokers).
- The earlier ICT-confluence test failed the Judge, so the assistant's suggestions are a disciplined checklist and a forward test, not a promise of profit.
- Premarket analysis on already-closed bars may use retrospective structure; anything used to **train a model or place paper trades must be causal**.

### 3.2 Stack by layer

**Data**
| Pick | Facts | Caveats |
|---|---|---|
| OANDA practice REST, direct via `httpx` | Free demo account, real spreads | Wrapper `oandapyV20` is stale (latest 0.7.2, Aug 2021) — skip it. |
| **tickterial** (Dukascopy ticks, MIT) | Ask/bid prices and volumes per tick; v1.1.2, Jun 2024; one maintainer | Only up to the previous hour; Dukascopy terms of use not verified. Optional. |
| Parquet + Polars/DuckDB | Standard columnar stack | Current versions not verified (only comparison articles read). |

**Technical analysis (price action, structure, ICT/SMC)**
| Pick | Facts | Caveats |
|---|---|---|
| **TA-Lib** (`TA_Lib` 0.8.2, Oct 2026, BSD-2) | Indicators + 61 `CDL*` candlestick patterns; wheels bundle the C library; one maintainer | Candle signals should count only near a level/zone. |
| **smart-money-concepts** (`joshyattridge`, MIT, 2.1k stars, 889 forks) | FVG, swings, BOS/CHoCH, order blocks (needs volume), liquidity, previous high/low, sessions, retracements; pandas in/out | "Educational purposes only"; newest commit seen is Mar 2024 (activity unconfirmed); swing logic uses candles on both sides → needs a causal wrapper that delays signals until confirmation. |
| **trendln** (MIT, 0.1.18, Apr 2026) | S/R trendlines, local extrema, Hough variants; one maintainer | Look-ahead behaviour unclear; metadata inconsistent. |
| smtlab/smartmoneyconcepts, smc-toolkit 0.1.0, pandas-ta-classic | Small forks / unknown author / community fork | Skip (10-star fork; unnamed author; unverified upstream). |
| TradingView / LuxAlgo open-source scripts | Reference definitions | Read for definitions only; licences not checked. |

**Premarket visuals**
| Pick | Facts | Caveats |
|---|---|---|
| TradingView **Lightweight Charts (JS)** via a small FastAPI page | Official library; plugin primitives can draw boxes/lines/labels | Needs a small web layer. |
| **lightweight-charts-python** (MIT, one maintainer) | Pythonic wrapper; DataFrame in; trendline/ray/horizontal tools; Jupyter, Streamlit, PyQt | Independent of TradingView; newest release seen 2.1 (Sep 2024); box drawing not confirmed. |
| **Plotly** | Rectangles for OB/FVG; static PDF/PNG for a daily brief | Not live. |

**Bot / AI**
| Layer | Pick | Notes |
|---|---|---|
| Scoring model | **LightGBM + SHAP**, triple-barrier labels + meta-labeling ("should we act on this setup?") | `mlfinpy` implements triple-barrier, meta-labeling, trend scanning, but licence/maintenance not stated on the page I read; triple-barrier is simple to implement ourselves. Use time-ordered splits with a gap. |
| LLM analyst | **Pydantic AI** (one source favours it for typed output and replayable runs); or the Anthropic SDK directly | Single-source comparison; LangGraph not evaluated. Analyst reads structured outputs and writes the premarket brief and rationale; it does not read screenshots or pick trades. |
| Design reference | **TradingAgents** (TauricResearch, Apache-2.0, v0.7.0; page shows ~113k stars) | Multi-agent firm with bull/bear debate; US-stock data (SEC EDGAR, Yahoo, FRED); simulated exchange; "research purposes only"; no backtest results shown. Borrow structure, not code. |
| Other agents | **QuantAgent** (MIT, 2.9k stars): vision-based chart reading; yfinance; no forex or paper trading stated; no results shown. **AgenticTrading** (OpenMDW licence, 547 stars): paper trading looks like a stub. **FinRL**: stocks/crypto, forex not mentioned. | Skip. |

**Paper trading**
| Option | Facts | Verdict |
|---|---|---|
| **OANDA practice account** | Official demo; `oanda/v20-python-samples` (MIT) shows market/limit/stop/TP/SL orders | First choice for FX. |
| **ib_async** (BSD-2, v2.1.0, Dec 2025, 1.8k stars, "Production/Stable") | Successor to `ib_insync`; one maintainer; needs TWS/IB Gateway running; forex supported | Second broker option. |
| **cTrader OpenApiPy** (MIT, 189 stars) | Demo host supported; Twisted-based | Order placement not confirmed on the page. |
| Internal simulator | Fills from live bid/ask + slippage; deterministic and replayable | Build first. |
| NautilusTrader (LGPL-3.0, 1.231.0, Aug 2026, Rust core, Python ≥3.12) | No OANDA adapter or sandbox mode found on its page | Skip for now (heavy). |
| Lumibot (GPL-3.0, 4.6.30) | Paper trading documented for Alpaca only; OANDA not confirmed | Skip (GPL; broker fit). |
| Freqtrade | Dry-run exists; crypto-focused; no reliable page opened | Skip. |
| backtrader / vectorbt / backtesting.py | backtrader original stopped ~2018; vectorbt development reportedly focused on PRO; backtesting.py single-instrument | Not for paper trading. |

### 3.3 Proposed architecture
Data feed → causal TA layer → premarket chart + brief → scoring model + LLM analyst → suggestion with evidence links → `PaperBroker` (internal simulator **or** OANDA practice **or** IB paper) → decision/audit log → scorecard.

### 3.4 Guardrails
1. Suggestions carry evidence, track record and a "not validated by the Judge" label.
2. **Freeze and pre-register the suggestion rules before the paper run**; tuning on paper results contaminates the forward test.
3. Paper only. Daily-loss halt, max concurrent trades, news blackout, kill switch, idempotent order IDs.
4. Every decision is logged and replayable.
5. Pin dependencies; run `pip-audit`; many projects here are single-maintainer.

---

## 4. Licences to watch
| Project | Licence | Note |
|---|---|---|
| Lumibot | GPL-3.0 | Copyleft; avoid linking into proprietary code. |
| NautilusTrader | LGPL-3.0-or-later | Importing is generally fine; check obligations. |
| TimesFM 3.0 weights | Non-commercial | Avoid. |
| arch | NCSA | Permissive. |
| ib_async | BSD-2 (PyPI classifier shows "Other/Proprietary (BSD)") | Confirm text. |
| AgenticTrading | OpenMDW-1.0 | Unfamiliar; read before use. |
| lightningchart-trader | Commercial | Rejected. |

---

## 5. Open items / not verified
- Last-commit and release dates for most GitHub projects (pages did not show them).
- Whether `smartmoneyconcepts` is actively maintained today; confirm look-ahead behaviour in `smc.py`.
- MAPIE's specific time-series methods; ruptures' latest release; mlfinpy's licence.
- Dukascopy terms of use; ForexFactory scraping terms; licences on TradingView/LuxAlgo scripts.
- Current versions of Polars, DuckDB, LightGBM, SHAP, Plotly.
- Whether lightweight-charts-python can draw boxes; cTrader OpenApiPy order placement.
- The Lab module's goal (volatility/regime forecasting was assumed; the owner has not confirmed).

---

## 6. Suggested next steps
1. Confirm the Lab module's goal (volatility/regime recommended).
2. Sandbox spike on `forex-pytory` versus the existing calendar feed (compare a few weeks of events, timezones, fields).
3. Write the design + phase docs for (a) the Lab module and (b) the standalone Trade-Assistant (contracts, layers, phases, tests), in the style of the existing `docs/` suite.
4. Tighten foundations first where possible: provider abstraction, negative-control oracles (E3), `dataVersion` in the ledger (E4).

---

## 7. Sources
- Packages from the first batch: [Forex-API](https://pypi.org/project/Forex-API/) · [forex-data-extractor](https://pypi.org/project/forex-data-extractor/) · [candlecraft](https://pypi.org/project/candlecraft/) · [google-finance-scraper](https://pypi.org/project/google-finance-scraper/) · [forex-pytory](https://pypi.org/project/forex-pytory/) · [tickerflow](https://pypi.org/project/tickerflow/) · [lightningchart-trader](https://pypi.org/project/lightningchart-trader/) · [technical-analysis](https://pypi.org/project/technical-analysis/) · [analysis-tool](https://pypi.org/project/analysis-tool/) · [genebot](https://pypi.org/project/genebot/) · [minimamba](https://pypi.org/project/minimamba/) · [QuantResearch](https://pypi.org/project/QuantResearch/)
- Lab: [state-spaces/mamba](https://github.com/state-spaces/mamba) · [mamba-ssm](https://pypi.org/project/mamba-ssm/) · [arch](https://pypi.org/project/arch/) · [neuralforecast](https://pypi.org/project/neuralforecast/) · [Nixtla/neuralforecast](https://github.com/Nixtla/neuralforecast) · [Chronos-2](https://huggingface.co/amazon/chronos-2) · [TimesFM](https://github.com/google-research/timesfm) · [MAPIE](https://github.com/simai-ml/MAPIE) · [ruptures](https://github.com/deepcharles/ruptures) · [hmmlearn](https://pypi.org/project/hmmlearn) · [purged-cross-validation](https://github.com/eslazarev/purged-cross-validation) · [Optuna](https://simple-repository.app.cern.ch/project/optuna) · [MLflow](https://aiwiki.ai/wiki/mlflow)
- Papers/posts: [arXiv 2603.01820](https://arxiv.org/abs/2603.01820) · [arXiv 2606.27100](https://arxiv.org/abs/2606.27100) · [arXiv 2511.18578](https://arxiv.org/pdf/2511.18578) · [Zenodo 18148216](https://zenodo.org/records/18148216) · [arXiv 2610.10323](https://arxiv.org/abs/2610.10323) · [Kinlay](https://jonathankinlay.com/2026/03/state-space-models-for-market-microstructure-can-mamba-replace-transformers-in-high-frequency-finance/)
- Trade-Assistant: [smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts) · [commit e09adc3](https://github.com/joshyattridge/smart-money-concepts/commit/e09adc3b20d6b9c5461d409270a43572b7d24dc1) · [smtlab fork](https://github.com/smtlab/smartmoneyconcepts) · [smc-toolkit](https://www.piwheels.org/project/smc-toolkit/) · [TA-Lib](https://pypi.org/project/TA_Lib/) · [trendln](https://pypi.org/project/trendln/) · [lightweight-charts (PyPI)](https://www.pypi.org/project/lightweight-charts/1.0.17/) · [lightweight-charts-python docs](https://docsearch.algolia.com/mcp/docs/repo/louisnw01/lightweight-charts-python) · [tickterial](https://pypi.org/project/tickterial) · [oandapyV20](https://www.pypi.org/project/oandapyV20/0.5.0/) · [oanda/v20-python-samples](https://github.com/oanda/v20-python-samples) · [ib_async (PyPI)](https://pypi.org/project/ib_async) · [ib_async (GitHub)](https://github.com/ib-api-reloaded/ib_async) · [cTrader OpenApiPy](https://github.com/spotware/OpenApiPy) · [mlfinpy](https://mlfinpy.readthedocs.io/en/stable/_sources/Labelling.rst.txt) · [TradingAgents](https://github.com/TauricResearch/TradingAgents) · [QuantAgent](https://github.com/Y-Research-SBU/QuantAgent) · [AgenticTrading](https://github.com/Open-Finance-Lab/AgenticTrading) · [awesome-trading-agents](https://github.com/LLMQuant/awesome-trading-agents) · [FinRL](https://docsearch.algolia.com/mcp/docs/repo/ai4finance-foundation/finrl) · [NautilusTrader](https://www.pypi.org/project/nautilus_trader) · [Lumibot](https://pypi.org/project/lumibot/) · [backtesting library comparison](https://algolab.co.kr/blog/python-backtesting-library-comparison-2026) · [Claude Agent SDK vs Pydantic AI](https://www.mindstudio.ai/blog/agent-sdk-vs-framework-claude-pydantic-ai-production)
