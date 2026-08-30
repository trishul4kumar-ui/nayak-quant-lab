"""Frozen econometric identities. Formula changes require a new identity."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from quantlab.domain.research import CheckResult
from quantlab.econometrics.enums import (
    BreakKind,
    CausalClaim,
    EstimatorKind,
    PanelEffect,
)


class EconometricSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    spec_id: str
    estimator: EstimatorKind
    series_ids: tuple[str, ...]
    lags: int = 1
    include_constant: bool = True
    as_of: datetime
    window_start: datetime | None = None
    window_end: datetime | None = None
    snapshot_id: str = "synthetic-diagnostic"
    seed: int = 0
    note: str = "Specification identity. Changing the formula creates a new spec."


class StationarityTest(BaseModel):
    model_config = ConfigDict(frozen=True)

    method: str
    statistic: float | None
    critical_5: float | None
    rejects_unit_root: bool | None
    lags: int
    n: int
    status: CheckResult
    note: str = ""


class DependenceDiagnostic(BaseModel):
    model_config = ConfigDict(frozen=True)

    acf: list[float] = Field(default_factory=list)
    pacf: list[float] = Field(default_factory=list)
    ljung_box: float | None = None
    hac_lags: int = 0
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = ""


class CointegrationTest(BaseModel):
    model_config = ConfigDict(frozen=True)

    method: EstimatorKind
    statistic: float | None
    beta: float | None
    residual_adf: StationarityTest | None = None
    status: CheckResult
    note: str = "Johansen remains NOT_TESTED without a certified multivariate library."


class VARSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    spec_id: str
    lags: int
    n_series: int
    selected_on: str = "train_window"
    aic: float | None = None
    note: str = "Lag selection uses the training window only."


class VECMSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    spec_id: str
    lags: int
    rank: int | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "VECM from Engle-Granger ECM unless Johansen rank is sourced."


class CausalityTest(BaseModel):
    model_config = ConfigDict(frozen=True)

    method: str
    statistic: float | None
    p_value: float | None
    lags: int
    claim: CausalClaim = CausalClaim.PREDICTIVE
    status: CheckResult
    note: str = "Granger is predictive causality, not proof of causation."


class StructuralBreakTest(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: BreakKind
    statistic: float | None
    break_index: int | None
    status: CheckResult
    note: str = ""


class PanelSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    spec_id: str
    effect: PanelEffect
    clustered: bool = True
    note: str = "Clustered errors are diagnostic, not a license to ignore dependence."


class CausalSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypothesis_id: str
    method: EstimatorKind
    treatment: str
    outcome: str
    pretreat_only_controls: bool = True
    claim: CausalClaim = CausalClaim.CAUSAL_UNDER_ASSUMPTIONS
    assumptions: tuple[str, ...] = ()
    note: str = "Assumptions are explicit. Correlation is not causation."


class CausalHypothesis(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypothesis_id: str
    statement: str
    identification: str
    estimand: str
    claim: CausalClaim = CausalClaim.NONE
    note: str = "A causal hypothesis is not an estimate."


class EconomicSignificance(BaseModel):
    model_config = ConfigDict(frozen=True)

    statistical: CheckResult
    economic_effect: float | None
    execution_adjusted: float | None
    robust: CheckResult
    status: CheckResult
    note: str = "P-value is not economic value. Execution-adjusted uses Prompt 13/21 assumptions."


class EconometricDiagnostics(BaseModel):
    model_config = ConfigDict(frozen=True)

    stationarity: list[StationarityTest] = Field(default_factory=list)
    dependence: DependenceDiagnostic | None = None
    cointegration: CointegrationTest | None = None
    causality: CausalityTest | None = None
    breaks: StructuralBreakTest | None = None
    residuals: list[float] = Field(default_factory=list)
    note: str = ""


class EconometricRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    econometrics_run_id: str
    spec_id: str
    as_of: datetime
    run_hash: str = ""
    family_id: str = ""
    tested_count: int = 0
    live_trading: bool = False
    note: str = "Research econometrics. Synthetic is not market evidence."


class EconometricRequest(BaseModel):
    spec_id: str = "seed-econo"
    as_of: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    live_trading: bool = False
    data_kind: str = "synthetic"
    seed: int = 0
    n: int = 120
    family_id: str = "econo-family"
    future_payload_ignored: dict[str, str] = Field(default_factory=dict)


class EconometricResult(BaseModel):
    run: EconometricRun
    spec: EconometricSpecification
    diagnostics: EconometricDiagnostics
    var: VARSpecification | None = None
    vecm: VECMSpecification | None = None
    panel: PanelSpecification | None = None
    causal: CausalSpecification | None = None
    economics: EconomicSignificance | None = None
    multiple_testing: dict[str, str] = Field(default_factory=dict)
    live_trading: bool = False
    note: str = "IN-SAMPLE FIT ≠ OOS EVIDENCE. CORRELATION ≠ CAUSATION."
