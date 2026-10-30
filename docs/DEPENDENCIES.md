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

## Python adopted in Phase 8A (checked 2026-10-27 in the sandbox, Python 3.12.3; `pip-audit` NOT run)
| Package | Pinned | Licence (package metadata) | Used by | What was actually checked |
|---|---|---|---|---|
| statsmodels | 0.15.0 | BSD-3-Clause | `lab/regime/markov_switching.py` | By running: `MarkovRegressionResults` has no `apply`; `MarkovRegression(new_y).filter(params)` returns filtered marginal probabilities that equal the prefix results (Phase 2 harness test); default start values gave a degenerate fit, so start values are set from the data. Source not read beyond this |
| ruptures | 1.1.10 (optional extra `crosscheck`, Python < 3.14 only) | BSD-2-Clause | tests only | **NOT installable on the owner's Python 3.14.3** (requires < 3.14; the 1.1.11rc1 pre-release allows only `<=3.14`, which excludes 3.14.x). Found by the owner's `pip install -e lab` on 2026-10-27. Replaced in `changepoints_offline.py` by an in-house exact PELT (L2 cost), tested against brute force. In the sandbox ruptures matched it in 117 of 120 random cases; in the other 3 the in-house result had a strictly lower objective, so ruptures' pruning is not exact with `min_size` |
| PyYAML | 6.0.3 | MIT | `lab/spec.py` (`safe_load` only) | Behaviour of `safe_load` and `safe_dump` used in tests |
| arch (MCS part) | 8.0.0 (already pinned) | NCSA (metadata) | `lab/evaluation/model_confidence_set.py` | `MCS.__init__` source read: bootstrap indices drawn once at construction (seed deterministic), default block `int(sqrt(T))`, needs 2+ columns. A known-answer run excludes a clearly worse model |

On the owner's Mac (Intel, Python 3.14.3): statsmodels 0.15.0 installed (pip reported it satisfied); ruptures failed as described; PyYAML 6.0.3 was not reached by that pip run and is unconfirmed. PyTorch/minimamba remain outside the repo venv (conda-forge env, see the 8A feasibility notes).

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

## Phase 9A (checked 2026-10-28 in the sandbox, Linux x86_64, Python 3.12.3)
| Package | Pinned | Licence (metadata, no legal review) | Used by | What I checked |
|---|---|---|---|---|
| lightgbm | 4.7.0 | MIT (not in the wheel metadata field; unconfirmed) | `model/train_lgbm.py` | Native `lgb.train` with `num_threads=1, deterministic=True, force_row_wise=True`: two fits on the same data gave identical predictions. Wheel `py3-none-macosx_10_15_x86_64` exists. The macOS wheel may need `libomp` (`brew install libomp`) at import time: UNCONFIRMED on the owner's Mac. |
| shap | 0.54.1 | MIT | `model/explain_shap.py` | Wheel `cp312-abi3-macosx_10_13_x86_64` exists (covers 3.12 to 3.14). It does NOT require numba (requires cloudpickle, numpy, packaging, pandas, scikit-learn, scipy, slicer, tqdm). For a binary LightGBM booster, `TreeExplainer.shap_values` returned an (n, features) array on the raw-margin scale, and base + sum of contributions equalled the booster's raw score; it also matched LightGBM's own `pred_contrib`. It prints a warning about "a list of ndarray" that is wrong for this version; the adapter silences exactly that message and re-checks shape and additivity on every call. |

Intel-Mac cp314 wheels were confirmed to exist (by `pip download --platform`, not by installing on a Mac) for scikit-learn 1.9.1, scipy 1.18.1, numpy 2.5.4 and pandas 3.1.0. Pure-Python transitive packages: slicer 0.0.8, cloudpickle 3.1.2, narwhals 2.28.0, tqdm 4.70.1. Transitive packages are not pinned by us. Not run through `pip-audit`. Source reading of both libraries was limited to the behaviour above, not their internals. Install with `pip install -e "assistant[dev,model]"` (new extra `model`).



## Phase 9C-1 (analyst), 2026-10-28
| Item | Version | Licence | Notes |
|---|---|---|---|
| httpx | 0.28.1 (already pinned by `data`; now also listed in `assistant`) | BSD-3-Clause | Direct HTTPS calls to the two providers; no vendor SDK is used. |
| Groq API (OpenAI-compatible) | base `https://api.groq.com/openai/v1` | service terms, not reviewed | Endpoint paths and the 429 `retry-after` / `x-ratelimit-*` headers were read from Groq docs on 2026-10-28; request parameter `max_completion_tokens` and the reply shape are the OpenAI-compatible ones and are UNVERIFIED against the live API. Groq's rate-limit page lists Developer-plan limits only. |
| Gemini API | `https://generativelanguage.googleapis.com/v1beta`, header `x-goog-api-key` | service terms, not reviewed | Endpoint and header read from Google docs on 2026-10-28; `systemInstruction`, `generationConfig` and `usageMetadata` names are UNVERIFIED against the live API. Free-tier limits and data-use terms not reviewed. |
No Anthropic SDK, Pydantic AI, Cloudflare or OpenRouter dependency was added.
