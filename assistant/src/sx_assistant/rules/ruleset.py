"""Rule sets, their content hash, and the freeze lock.

The hash is taken over the canonical JSON of the parsed rules, so whitespace or key order
in the file does not matter but any value does. ``freeze`` writes ``<file>.lock`` once; it
refuses to overwrite a lock with a different hash. A changed rule needs a NEW rule file
(new ``version``) and a new run, never an edited one.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from pydantic import Field, model_validator

from sx_core.contracts._base import Contract, UtcDatetime


class RulesError(Exception):
    """Rules are missing a lock, changed since freezing, or invalid."""


class Blackout(Contract):
    """A news blackout window, UTC, ``[start, end)``. Listed by hand: there is no calendar feed."""

    label: str = Field(min_length=1)
    start: UtcDatetime
    end: UtcDatetime

    @model_validator(mode="after")
    def _ordered(self) -> Blackout:
        if self.end <= self.start:
            raise ValueError("blackout end must be after start")
        return self


class RuleSet(Contract):
    version: str = Field(min_length=1)
    max_open_trades: int = Field(ge=1)
    daily_loss_limit: float = Field(gt=0)  # quote currency, realized losses per UTC day
    blackouts: list[Blackout] = Field(default_factory=list)


def load_rules(path: str | Path) -> RuleSet:
    try:
        return RuleSet.model_validate_json(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise RulesError(f"cannot load rules from {path}: {exc}") from exc


def rules_hash(rules: RuleSet) -> str:
    canon = json.dumps(json.loads(rules.model_dump_json()), sort_keys=True,
                       separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode()).hexdigest()


def lock_path(path: str | Path) -> Path:
    return Path(str(path) + ".lock")


def freeze(path: str | Path) -> str:
    """Write the lock for these rules. Refuses to change an existing lock."""
    h = rules_hash(load_rules(path))
    lock = lock_path(path)
    if lock.exists():
        if lock.read_text().strip() != h:
            raise RulesError("already frozen with a different hash; make a new version file")
        return h
    lock.write_text(h + "\n")
    return h


def verify_frozen(path: str | Path) -> tuple[RuleSet, str]:
    """Return the rules and their hash, or raise if there is no lock or the hash differs."""
    rules = load_rules(path)
    lock = lock_path(path)
    if not lock.exists():
        raise RulesError(f"rules are not frozen (no {lock.name}); refusing to run")
    h = rules_hash(rules)
    if lock.read_text().strip() != h:
        raise RulesError("rules changed since they were frozen; refusing to run")
    return rules, h


def rules_version(rules: RuleSet, h: str) -> str:
    return f"{rules.version}-{h[:12]}"


if __name__ == "__main__":  # python -m sx_assistant.rules.ruleset freeze <file>
    if len(sys.argv) == 3 and sys.argv[1] == "freeze":
        print(freeze(sys.argv[2]))
    else:
        raise SystemExit("usage: python -m sx_assistant.rules.ruleset freeze <rules.json>")
