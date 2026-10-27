"""Phase 5A: sample fixture, builder causality, checklist, payload labels."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sx_assistant.premarket.bias_checklist import build_checklist
from sx_assistant.premarket.builder import build_premarket
from sx_assistant.premarket.chart_payload import build_payload
from sx_assistant.premarket.data_source import DEFAULT_FIXTURE, SAMPLE_LABEL, FixtureSource
from sx_core.clock import bar_close

PINNED = "399e12e5218dabea4b4af0c16c08e5fff0b17d4ed1ba1aace9e6fd11ca829aed"
T = datetime(2026, 10, 26, 12, tzinfo=UTC)


@pytest.fixture(scope="module")
def src():
    return FixtureSource()


@pytest.fixture(scope="module")
def analysis(src):
    return build_premarket(src, "EUR_USD", T)


def test_fixture_is_pinned():
    assert hashlib.sha256(Path(DEFAULT_FIXTURE).read_bytes()).hexdigest() == PINNED


def test_source_is_labelled_not_live(src):
    assert src.info.live is False and src.info.label == SAMPLE_LABEL


def test_source_never_returns_unclosed_bars(src):
    t = datetime(2026, 10, 26, 10, 7, tzinfo=UTC)
    for tf in ("M15", "H1", "H4", "D"):
        assert all(bar_close(c.time, tf) <= t for c in src.candles("EUR_USD", tf, t))


def test_everything_is_known_by_as_of(analysis):
    assert analysis.setups
    assert all(s.known_at <= T and s.status == "causal" for s in analysis.setups)
    assert all(bar_close(c.time, "M15") <= T for c in analysis.candles)
    assert all(i.known_at <= T for i in analysis.checklist)


@pytest.mark.parametrize("hour", [3, 8])
def test_build_on_truncated_data_equals_build_as_of(src, hour):
    """Causality: as_of=t on the full source equals as_of=t on a source that ends at t."""
    t = datetime(2026, 10, 26, hour, tzinfo=UTC)

    class Truncated(FixtureSource):
        def last_close(self, instrument):
            return t

        def candles(self, instrument, tf, as_of):
            assert as_of <= t
            return super().candles(instrument, tf, as_of)

    full = build_premarket(src, "EUR_USD", t)
    cut = build_premarket(Truncated(), "EUR_USD", t)
    assert [s.model_dump() for s in full.setups] == [s.model_dump() for s in cut.setups]
    assert full.checklist == cut.checklist and full.data_version == cut.data_version


def test_later_as_of_is_refused(src):
    with pytest.raises(ValueError, match="after the newest closed bar"):
        build_premarket(src, "EUR_USD", T + timedelta(hours=1))


def test_naive_as_of_is_refused(src):
    with pytest.raises(ValueError, match="timezone"):
        build_premarket(src, "EUR_USD", datetime(2026, 10, 26, 12))


def test_checklist_is_facts_not_a_verdict(analysis):
    text = " ".join(i.text for i in analysis.checklist).lower()
    assert analysis.checklist
    for banned in ("buy", "sell", "probab", "%", "likely", "bullish bias", "bearish bias"):
        assert banned not in text


def test_checklist_needs_two_bars():
    assert build_checklist([], []) == []


def test_payload_labels_and_shape(analysis):
    p = build_payload(analysis)
    assert p["source"]["label"] == SAMPLE_LABEL and p["source"]["live"] is False
    assert p["status_labels"] == ["sample", "causal"]
    assert p["as_of"] == "2026-10-26T12:00:00Z" and p["bar_seconds"] == 900
    assert len(p["candles"]) == len(analysis.candles)
    assert {t["setup_id"] for t in p["timeline"]} == {s["id"] for s in p["setups"]}
    assert all(t["time"] <= p["as_of"] for t in p["timeline"])
    assert "Not a forecast" in p["disclaimer"]


def test_payload_session_bands_only_started_sessions(analysis):
    bands = build_payload(analysis)["session_bands"]
    assert bands and all(b["t_start"] <= "2026-10-26T12:00:00Z" for b in bands)
    ny = [b for b in bands if b["name"] == "ny" and b["id"].endswith("2026-10-26")]
    assert ny == [] or ny[0]["complete"] is False
