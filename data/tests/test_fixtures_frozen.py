import hashlib

PINS = {
    "oanda/eurusd_m1_oanda_shape.json":
        "659aac4cbc3a65b50aaa8c428b7db68798e11152e4876117a3ab11c960fc54b4",
    "eurusd_h1_week.json":
        "03a4507b0a48baa02a1b402e1e502fb6aa4f1fd59811da5b16da3b3a5c7e0c8b",
}


def test_data_fixtures_are_frozen(fixtures_dir):
    """Edits to the frozen Phase 3 fixtures must be deliberate (regenerate, then re-pin)."""
    for name, digest in PINS.items():
        assert hashlib.sha256((fixtures_dir / name).read_bytes()).hexdigest() == digest, name
