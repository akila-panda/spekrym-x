"""The Phase 4 fixtures are frozen: change them only on purpose (scripts/make_ta_fixtures.py)."""

import hashlib

import pytest

PINNED = {
    "labelled_day.json":
        "5befd7209164af2964d94604f1a1dfe0f31c84d5678013a041688e6ff509b630",
    "labelled_day_tail.json":
        "4436bf8225ef66bd50ebdb40420788f760fc0e823ee52697dbf81cc6c24cd641",
    "labelled_day_expected.json":
        "f78d74ca9bf1426bcfffac68060f2245f8b6d942571370252e97ece2ea687b9d",
    "liquidity_day.json":
        "5aa6e2f7af32c81a90defefa978cfc11568a8dc796b28a3509e87af120858fe3",
    "candle_day.json":
        "7caf23cc80e34b9fd16937dba2b9eb64c3e630b9cccd45fb5b24cc4921547cd3",
    "dst_h1.json":
        "0948bb5d11d78aad9a22ecdf1305cf9a7cfc956ae2c305945559d1eb55403f53",
}


@pytest.mark.parametrize("name", sorted(PINNED))
def test_fixture_hash_is_pinned(ta_dir, name):
    digest = hashlib.sha256((ta_dir / name).read_bytes()).hexdigest()
    assert digest == PINNED[name], f"{name} changed: {digest}"


def test_fixtures_are_valid_closed_ordered_series(day, day_tail, liq, candle_day, dst_h1):
    for series in (day, day_tail, liq["candles"], candle_day["candles"], dst_h1):
        assert all(c.complete for c in series)
        assert [c.time for c in series] == sorted({c.time for c in series})
    assert day_tail[0].time == day[-1].time + (day[1].time - day[0].time)
