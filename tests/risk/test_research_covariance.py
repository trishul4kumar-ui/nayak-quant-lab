"""EWMA/shrinkage PIT covariance, PSD, and research risk experiments."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import numpy as np
import pytest

from quantlab.core.errors import CovarianceError
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.features.engine import session_calendar
from quantlab.portfolio.covariance import as_array, estimate_covariance, principal_risk_shares
from quantlab.research.gate import GateOutcome
from quantlab.risk.experiment import run_named_risk_experiment
from quantlab.risk.model import get_risk_model
from quantlab.risk.stress import run_stress, seed_scenarios


@pytest.mark.factor
def test_ewma_and_shrinkage_are_pit_and_psd() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    names = [str(inst) for inst in bars]
    calendar = session_calendar(bars)
    as_of = calendar[-5]
    for estimator in ("sample", "ewma", "shrinkage"):
        report = estimate_covariance(bars, as_of, names, 20, estimator=estimator)
        matrix = as_array(report)
        assert np.allclose(matrix, matrix.T)
        assert report.psd
        future = deepcopy(bars)
        for inst, series in future.items():
            extra = series[-1].model_copy(deep=True)
            extra.pit.event_time = calendar[-1] + timedelta(days=3)
            extra.pit.effective_time = extra.pit.event_time
            extra.pit.available_time = extra.pit.event_time
            extra.pit.ingestion_time = extra.pit.event_time
            extra.close = extra.close * 1.5
            future[inst] = series + [extra]
        later = estimate_covariance(future, as_of, names, 20, estimator=estimator)
        assert as_array(report) == pytest.approx(as_array(later), abs=1e-12)


@pytest.mark.factor
def test_ill_conditioned_covariance_fails() -> None:
    from datetime import UTC, datetime

    from quantlab.portfolio.covariance import _finalize

    cov = np.array([[1.0, 0.0], [0.0, 1e-20]], dtype=np.float64)
    with pytest.raises(CovarianceError, match="ill-conditioned"):
        _finalize(
            cov,
            ["NSE:A", "NSE:B"],
            lookback=20,
            estimator="sample",
            as_of=datetime(2024, 1, 2, tzinfo=UTC),
            n_obs=20,
            repair="none",
            extra={},
            note="test",
        )


@pytest.mark.parametrize("roundoff", [-5e-17, 0.0, 5e-17])
def test_null_eigenvalue_roundoff_does_not_change_invertibility(
    monkeypatch: pytest.MonkeyPatch, roundoff: float
) -> None:
    from datetime import UTC, datetime

    from quantlab.portfolio.covariance import _finalize

    monkeypatch.setattr(np.linalg, "eigvalsh", lambda _: np.array([roundoff, 2.0]))
    report = _finalize(
        np.array([[1.0, 1.0], [1.0, 1.0]]),
        ["NSE:A", "NSE:B"],
        lookback=20,
        estimator="sample",
        as_of=datetime(2024, 1, 2, tzinfo=UTC),
        n_obs=20,
        repair="none",
        extra={},
        note="singular fixture",
    )
    assert report.psd and report.rank == 1
    assert report.condition_number is None
    assert "not directly invertible" in report.note


@pytest.mark.factor
def test_non_psd_fails_unless_repair_named() -> None:
    from datetime import UTC, datetime

    from quantlab.portfolio.covariance import _finalize

    bad = np.array([[1.0, 2.0], [2.0, 1.0]], dtype=np.float64)
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    with pytest.raises(CovarianceError, match="not PSD"):
        _finalize(
            bad,
            ["NSE:A", "NSE:B"],
            lookback=2,
            estimator="sample",
            as_of=as_of,
            n_obs=2,
            repair="none",
            extra={},
            note="test",
        )
    repaired = _finalize(
        bad,
        ["NSE:A", "NSE:B"],
        lookback=2,
        estimator="sample",
        as_of=as_of,
        n_obs=2,
        repair="eigenvalue_clip",
        extra={},
        note="test",
    )
    assert repaired.psd
    assert repaired.repair == "eigenvalue_clip"


@pytest.mark.factor
def test_principal_risk_shares_sum_to_one() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    names = [str(inst) for inst in bars]
    calendar = session_calendar(bars)
    report = estimate_covariance(bars, calendar[-1], names, 20)
    shares = principal_risk_shares(report)
    assert shares
    assert sum(shares) == pytest.approx(1.0, abs=1e-8)


@pytest.mark.factor
def test_synthetic_risk_cannot_promote(tmp_path: Path) -> None:
    report, run = run_named_risk_experiment(
        "sample_cs",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.integrity["future_covariance"] == "pass"
    assert report.integrity["future_factor"] == "pass"
    assert report.integrity["future_beta"] == "pass"
    assert report.psd
    assert run.risk_model_id == "sample_cs"
    assert get_risk_model("ewma_cs").covariance_estimator == "ewma"
    assert (tmp_path / "artifacts" / run.id / "stress.json").is_file()


@pytest.mark.factor
def test_stress_is_labeled_not_a_forecast() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    names = [str(inst) for inst in bars]
    calendar = session_calendar(bars)
    cov = estimate_covariance(bars, calendar[-1], names, 20)
    weights = {name: 1.0 / len(names) for name in cov.names}
    for scenario in seed_scenarios():
        result = run_stress(weights, cov, scenario)
        assert "not a forecast" in result.note
        assert result.scenario_id == scenario.scenario_id
