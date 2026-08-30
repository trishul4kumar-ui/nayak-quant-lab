from __future__ import annotations

import pytest

from quantlab.release.errors import InvalidReleaseTransition
from quantlab.release.state import CertState, current, transition

pytestmark = pytest.mark.release


def test_draft_to_certified_is_illegal() -> None:
    assert current() is CertState.DRAFT
    with pytest.raises(InvalidReleaseTransition):
        transition(CertState.CERTIFIED)


def test_failed_to_certified_is_illegal() -> None:
    from quantlab.release.state import force

    force(CertState.FAILED)
    with pytest.raises(InvalidReleaseTransition):
        transition(CertState.CERTIFIED)


def test_no_live_state() -> None:
    assert not hasattr(CertState, "LIVE")
    names = {item.value for item in CertState}
    assert "live" not in names
    assert "live_enabled" not in names
