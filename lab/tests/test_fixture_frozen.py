import hashlib

PIN = "f762bb59e209f924a63e8307cb7ac2b05b78e5fdddca319974b30d1c2d248a22"


def test_lab_fixture_is_frozen(fixtures_dir):
    """Edits to the frozen Lab fixture must be deliberate (regenerate, then re-pin)."""
    raw = (fixtures_dir / "lab" / "eurusd_h1_synth_1000.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
