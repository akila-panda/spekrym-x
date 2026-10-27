import pytest

from sx_core.contracts import Setup
from sx_core.labels import (
    RetrospectiveInputError,
    StatusLabel,
    assert_not_retrospective,
    display_name,
)


def test_exactly_the_five_documented_labels():
    assert {s.value for s in StatusLabel} == {
        "sample", "exploratory", "not_validated", "retrospective", "causal"}


def test_display_names():
    assert display_name("not_validated") == "Not validated"
    assert display_name(StatusLabel.SAMPLE) == "Sample data"
    with pytest.raises(ValueError):
        display_name("validated")


def test_retrospective_objects_are_blocked_from_models(fixtures_dir):
    import json

    raw = json.loads((fixtures_dir / "contracts" / "setup.json").read_text())
    causal = Setup.model_validate(raw)
    retro = Setup.model_validate({**raw, "status": "retrospective"})
    assert_not_retrospective([causal, object()])
    with pytest.raises(RetrospectiveInputError):
        assert_not_retrospective([causal, retro])
