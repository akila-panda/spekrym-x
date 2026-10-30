"""Phase 9B: suggestions engine, evidence rules, gate view (synthetic fixtures only)."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from sx_assistant.model.features import FEATURE_NAMES, build_rows
from sx_assistant.model.labels_triple_barrier import label_rows
from sx_assistant.model.protocol import ProtocolSpec, ScorerPartition
from sx_assistant.model.scorer import Scorer
from sx_assistant.model.train_lgbm import fit, margin
from sx_assistant.rules.ruleset import RulesError, freeze
from sx_assistant.suggestions.engine import build_suggestions
from sx_assistant.suggestions.evidence import EvidenceError, make_reason, validate_suggestion
from sx_assistant.suggestions.gates_view import NO_STATE
from sx_core.contracts import (Candle, Forecast, Interval, ModelRef, Setup, TrackRecord)
from sx_core.storage import candles_to_frame

FX = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "model"
FEATS = list(FEATURE_NAMES)
PARAMS = {"num_leaves": 4, "min_data_in_leaf": 10, "num_boost_round": 30}
RULES = {"version": "paper-test", "max_open_trades": 2, "daily_loss_limit": 100.0, "blackouts": []}


@pytest.fixture(scope="module")
def world():
    candles = [Candle(**d) for d in json.loads((FX / "candles_h1_1800.json").read_text())]
    setups = [Setup(**d) for d in json.loads((FX / "setups_synthetic.json").read_text())]
    spec = ProtocolSpec(min_rows_per_split=30)
    rows = build_rows(setups, candles, spec.barrier)
    rows = rows.join(label_rows(rows, candles_to_frame(candles), spec.barrier), how="inner")
    part = ScorerPartition(rows, len(candles), spec, "dv:test")
    tr, va = part.train(), part.validation()
    model = fit(tr[FEATS], tr["label"].to_numpy(), PARAMS, 1)
    return candles, setups, Scorer(model, margin(model, va[FEATS]))


def _rules(tmp_path, **over):
    p = tmp_path / f"{over.get('version', RULES['version'])}.json"
    p.write_text(json.dumps({**RULES, **over}))
    freeze(p)
    return p


def _first_hit(world, rules, **kw):
    candles, setups, scorer = world
    for k in range(len(candles) - 1, len(candles) - 200, -1):
        as_of = candles[k].time + timedelta(hours=1)
        res = build_suggestions(setups, candles, scorer, rules, as_of=as_of, **kw)
        if res.suggestions:
            return res, as_of
    raise AssertionError("no suggestion found in the last 200 bars of the fixture")


def test_every_claim_resolves_and_levels_follow_the_side(world, tmp_path):
    res, as_of = _first_hit(world, _rules(tmp_path))
    for s in res.suggestions:
        ids = set(s.setup_ids)
        assert ids <= set(res.evidence) and len(s.reasons) >= 2
        assert all(r.evidence_id in ids for r in s.reasons)
        assert s.status == "not_validated" and 0 <= s.score <= 100 and s.created_at == as_of
        assert (s.stop < s.entry < s.target) if s.side == "long" else (s.target < s.entry < s.stop)
        assert {g.name for g in s.gates} == {"news_blackout", "max_open_trades", "daily_loss_halt"}
        assert s.rules_version.startswith("paper-test-")
        assert res.scored[s.id].labels and res.evidence[s.setup_ids[0]].known_at <= as_of


def test_prefix_equality_same_answer_on_truncated_history(world, tmp_path):
    candles, setups, scorer = world
    rules = _rules(tmp_path)
    res, as_of = _first_hit(world, rules)
    cut = [c for c in candles if c.time + timedelta(hours=1) <= as_of]
    again = build_suggestions(setups, cut, scorer, rules, as_of=as_of)
    assert [(s.id, s.entry, s.stop, s.target) for s in again.suggestions] == [
        (s.id, s.entry, s.stop, s.target) for s in res.suggestions]


def test_unknown_evidence_and_probability_wording_are_rejected(world, tmp_path):
    res, _ = _first_hit(world, _rules(tmp_path))
    s = res.suggestions[0]
    with pytest.raises(EvidenceError, match="no evidence"):
        make_reason("A claim", "setup:doesnotexist", set(res.evidence))
    with pytest.raises(EvidenceError, match="probability"):
        make_reason("A high chance of working", s.setup_ids[0], set(res.evidence))
    bad = s.model_copy(update={"reasons": [*s.reasons, s.reasons[0].model_copy(
        update={"evidence_id": "setup:other"})]})
    with pytest.raises(EvidenceError, match="not one of"):
        validate_suggestion(bad, set(res.evidence) | {"setup:other"})
    with pytest.raises(EvidenceError, match="at least one reason"):
        validate_suggestion(s.model_copy(update={"reasons": []}), set(res.evidence))


def test_forecast_adds_a_linked_claim_and_must_be_causal(world, tmp_path):
    rules = _rules(tmp_path)
    res, as_of = _first_hit(world, rules)

    def fc(issued):
        return Forecast(id="fc:test", instrument="EUR_USD", tf="H1", issued_at=issued,
                        horizon_end=issued + timedelta(hours=24), target="realized_vol", point=1.0,
                        interval=Interval(low=0.5, high=1.5, nominal_coverage=0.8),
                        model=ModelRef(name="x", version="1", params_hash="h"),
                        track_record=TrackRecord(n=0, empirical_coverage=0.0, variants_tried=0),
                        status="exploratory")
    withf = build_suggestions(world[1], world[0], world[2], rules, as_of=as_of,
                              forecast=fc(as_of - timedelta(hours=1)))
    s = withf.suggestions[0]
    assert s.forecast_id == "fc:test" and s.reasons[-1].evidence_id == "fc:test"
    assert "not a direction" in s.reasons[-1].text
    with pytest.raises(ValueError, match="not causal"):
        build_suggestions(world[1], world[0], world[2], rules, as_of=as_of,
                          forecast=fc(as_of + timedelta(hours=1)))


def test_gates_use_the_frozen_rules_and_say_when_state_is_unknown(world, tmp_path):
    res, as_of = _first_hit(world, _rules(tmp_path))
    box = {"label": "test news", "start": (as_of - timedelta(minutes=5)).isoformat(),
           "end": (as_of + timedelta(hours=1)).isoformat()}
    blocked = build_suggestions(world[1], world[0], world[2],
                                _rules(tmp_path, version="b",
                                       blackouts=[box]), as_of=as_of, open_orders=[])
    g = {x.name: x for x in blocked.suggestions[0].gates}
    assert not g["news_blackout"].passed and "test news" in g["news_blackout"].detail
    assert NO_STATE in {x.name: x for x in res.suggestions[0].gates}["max_open_trades"].detail
    assert NO_STATE not in g["max_open_trades"].detail  # state was supplied (empty)


def test_refuses_unfrozen_rules_and_non_h1_bars(world, tmp_path):
    candles, setups, scorer = world
    p = tmp_path / "unfrozen.json"
    p.write_text(json.dumps(RULES))
    with pytest.raises(RulesError):
        build_suggestions(setups, candles, scorer, p, as_of=candles[-1].time)
    m15 = [c.model_copy(update={"tf": "M15"}) for c in candles[:50]]
    with pytest.raises(ValueError, match="H1"):
        build_suggestions(setups, m15, scorer, _rules(tmp_path), as_of=candles[60].time)
