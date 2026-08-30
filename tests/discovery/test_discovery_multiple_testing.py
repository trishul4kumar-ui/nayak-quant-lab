from __future__ import annotations

import pytest

from quantlab.orchestration.multiple_testing import family_correction
from quantlab.research.gate import GateOutcome


@pytest.mark.discovery
def test_family_correction_reuses_prompt05() -> None:
    report = family_correction([0.9, 0.8, 0.7, 0.6], method="benjamini_hochberg")
    assert report.n_hypotheses == 4
    assert report.discoveries == 0
    assert GateOutcome.RESEARCH_CANDIDATE.value != "warn"
