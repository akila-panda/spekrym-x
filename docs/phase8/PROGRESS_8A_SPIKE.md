
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
