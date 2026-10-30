"""Analyst commands (Phase 9C-1). Run from the repo root:

  python -m sx_assistant.analyst.run check             # keys, approvals, model lists (no brief)
  python -m sx_assistant.analyst.run status            # saved state: cooldowns, usage estimates
  python -m sx_assistant.analyst.run reset --provider groq   # forget a provider's saved state
  python -m sx_assistant.analyst.run brief --fake      # whole pipeline offline, no network
  python -m sx_assistant.analyst.run brief             # real providers, frozen sample data

Output goes to ``assistant/outputs/analyst/`` (gitignored): ``brief_<hash>.json``, ``state.db``
(cooldowns and usage estimates) and ``routing.jsonl`` (provider, model, outcome, latency, tokens;
never keys or prompts). A brief for an unchanged packet is reused; add ``--force`` to call again.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sx_assistant.analyst.config import (ApprovalError, ProviderSetup, build_providers,
                                         load_approved, load_env)
from sx_assistant.analyst.errors import ProviderError
from sx_assistant.analyst.packet import build_packet
from sx_assistant.analyst.providers.fake import FakeProvider, echo_reply
from sx_assistant.analyst.service import AnalystService
from sx_assistant.analyst.state import SqliteState
from sx_assistant.premarket.builder import build_premarket
from sx_assistant.premarket.data_source import FixtureSource
from sx_core.config import load_settings

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "assistant" / "outputs" / "analyst"


def _real_setup(require_confirmed: bool) -> ProviderSetup:
    settings = load_settings(dotenv_path=ROOT / ".env")
    return build_providers(settings, load_env(ROOT / ".env"), require_confirmed=require_confirmed)


def cmd_check() -> int:
    try:
        setup = _real_setup(False)
    except ApprovalError as e:
        print(f"REFUSED: {e}")
        return 2
    for pid, why in setup.skipped.items():
        print(f"{pid}: skipped, {why}")
    approved = load_approved()
    for p in setup.providers:
        s = p.spec
        confirmed = approved[(s.provider_id, s.model_id)].get("owner_confirmed_free")
        print(f"{s.provider_id}: model {s.model_id!r}, owner_confirmed_free={confirmed}")
        try:
            names = p.list_models()
        except ProviderError as e:
            print(f"  could not list models: {e.kind}: {e}")
            continue
        print(f"  key accepted; {len(names)} models visible; "
              f"configured model {'IS' if s.model_id in names else 'is NOT'} among them")
    return 0


def cmd_status() -> int:
    st = AnalystService(OUT, _real_setup).status()
    if st["status"] != "ok":
        print(f"{st['status'].upper()}: {st.get('error')}")
        return 2
    for r in st["providers"]:
        if not r["key_present"]:
            print(f"{r['provider']}: {r['note']}")
            continue
        print(f"{r['provider']}/{r['model']}: {r['health']}, confirmed_free="
              f"{r['owner_confirmed_free']}, requests today ~{r['requests_today_estimate']}"
              f"/{r['daily_cap']}, tokens ~{r['tokens_today_estimate']}, cooldown "
              f"{r['cooldown_remaining_s']}s" + (f", {r['disabled_reason']}"
                                                if r["disabled_reason"] else ""))
    print(st["note"])
    return 0


def cmd_reset(provider: str) -> int:
    n = SqliteState(OUT / "state.db").reset(provider)
    print(f"Forgot saved state for {provider!r} ({n} row(s)).")
    return 0


def cmd_brief(fake: bool, force: bool) -> int:
    src = FixtureSource()
    inst = src.instruments()[0]
    packet = build_packet(build_premarket(src, inst, src.last_close(inst)))
    if fake:
        svc = AnalystService(OUT / "fake", lambda _c: ProviderSetup(
            [FakeProvider("fake", [echo_reply(packet)] * 2)]))
    else:
        svc = AnalystService(OUT, _real_setup)
    res = svc.generate(packet, force=force)
    for a in res.get("attempts", []):
        print(f"  {a['provider']}/{a['model']}: {a['outcome']}"
              + (f" ({a['detail']})" if a["detail"] else ""))
    if res["status"] != "published":
        print(f"{res['status'].upper()}: {res.get('reason', '')}")
        return 1
    b = res["brief"]
    n_un = sum(c["status"] == "unverified" for c in b["claims"])
    print(f"PUBLISHED{' (reused, no call made)' if res['reused'] else ''} by "
          f"{b['writer']['provider']}/{b['writer']['model']}: {len(b['claims'])} claims, "
          f"{n_un} unverified. Labels: {', '.join(b['labels'])}. Folder: {svc.dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sx-analyst")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("status")
    r = sub.add_parser("reset")
    r.add_argument("--provider", required=True)
    b = sub.add_parser("brief")
    b.add_argument("--fake", action="store_true", help="offline echo provider, no network")
    b.add_argument("--force", action="store_true", help="call again even if a brief is saved")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return cmd_check()
    if a.cmd == "status":
        return cmd_status()
    if a.cmd == "reset":
        return cmd_reset(a.provider)
    return cmd_brief(a.fake, a.force)


if __name__ == "__main__":
    sys.exit(main())
