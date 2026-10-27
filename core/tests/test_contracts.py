import json
import math
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sx_core.contracts import (
    Candle,
    Forecast,
    LedgerEntry,
    PaperOrder,
    Setup,
    Suggestion,
)

GOLDENS = {"candle": Candle, "setup": Setup, "forecast": Forecast, "suggestion": Suggestion,
           "paper_order": PaperOrder, "ledger_entry": LedgerEntry}


def golden(fixtures_dir, name):
    return json.loads((fixtures_dir / "contracts" / f"{name}.json").read_text())


@pytest.mark.parametrize("name", GOLDENS)
def test_golden_validates_and_round_trips_to_identical_json(fixtures_dir, name):
    raw = golden(fixtures_dir, name)
    model = GOLDENS[name].model_validate(raw)
    assert model.to_wire() == raw


@pytest.mark.parametrize("name", GOLDENS)
def test_unknown_field_is_rejected(fixtures_dir, name):
    raw = {**golden(fixtures_dir, name), "surprise": 1}
    with pytest.raises(ValidationError):
        GOLDENS[name].model_validate(raw)


@pytest.mark.parametrize("name", GOLDENS)
def test_models_are_immutable(fixtures_dir, name):
    model = GOLDENS[name].model_validate(golden(fixtures_dir, name))
    with pytest.raises(ValidationError):
        model.id = "x" if hasattr(model, "id") else None  # type: ignore[attr-defined]  # noqa: B010


def test_naive_datetime_rejected(fixtures_dir):
    raw = {**golden(fixtures_dir, "candle"), "time": "2026-10-19T00:00:00"}
    with pytest.raises(ValidationError, match="timezone"):
        Candle.model_validate(raw)


def test_offset_datetime_is_converted_to_utc_and_serialised_with_z(fixtures_dir):
    raw = {**golden(fixtures_dir, "candle"), "time": "2026-10-19T02:00:00+02:00"}
    c = Candle.model_validate(raw)
    assert c.time == datetime(2026, 10, 19, 0, 0, tzinfo=UTC)
    assert json.loads(c.model_dump_json())["time"] == "2026-10-19T00:00:00Z"


def test_candle_ohlc_order(fixtures_dir):
    raw = golden(fixtures_dir, "candle")
    with pytest.raises(ValidationError, match="OHLC"):
        Candle.model_validate({**raw, "high": raw["low"] - 0.001})


def test_candle_rejects_unknown_timeframe(fixtures_dir):
    with pytest.raises(ValidationError):
        Candle.model_validate({**golden(fixtures_dir, "candle"), "tf": "M3"})


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_non_finite_floats_rejected(fixtures_dir, bad):
    with pytest.raises(ValidationError):
        Candle.model_validate({**golden(fixtures_dir, "candle"), "volume": bad})


def test_setup_known_at_cannot_precede_event_time(fixtures_dir):
    raw = golden(fixtures_dir, "setup")
    with pytest.raises(ValidationError, match="known_at before event_time"):
        Setup.model_validate({**raw, "known_at": "2026-10-19T06:00:00Z"})


def test_setup_price_order(fixtures_dir):
    raw = golden(fixtures_dir, "setup")
    geo = {**raw["geometry"], "price_low": 2.0, "price_high": 1.0}
    with pytest.raises(ValidationError, match="price_low above price_high"):
        Setup.model_validate({**raw, "geometry": geo})


def test_setup_status_only_causal_or_retrospective(fixtures_dir):
    raw = golden(fixtures_dir, "setup")
    assert Setup.model_validate({**raw, "status": "retrospective"}).status == "retrospective"
    with pytest.raises(ValidationError):
        Setup.model_validate({**raw, "status": "exploratory"})


def test_forecast_point_inside_interval_and_coverage_bounds(fixtures_dir):
    raw = golden(fixtures_dir, "forecast")
    with pytest.raises(ValidationError, match="point outside interval"):
        Forecast.model_validate({**raw, "point": 1.0})
    with pytest.raises(ValidationError):
        Forecast.model_validate({**raw, "interval": {**raw["interval"], "nominal_coverage": 1.0}})


def test_forecast_status_cannot_claim_validation(fixtures_dir):
    raw = golden(fixtures_dir, "forecast")
    with pytest.raises(ValidationError):
        Forecast.model_validate({**raw, "status": "causal"})


def test_forecast_has_no_direction_field(fixtures_dir):
    assert not {"direction", "side", "bias"} & set(Forecast.model_fields)


def test_suggestion_must_stay_not_validated(fixtures_dir):
    raw = golden(fixtures_dir, "suggestion")
    with pytest.raises(ValidationError):
        Suggestion.model_validate({**raw, "status": "causal"})


def test_suggestion_reason_requires_evidence_id(fixtures_dir):
    raw = golden(fixtures_dir, "suggestion")
    with pytest.raises(ValidationError):
        Suggestion.model_validate({**raw, "reasons": [{"text": "trust me", "evidence_id": ""}]})


def test_paper_order_backend_is_paper_only(fixtures_dir):
    raw = golden(fixtures_dir, "paper_order")
    with pytest.raises(ValidationError):
        PaperOrder.model_validate({**raw, "backend": "oanda_live"})


def test_to_wire_omits_unset_optionals_but_keeps_payload_nulls(fixtures_dir):
    raw = golden(fixtures_dir, "candle")
    bare = {k: v for k, v in raw.items() if k not in ("bid_close", "ask_close")}
    assert Candle.model_validate(bare).to_wire() == bare
    entry = LedgerEntry.model_validate({**golden(fixtures_dir, "ledger_entry"),
                                        "payload": {"a": None}})
    assert entry.to_wire()["payload"] == {"a": None}
