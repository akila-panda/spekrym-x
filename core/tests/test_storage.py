import hashlib

import pandas as pd

from sx_core.storage import (
    candles_to_frame,
    data_version,
    frame_to_candles,
    read_parquet,
    write_parquet,
)


def test_fixture_file_is_frozen(fixtures_dir):
    """Edits to the frozen candle fixture must be deliberate."""
    digest = hashlib.sha256((fixtures_dir / "eurusd_m15_96bars.json").read_bytes()).hexdigest()
    assert digest == "4a18001cd4e54aca3f6919df9eab357bd1f0a0f782d19d6ebdb00ee55a218244"


def test_parquet_round_trip_preserves_candles_and_version(tmp_path, m15_candles):
    df = candles_to_frame(m15_candles)
    v = write_parquet(df, tmp_path / "sub" / "c.parquet")
    back = read_parquet(tmp_path / "sub" / "c.parquet")
    assert data_version(back) == v
    assert frame_to_candles(back) == m15_candles
    assert str(back["time"].dtype) == "datetime64[ns, UTC]"


def test_missing_bid_ask_round_trips_as_none(tmp_path, m15_candles):
    cs = [m15_candles[0].model_copy(update={"bid_close": None, "ask_close": None})]
    write_parquet(candles_to_frame(cs), tmp_path / "c.parquet")
    assert frame_to_candles(read_parquet(tmp_path / "c.parquet")) == cs


def test_version_depends_on_content_not_on_file_bytes(tmp_path, m15_candles):
    df = candles_to_frame(m15_candles)
    v1 = write_parquet(df, tmp_path / "a.parquet")
    v2 = write_parquet(df.copy(), tmp_path / "b.parquet")
    assert v1 == v2 == data_version(df)


def test_version_changes_with_any_value_row_order_or_column(m15_candles):
    df = candles_to_frame(m15_candles)
    base = data_version(df)
    tweaked = df.copy()
    tweaked.loc[10, "close"] += 0.00001
    assert data_version(tweaked) != base
    assert data_version(df.iloc[::-1].reset_index(drop=True)) != base
    assert data_version(df.drop(columns=["volume"])) != base
    assert data_version(df.iloc[:-1]) != base


def test_version_ignores_index(m15_candles):
    df = candles_to_frame(m15_candles)
    assert data_version(df.set_axis(range(100, 100 + len(df)))) == data_version(df)


def test_version_is_stable_with_nan_and_equal_across_timezone_representations(m15_candles):
    cs = [c.model_copy(update={"bid_close": None}) for c in m15_candles[:5]]
    df = candles_to_frame(cs)
    other = df.copy()
    other["time"] = other["time"].dt.tz_convert("Asia/Colombo")
    assert data_version(df) == data_version(other)
    assert isinstance(df["bid_close"].iloc[0], float) and pd.isna(df["bid_close"].iloc[0])


def test_version_format(m15_candles):
    v = data_version(candles_to_frame(m15_candles))
    assert v.startswith("dv:") and len(v) == 19
