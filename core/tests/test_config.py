import pytest

from sx_core.config import TradingModeError, enforce_paper_mode, load_settings, parse_dotenv

OK = {"SX_TRADING_MODE": "paper"}


def test_paper_mode_passes():
    enforce_paper_mode(OK)
    enforce_paper_mode({**OK, "OANDA_ENV": "practice"})


@pytest.mark.parametrize("env", [
    {}, {"SX_TRADING_MODE": "live"}, {"SX_TRADING_MODE": "Paper"}, {"SX_TRADING_MODE": ""},
    {"SX_TRADING_MODE": " paper"}, {"SX_TRADING_MODE": "paper", "OANDA_ENV": "live"},
    {"SX_TRADING_MODE": "paper", "OANDA_ENV": "trade"},
])
def test_anything_but_paper_practice_is_refused(env):
    with pytest.raises(TradingModeError, match="refusing to start"):
        enforce_paper_mode(env)


def test_load_settings_refuses_live_mode_even_via_dotenv(tmp_path):
    f = tmp_path / ".env"
    f.write_text("SX_TRADING_MODE=live\n")
    with pytest.raises(TradingModeError):
        load_settings(env={}, dotenv_path=f)


def test_real_env_overrides_dotenv(tmp_path):
    f = tmp_path / ".env"
    f.write_text("SX_TRADING_MODE=live\nOANDA_ACCOUNT_ID=111\n")
    s = load_settings(env={"SX_TRADING_MODE": "paper"}, dotenv_path=f)
    assert s.trading_mode == "paper" and s.oanda_account_id == "111"


def test_secrets_never_appear_in_repr():
    s = load_settings(env={**OK, "OANDA_TOKEN": "tok-secret-123", "ANTHROPIC_API_KEY": "sk-xyz"})
    assert "tok-secret-123" not in repr(s) and "sk-xyz" not in str(s)
    assert s.oanda_token.get_secret_value() == "tok-secret-123"


def test_missing_dotenv_file_is_fine():
    assert load_settings(env=OK, dotenv_path="/nonexistent/.env").ib_port == 7497


def test_repo_env_example_is_paper_and_loads(fixtures_dir):
    path = fixtures_dir.parent.parent / ".env.example"
    assert load_settings(env={}, dotenv_path=path).trading_mode == "paper"


def test_parse_dotenv():
    text = "# c\n\nA=1\nB = 'two'\nC=\"three\"\nD=x=y\nbad line\n"
    assert parse_dotenv(text) == {"A": "1", "B": "two", "C": "three", "D": "x=y"}
