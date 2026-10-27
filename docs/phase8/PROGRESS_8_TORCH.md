
## Phase 8A feasibility result: PyTorch on the owner's Mac (2026-10-27)

- Owner ran on the Mac (Intel x86_64, Python 3.14.3, `.venv`): `python -m pip install torch --dry-run` → `Could not find a version that satisfies the requirement torch (from versions: none)`. **PyTorch cannot be installed in the project venv.**
- Claude checked PyPI metadata from the sandbox (2026-10-27): torch 2.14.1 is the latest; releases 2.12.0 to 2.14.1 publish macOS wheels for Python 3.12 to 3.14 but **none for Intel macOS** (no x86_64 or universal2 wheels). The newest release with an Intel-Mac wheel is **2.2.2**, built for Python 3.8 to 3.12 only.
- Consequence: on this Mac, torch would need Python 3.12 and 2.2.2, which was built before numpy 2 and conflicts with the repo's pins (numpy 2.5.4, pandas 3.1.0). I did NOT test whether torch 2.2.2 plus numpy 1.x runs at all, nor whether `minimamba` works with it. Running the challengers locally is therefore not recommended.
- Not verified: that `minimamba` itself installs and runs anywhere; that the sandbox has enough CPU time for EXP-001.
