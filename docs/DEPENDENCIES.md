# Dependencies

Every library: version, licence, reason, last check. Nothing here has been installed or audited yet. Before adopting: sandbox install, `pip-audit`, licence review, pin the version.

## Web (adopted for the UI)
| Package | Why | Licence | Checked |
|---|---|---|---|
| react, react-dom | UI | MIT | - |
| vite | Build | MIT | - |
| tailwindcss | Styling | MIT | - |
| lightweight-charts | Candlestick chart | Apache-2.0 | - |
| @radix-ui/* | Accessible primitives | MIT | - |
| cmdk | Command palette | MIT | - |
| zustand | UI state | MIT | - |
| @tanstack/react-query | API data | MIT | - |
| zod | Contract validation | MIT | - |
| vitest, playwright | Tests | MIT / Apache-2.0 | - |

### Installed in Phase 1 (checked 2026-10-26 in the sandbox; licences from package metadata not yet reviewed)
zustand 5.0.16, zod 4.6.7, cmdk 1.1.1, vitest 3.2.7 (pinned ^3: Vitest 5 needs Vite 6+), jsdom 30.1.3, @testing-library/react, jest-dom, user-event, @playwright/test 1.64.1 (browser not installed in the sandbox), eslint 10.13.0, typescript-eslint 8.72.0, eslint-plugin-react-hooks 7.1.1, @types/node 22. `npm audit` reports 8 dev-tooling vulnerabilities; see Known issues in the plan. Radix and TanStack Query are not installed yet.

## Python adopted in Phase 2 (checked 2026-10-26 in the sandbox, Python 3.12.3; `pip-audit` found nothing in these)
| Package | Pinned | Licence (package metadata) | Used by |
|---|---|---|---|
| pydantic | 2.14.1 | MIT | core contracts, config |
| pandas | 3.1.0 | BSD-3-Clause | core storage |
| pyarrow | 26.0.0 | Apache-2.0 | core storage (Parquet) |
| numpy | 2.5.4 | BSD-3-Clause and others (0BSD, MIT, Zlib, CC0) | core storage hashing |
| pytest (dev) | 9.1.1 | MIT | tests |
| ruff (dev) | 0.17.2 | MIT | lint |

Licences come from package metadata and have not had a legal review. mypy was used once as a check and is not adopted.

## Python adopted in Phase 3 (checked 2026-10-26 in the sandbox, Python 3.12.3)
| Package | Pinned | Licence (package metadata) | Used by |
|---|---|---|---|
| httpx | 0.28.1 | BSD-3-Clause | `sx_data.oanda_rest` (OANDA practice REST) |

httpx brings anyio, certifi, httpcore, idna (and h11, sniffio). `pip-audit` on the installed packages found nothing except the venv's own `pip` 24.0. `httpx.MockTransport` is what the tests use; no mocking library was added. mypy was run once as a check (`--strict` on `core/src` and `data/src`, no issues) and is still not adopted.

**Python version finding (resolved 2026-10-27, X9):** `numpy==2.5.4` requires Python 3.12 or newer (PyPI `requires_python >=3.12`; wheels for cp312 to cp315 including macOS arm64). The minimum is now 3.12 in `core`, `data`, `assistant` and the ruff target.

The OANDA request and response shapes in `sx_data/oanda_parse.py` and `oanda_rest.py` come from memory of OANDA's v20 docs and were **not** checked against the live API.

## Python adopted in Phase 4 (checked 2026-10-27 in the sandbox, Python 3.12.3, fresh venv; `pip-audit` found nothing except the venv's own `pip` 24.0)
| Package | Pinned | Licence (package metadata) | Used by | Flags |
|---|---|---|---|---|
| smartmoneyconcepts | 0.0.27 (install with `pip install --no-deps smartmoneyconcepts==0.0.27`) | not declared in PyPI metadata (check the repository before relying on it) | `ta/smc_adapter.py` | **Declares numba but never imports it** (grep of its source), so it is installed `--no-deps`; numba 0.68 and llvmlite 0.50 have no Intel-Mac wheels, and building llvmlite needs LLVM. Single maintainer. Prints a promotional banner on import (the adapter silences it). Not causal as shipped: see `smc_adapter.py`. Last release 2026-04-03 |
| TA-Lib | 0.8.2 | not declared in PyPI metadata (the C library is BSD-3-Clause; check) | `ta/candles_talib.py` | Binary wheels exist for cp311 to cp315 on Linux, macOS arm64/x86_64 and Windows, so no system library is needed. **Installed and tested on Linux x86_64 only.** The owner's Mac is Intel (x86_64): pip downloaded `ta_lib-0.8.2-cp314-cp314-macosx_13_0_x86_64.whl` there |
| trendln (extra `retro`) | 0.1.18 | MIT | `ta/levels_trendln.py` | Optional. Heavy: pulls scipy 1.18.1, scikit-image 0.26.0, matplotlib 3.11.2, sympy 1.14.0, findiff 0.16.0, networkx, pillow and more (transitive versions are not pinned by us). Retrospective only; about 0.3 s on 96 bars |

smartmoneyconcepts, TA-Lib and trendln source or behaviour was read or run before adoption: the SMC source was read function by function (`swing_highs_lows`, `bos_choch`, `fvg`, `ob`, `liquidity`); trendln's return value was read from its source and confirmed by running it; TA-Lib candle functions were verified only through the causality harness and the labelled candle fixture. The library list "planned" below keeps the rest.

## Python (planned, not yet installed)
| Package | Module | Why | Flags |
|---|---|---|---|
| lightgbm, shap | assistant | Setup scorer | - |
| arch | lab | GARCH, HAR, MCS | One maintainer |
| minimamba | lab | CPU Mamba challenger | Single maintainer, ~12 tests, unverified vs reference |
| neuralforecast | lab | Baseline models | Heavy |
| MAPIE | lab | Conformal intervals | Time-series support unverified |
| optuna | lab | Search; every trial logged | - |
| statsmodels | lab | Markov switching (filtered probabilities only) | - |
| fastapi, uvicorn | api | Service | - |
| ib_async | assistant | IB paper backend | One maintainer; needs TWS/Gateway |

Source: `docs/research/SPEKRYM_NEW_MODULES_RESEARCH.md`.

## Phase 5A (2026-10-27)
`apps/api/pyproject.toml` pins `fastapi==0.162.0` and `uvicorn==0.54.0` (versions installed and exercised in the sandbox, Python 3.12.3; starlette 1.10.0 came with fastapi). `sx-assistant` now depends on `sx-data` (for `resample`). Not run through `pip-audit`. The test client warns that `httpx` use is deprecated in favour of `httpx2`; not acted on.

## Phase 5B (2026-10-27)
Web: `@tanstack/react-query` ^5 (installed 5.105.0). Python extra `assistant[report]`: `plotly==7.1.0`, `kaleido==1.5.0` (installed and exercised in the sandbox for figure building and HTML export only). kaleido 1.x needs Google Chrome for PNG/PDF; the sandbox has none, so PNG/PDF export is NOT verified there. Not run through `pip-audit` or `npm audit`.

## Python adopted in Phase 7B (checked 2026-10-27 in the sandbox, Python 3.12.3; `pip-audit` found nothing except the venv's own `pip` 24.0)
| Package | Pinned | Licence (package metadata, no legal review) | Used by |
|---|---|---|---|
| arch | 8.0.0 | NCSA (metadata field; no classifier) | `sx_lab.baselines.garch` (parameter estimation only) |
| optuna | 5.0.0 | MIT (classifier) | `sx_lab.search.optuna_search` |

Transitive and NOT pinned by us: scipy 1.18.1, statsmodels 0.15.0 (via arch); SQLAlchemy 2.1.6, alembic 1.20.1, colorlog, tqdm, PyYAML (via optuna). Optuna's database stack is heavier than this use needs (in-memory study only); swap for an in-house grid search if that bothers you. Source reading was partial (see PROGRESS 7B).
