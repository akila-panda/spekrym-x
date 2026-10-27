from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr
from test_oanda_rest import ENV, NOW, T0, Server

from sx_core.storage import candles_to_frame, data_version
from sx_data.cache import CandleCache
from sx_data.errors import DataError
from sx_data.oanda_rest import OandaClient
from sx_data.pipeline import rebuild_higher, sync_m1


def test_store_round_trip_manifest_and_version(tmp_path, m1_closed):
    cache = CandleCache(tmp_path)
    v = cache.store(candles_to_frame(m1_closed))
    assert cache.version("EUR_USD", "M1") == v == data_version(cache.load("EUR_USD", "M1"))
    manifest = (tmp_path / "EUR_USD" / "M1.json").read_text()
    assert v in manifest and '"n_bars": 175' in manifest and "2026-10-19T06:00:00Z" in manifest
    assert cache.load("EUR_USD", "M5") is None and cache.version("EUR_USD", "M5") is None


def test_store_merges_overlap_and_new_bars_win(tmp_path, m1_closed):
    cache = CandleCache(tmp_path)
    cache.store(candles_to_frame(m1_closed[:100]))
    changed = m1_closed[90].model_copy(update={"volume": 9999.0})
    cache.store(candles_to_frame([changed, *m1_closed[100:]]))
    df = cache.load("EUR_USD", "M1")
    assert len(df) == 175 and df["time"].is_monotonic_increasing and df["time"].is_unique
    assert df.loc[df["time"] == changed.time, "volume"].item() == 9999.0


def test_same_content_gives_same_version_regardless_of_batches(tmp_path, m1_closed):
    a, b = CandleCache(tmp_path / "a"), CandleCache(tmp_path / "b")
    va = a.store(candles_to_frame(m1_closed))
    b.store(candles_to_frame(m1_closed[:50]))
    vb = b.store(candles_to_frame(m1_closed[40:]))
    assert va == vb


def test_cache_refuses_bad_input(tmp_path, m1_all, m1_closed, h1_week):
    cache = CandleCache(tmp_path)
    with pytest.raises(DataError, match="complete"):
        cache.store(candles_to_frame(m1_all))  # last bar is still forming
    with pytest.raises(DataError, match="empty"):
        cache.store(candles_to_frame(m1_closed).iloc[0:0])
    with pytest.raises(DataError, match="one instrument"):
        cache.store(candles_to_frame([m1_closed[0], h1_week[0]]))
    for bad in ("../etc", "eur_usd", "EURUSD", "EUR_USD/.."):
        with pytest.raises(DataError):
            cache.path(bad, "M1")
    with pytest.raises(DataError):
        cache.path("EUR_USD", "../M1")


def test_sync_then_rebuild_builds_every_timeframe_from_m1(tmp_path, m1_payload, m1_closed):
    srv = Server(m1_payload)
    client = OandaClient(SecretStr("tok"), env=ENV, transport=httpx.MockTransport(srv),
                         sleep=lambda s: None, now=lambda: NOW, min_interval=0.0, page_size=60)
    cache = CandleCache(tmp_path)
    v = sync_m1(client, cache, "EUR_USD", T0, T0 + timedelta(hours=4))
    assert v == cache.version("EUR_USD", "M1")
    versions = rebuild_higher(cache, "EUR_USD")
    assert set(versions) == {"M15", "H1", "H4"}  # no closed D bar exists in 3 hours of data
    last_m15 = cache.load("EUR_USD", "M15")["time"].iloc[-1]
    assert last_m15 == datetime(2026, 10, 19, 8, 45, tzinfo=UTC)
    assert rebuild_higher(cache, "EUR_USD") == versions  # deterministic and idempotent


def test_sync_with_no_new_bars_returns_none(tmp_path, m1_payload):
    srv = Server({"candles": []})
    client = OandaClient(SecretStr("tok"), env=ENV, transport=httpx.MockTransport(srv),
                         sleep=lambda s: None, now=lambda: NOW, min_interval=0.0)
    assert sync_m1(client, CandleCache(tmp_path), "EUR_USD", T0, NOW) is None


def test_rebuild_without_m1_is_an_error(tmp_path):
    with pytest.raises(DataError, match="sync"):
        rebuild_higher(CandleCache(tmp_path), "EUR_USD")


def test_cli_sync_prints_versions_and_never_the_token(tmp_path, monkeypatch, capsys, m1_payload):
    from sx_data import cli

    (tmp_path / ".env").write_text("OANDA_TOKEN=tok-cli-secret\nSX_TRADING_MODE=paper\n")
    for k in ("SX_TRADING_MODE", "OANDA_ENV", "OANDA_TOKEN"):
        monkeypatch.delenv(k, raising=False)

    def fake(token, **kw):
        return OandaClient(token, env=ENV, transport=httpx.MockTransport(Server(m1_payload)),
                           sleep=lambda s: None, now=lambda: NOW, min_interval=0.0)

    monkeypatch.setattr(cli, "OandaClient", fake)
    monkeypatch.setattr(cli, "datetime", type("D", (), {"now": staticmethod(lambda tz=None: NOW)}))
    assert cli.main(["sync", "--days", "1", "--dotenv", str(tmp_path / ".env"),
                     "--cache", str(tmp_path / "c")]) == 0
    out = capsys.readouterr().out
    assert "M1 data_version" in out and "H1: dv:" in out and "tok-cli-secret" not in out
    assert "not validated" in out.lower()


def test_cli_refuses_non_paper_mode(tmp_path, monkeypatch):
    from sx_core.config import TradingModeError
    from sx_data import cli

    (tmp_path / ".env").write_text("SX_TRADING_MODE=live\nOANDA_TOKEN=x\n")
    monkeypatch.delenv("SX_TRADING_MODE", raising=False)
    with pytest.raises(TradingModeError):
        cli.main(["sync", "--dotenv", str(tmp_path / ".env"), "--cache", str(tmp_path / "c")])
