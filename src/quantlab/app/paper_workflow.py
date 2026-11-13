"""Explicit immutable inputs for local paper accounting and historical shadow replay.

This module never imports a broker writer. A configured paper opening balance is
not an observed broker balance. Frozen historical marks are replay evidence, not
fresh market observations or proof of historical point-in-time availability.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from quantlab.agents.hashing import Artifact, digest
from quantlab.agents.repository import AgentRepository
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.market_backtest import FrozenMarketHistory
from quantlab.capital.allocator import AllocationResult
from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.capital.identity import hash_decision
from quantlab.core.errors import DataIntegrityError
from quantlab.paper_oms.models import (
    CashLedger,
    PaperAccount,
    PaperMarketSnapshot,
    PaperOMSRequest,
    PaperOMSResult,
)
from quantlab.realtime_data.candles import INTERVALS


class FrozenPaperMarket(Artifact):
    snapshot: PaperMarketSnapshot
    history_hashes: tuple[str, ...] = Field(min_length=1)
    purpose: Literal["historical_replay"] = "historical_replay"
    execution_authority: Literal[False] = False


class PaperWorkflowInputs(Artifact):
    research_result_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    capital_allocation_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: InvestmentDecision
    target: TargetPortfolio
    opening_account: PaperAccount
    arrival: FrozenPaperMarket
    reviewed: Literal[True]
    execution_policy_id: str = "base"
    historical_replay: Literal[True] = True
    unverified_liquidity_acknowledged: bool = False
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_links(self) -> PaperWorkflowInputs:
        if self.decision.live_trading or self.decision.data_kind.lower() != "real":
            raise ValueError("REAL_PAPER_DECISION_REQUIRED")
        if self.decision.research_result_id != self.research_result_hash:
            raise ValueError("DECISION_RESEARCH_PARENT_MISMATCH")
        if self.target.decision_id != self.decision.decision_id:
            raise ValueError("TARGET_DECISION_MISMATCH")
        if self.target.weights != self.decision.target_weights:
            raise ValueError("TARGET_DECISION_WEIGHTS_MISMATCH")
        if hash_decision(self.decision) != self.decision.decision_hash:
            raise ValueError("DECISION_HASH_MISMATCH")
        if self.decision.decision_time >= self.arrival.snapshot.as_of:
            raise ValueError("ARRIVAL_MUST_FOLLOW_DECISION")
        if self.opening_account.cash < 0 or self.opening_account.equity <= 0:
            raise ValueError("EXPLICIT_POSITIVE_PAPER_CAPITAL_REQUIRED")
        required = set(self.target.weights) | set(self.opening_account.positions)
        if required - set(self.arrival.snapshot.prices):
            raise ValueError("ARRIVAL_MARKS_MISSING")
        if self.target.portfolio_hash != self.decision.decision_hash:
            raise ValueError("TARGET_DECISION_HASH_MISMATCH")
        equity = self.opening_account.equity
        if any(
            abs(self.target.notional_targets.get(name, 0.0) - equity * weight)
            > max(1e-6, abs(equity) * 1e-10)
            for name, weight in self.target.weights.items()
        ):
            raise ValueError("TARGET_PAPER_BUDGET_MISMATCH")
        if (
            abs(self.target.cash_target + sum(self.target.notional_targets.values()) - equity)
            > 1e-6
        ):
            raise ValueError("TARGET_CASH_BUDGET_IDENTITY_FAILED")
        return self


class FrozenCapitalAllocation(Artifact):
    research_result_hash: str
    opening_cash: float = Field(gt=0)
    allocation: AllocationResult
    execution_authority: Literal[False] = False


class FrozenPaperWorkflowRun(Artifact):
    kind: Literal["paper_oms", "monitoring", "tca", "shadow", "twin"]
    workflow_id: str
    parent_run_hash: str = ""
    mark_snapshot_hash: str = ""
    result: dict[str, Any]
    execution_authority: Literal[False] = False


def _positive_cash(value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        raise DataIntegrityError("PAPER_CAPITAL_REQUIRED: enter a finite positive research budget")
    return float(value)


def allocate_research_capital(
    *,
    repository_path: Path,
    ledger_path: Path,
    research_result_hash: str,
    opening_cash: float,
    allow_unverified_liquidity: bool = False,
    publication_job: Job | None = None,
) -> dict[str, Any]:
    """Allocate genuine portfolio scores/risk, with no fabricated ADV or passing gate."""
    import json

    from quantlab.app.research_workbench import load_research_run
    from quantlab.capital.allocator import allocate
    from quantlab.capital.definitions import (
        AllocationRequest,
        CapitalBooks,
        CapitalPolicy,
        ConstraintPolicy,
        ExpectedReturnSource,
        LiquidityPolicy,
        SizingMethod,
    )
    from quantlab.capital.experiment import _run_from_result
    from quantlab.capital.memory import register
    from quantlab.models.registry import ExperimentLedger
    from quantlab.portfolio.covariance import CovarianceReport
    from quantlab.research.gate import GateOutcome, ResearchGateResult

    cash = _positive_cash(opening_cash)
    if not research_result_hash:
        raise DataIntegrityError(
            "RESEARCH_PORTFOLIO_REQUIRED: select a completed real portfolio result"
        )
    research = load_research_run(repository_path, research_result_hash)
    if research.engine != "portfolio":
        raise DataIntegrityError(
            "PORTFOLIO_RESULT_REQUIRED: Features or ordinary backtests are not allocations"
        )
    report = json.loads(research.report_json)
    scores = report.get("expected_returns", {})
    raw_weights = report.get(
        "target_weights", report.get("targets", report.get("last_weights", {}))
    )
    covariance_payload = report.get("covariance")
    if not raw_weights or covariance_payload is None:
        raise DataIntegrityError(
            "CAPITAL_INPUTS_REQUIRED: selected portfolio must persist constructor targets "
            "and an aligned covariance report; rank scores are not expected returns"
        )
    covariance = CovarianceReport.model_validate(covariance_payload)
    if covariance.as_of is None or covariance.as_of > research.context.analytical_end:
        raise DataIntegrityError("COVARIANCE_TIME_MISMATCH")
    if covariance.n_obs < 2 or not set(raw_weights).issubset(covariance.names):
        raise DataIntegrityError("SCORES_COVARIANCE_UNIVERSE_MISMATCH")
    if any(not math.isfinite(float(value)) for value in scores.values()):
        raise DataIntegrityError("NONFINITE_EXPECTED_RETURN")
    # Use a fully named research-only policy, never mutate the production policy.
    policy = CapitalPolicy(
        policy_id="EXPLORATORY-PAPER-CAPITAL-v1",
        starting_capital=cash,
        available_capital=cash,
        cash_floor=0.05,
        max_position_weight=0.40,
        sizing_method=SizingMethod.SCORE_WEIGHT,
        liquidity_policy=LiquidityPolicy(strict_unknown=not allow_unverified_liquidity),
        constraint_policy=ConstraintPolicy(strict_missing_covariance=True),
    ).with_hash()
    request = AllocationRequest(
        policy_id=policy.policy_id,
        as_of=research.context.analytical_end,
        snapshot_id=research.context.input_hash,
        dataset_checksum=research.context.input_hash,
        scores={str(name): float(value) for name, value in scores.items()},
        expected_return_source=ExpectedReturnSource.MODEL,
        expected_return_confidence=0.0,
        covariance=covariance,
        vols={
            name: math.sqrt(max(covariance.matrix[index][index], 0.0))
            for index, name in enumerate(covariance.names)
        },
        data_kind="REAL",
        books=CapitalBooks(
            equity=cash,
            cash=cash,
            investable_capital=cash,
            note="Explicit research paper budget; not observed available broker cash.",
        ),
        gate=ResearchGateResult(
            outcome=GateOutcome.WARN,
            warnings=[
                "Exploratory research only; independent PIT, validation and liquidity "
                "evidence is NOT_TESTED."
            ],
        ),
        liquidity_adv={name: None for name in covariance.names},
        portfolio_spec_id=research.specification,
        experiment_id=research.run_id,
        research_result_id=research.content_hash,
        strategy_id=research.specification,
        knowledge_snapshot_id="",
        risk_policy_id=policy.policy_id,
        input_alpha_version=research.content_hash,
        covariance_version=research.content_hash,
        risk_model_version=research.content_hash,
        regime_version="NOT_TESTED",
        execution_model_version="configured-paper-base",
        n_obs_returns=covariance.n_obs,
    )
    allocation = (
        allocate(request, policy=policy)
        if scores
        else _allocate_constructor_targets(
            raw_weights,
            covariance,
            request=request,
            research_hash=research.content_hash,
            cash=cash,
            allow_unverified_liquidity=allow_unverified_liquidity,
        )
    )
    frozen = FrozenCapitalAllocation(
        created_at=datetime.now(UTC),
        research_result_hash=research.content_hash,
        opening_cash=cash,
        allocation=allocation,
    )
    repository = AgentRepository(repository_path)
    try:
        if publication_job is not None:
            publication_job.begin_publication()
        repository.put(frozen)
        row = _run_from_result(allocation, request)
        from quantlab.domain.models import ExperimentStatus

        row = row.model_copy(
            update={"status": ExperimentStatus.COMPLETED, "gate_outcome": "NOT_TESTED"}
        )
        ExperimentLedger(ledger_path).append(row)
        repository.audit(
            "CAPITAL_COMPLETED",
            run_id=allocation.decision.decision_id,
            now=frozen.created_at,
            artifact_hash=frozen.content_hash,
        )
    finally:
        repository.close()
    register(allocation)
    return {
        "kind": "capital",
        "result_hash": frozen.content_hash,
        "research_result_hash": research.content_hash,
        "decision_id": allocation.decision.decision_id,
        "decision": allocation.decision.model_dump(mode="json"),
        "target": allocation.target.model_dump(mode="json"),
        "allocation": allocation.model_dump(mode="json"),
        "opening_cash": cash,
        "data_kind": "REAL",
        "validation_state": "NOT_TESTED",
        "live_trading": False,
        "execution_authority": False,
        "unverified_liquidity_acknowledged": allow_unverified_liquidity,
        "note": (
            "Research-only target. Unknown ADV remains unknown; "
            "no broker balance or order authority."
        ),
    }


def _allocate_constructor_targets(
    raw_weights: dict[str, Any],
    covariance: Any,
    *,
    request: Any,
    research_hash: str,
    cash: float,
    allow_unverified_liquidity: bool,
) -> AllocationResult:
    """Budget an existing constructor, not pretend rank scores are return forecasts."""
    import numpy as np

    from quantlab import __version__
    from quantlab.capital.decision import freeze_decision
    from quantlab.capital.definitions import (
        AbstentionCode,
        CapitalAllocationState,
        ConstraintCheck,
        DecisionStatus,
        ExpectedReturn,
        LiquidityStatus,
    )
    from quantlab.capital.diagnostics import AllocationDiagnostics
    from quantlab.domain.research import CheckResult, IntegrityReport
    from quantlab.portfolio.risk_model import portfolio_volatility, risk_contributions

    weights = {str(name): float(value) for name, value in raw_weights.items()}
    if any(not math.isfinite(value) or value < 0 for value in weights.values()):
        raise DataIntegrityError(
            "LONG_ONLY_PAPER_WEIGHTS_REQUIRED: no implicit shorting or leverage"
        )
    gross = sum(weights.values())
    if gross > 1.0 + 1e-9 or gross <= 0:
        raise DataIntegrityError("UNLEVERED_PAPER_WEIGHT_BUDGET_REQUIRED")
    matrix = np.asarray(covariance.matrix, dtype=float)
    if (
        matrix.shape != (len(covariance.names), len(covariance.names))
        or not np.isfinite(matrix).all()
        or not np.allclose(matrix, matrix.T)
        or float(np.linalg.eigvalsh(matrix).min()) < -1e-10
    ):
        raise DataIntegrityError("INVALID_COVARIANCE_FOR_CAPITAL")
    # Five percent research cash reserve is explicit, not hidden optimization.
    scale = min(1.0, 0.95 / gross)
    weights = {name: value * scale for name, value in weights.items()}
    warnings = [
        "Constructor weights budgeted directly; rank scores are not calibrated expected returns.",
        "Covariance and volatility are per observed interval, not annualized.",
        "Historical availability, corporate actions, official calendar and ADV are NOT_TESTED.",
        "A 5% minimum cash reserve applies; no shorting or leverage.",
    ]
    blocked = not allow_unverified_liquidity
    if blocked:
        weights = {}
    gross = sum(weights.values())
    risk = risk_contributions(weights, covariance)
    decision = freeze_decision(
        InvestmentDecision(
            decision_id="pending",
            decision_time=request.as_of,
            snapshot_id=request.snapshot_id,
            experiment_id=request.experiment_id,
            research_result_id=research_hash,
            strategy_id=request.strategy_id,
            portfolio_spec_id=request.portfolio_spec_id,
            capital_policy_id="EXPLORATORY-CONSTRUCTOR-BUDGET-v1",
            risk_policy_id="PER-INTERVAL-COVARIANCE-v1",
            covariance_version=research_hash,
            input_alpha_version=research_hash,
            risk_model_version=research_hash,
            decision_status=DecisionStatus.ABSTAIN if blocked else DecisionStatus.RESEARCH_ONLY,
            expected_return={},
            expected_return_source="unavailable_rank_signal_not_return_forecast",
            expected_risk=portfolio_volatility(weights, covariance),
            expected_volatility=portfolio_volatility(weights, covariance),
            target_weights=weights,
            gross_target=gross,
            net_target=gross,
            risk_contribution={
                row.security_id: row.component
                for row in risk.contributions
                if row.component is not None
            },
            constraint_status=[
                ConstraintCheck(
                    name="unlevered_long_only", result=CheckResult.PASS, value=gross, bound=1.0
                ),
                ConstraintCheck(
                    name="minimum_research_cash",
                    result=CheckResult.PASS,
                    value=1.0 - gross,
                    bound=0.05,
                ),
                ConstraintCheck(
                    name="sourced_adv",
                    result=CheckResult.NOT_TESTED,
                    note="Unknown; acknowledgement permits historical paper research only.",
                ),
            ],
            liquidity_status=LiquidityStatus.UNKNOWN,
            confidence=0.0,
            evidence_status="EXPLORATORY_NOT_INDEPENDENTLY_VALIDATED",
            abstention_code=AbstentionCode.UNKNOWN_LIQUIDITY if blocked else AbstentionCode.NONE,
            abstention_reason="ADV unavailable; research-only liquidity acknowledgement required"
            if blocked
            else "",
            capital_state=CapitalAllocationState.ABSTAIN
            if blocked
            else CapitalAllocationState.FULL,
            allocation_method="persisted_constructor_weights_explicit_paper_budget",
            data_kind="REAL",
            warnings=warnings,
            config_hash=digest(
                {
                    "research": research_hash,
                    "cash": cash,
                    "reserve": 0.05,
                    "allow_unverified_liquidity": allow_unverified_liquidity,
                }
            ),
            created_at=request.as_of,
            software_version=__version__,
            note=(
                "Research-only constructor budget, not expected-return optimization, "
                "validation, or an order."
            ),
        )
    )
    target = TargetPortfolio(
        portfolio_id=f"TP-{decision.decision_id}",
        decision_id=decision.decision_id,
        timestamp=request.as_of,
        weights=weights,
        notional_targets={name: cash * value for name, value in weights.items()},
        cash_target=cash * (1 - gross),
        gross_exposure=gross,
        net_exposure=gross,
        risk_target=None,
        constraint_state=decision.constraint_status,
        portfolio_hash=decision.decision_hash,
        note="Target from persisted constructor and explicit paper cash. Not a broker instruction.",
    )
    return AllocationResult(
        decision=decision,
        target=target,
        diagnostics=AllocationDiagnostics(
            warnings=warnings,
            vol_status="PER_INTERVAL_NOT_ANNUALIZED",
            explanations=[
                {"name": name, "target_weight": str(value)} for name, value in weights.items()
            ],
        ),
        integrity=IntegrityReport(
            checks={
                "independent_validation": CheckResult.NOT_TESTED,
                "historical_availability": CheckResult.NOT_TESTED,
            }
        ),
        expected_return=ExpectedReturn(
            values={},
            confidence=0.0,
            note="Rank scores are not calibrated expected returns; no expected return estimated.",
        ),
    )


def prepare_workflow(
    *,
    repository_path: Path,
    research_result_hash: str,
    opening_cash: float,
    arrival_history_hashes: tuple[str, ...] = (),
    reviewed: bool = False,
    allow_unverified_liquidity: bool = False,
    execution_policy_id: str = "base",
    ledger_path: Path | None = None,
    publication_job: Job | None = None,
) -> dict[str, Any]:
    """End-user preparation API: review one research portfolio and a paper budget."""
    from quantlab.app.research_workbench import load_research_run
    from quantlab.paper_oms.policy import resolve_policy

    if not reviewed:
        raise DataIntegrityError(
            "REVIEW_REQUIRED: review the target and historical replay assumptions"
        )
    research = load_research_run(repository_path, research_result_hash)
    resolved_policy = resolve_policy(execution_policy_id)
    allocation_payload = allocate_research_capital(
        repository_path=repository_path,
        ledger_path=ledger_path or repository_path.with_name("paper_workflow_ledger.jsonl"),
        research_result_hash=research.content_hash,
        opening_cash=opening_cash,
        allow_unverified_liquidity=allow_unverified_liquidity,
        publication_job=publication_job,
    )
    allocation = AllocationResult.model_validate(allocation_payload["allocation"])
    if not allocation.target.weights:
        raise DataIntegrityError(
            f"CAPITAL_TARGET_UNAVAILABLE: {allocation.decision.abstention_code.value}; "
            f"{allocation.decision.abstention_reason}. Review the capital constraints; "
            "unknown liquidity is not silently treated as infinite."
        )
    repository = AgentRepository(repository_path)
    try:
        hashes = arrival_history_hashes or research.context.history_hashes
        if set(hashes) != set(research.context.history_hashes):
            # A later arrival capture is allowed only if it has exactly the same named universe.
            names = {repository.get(item, FrozenMarketHistory).instrument for item in hashes}
            if names != set(research.context.universe):
                raise DataIntegrityError("ARRIVAL_UNIVERSE_MISMATCH")
        arrival = market_from_histories(repository, hashes, after=allocation.decision.decision_time)
        account_key = digest({"research": research.content_hash, "cash": opening_cash})[:16]
        inputs = repository.put(
            PaperWorkflowInputs(
                created_at=datetime.now(UTC),
                research_result_hash=research.content_hash,
                capital_allocation_hash=allocation_payload["result_hash"],
                decision=allocation.decision,
                target=allocation.target,
                opening_account=opening_paper_account(
                    opening_cash, account_id=f"PAPER-{account_key}"
                ),
                arrival=arrival,
                reviewed=True,
                execution_policy_id=resolved_policy.policy_id,
                unverified_liquidity_acknowledged=allow_unverified_liquidity,
            )
        )
        return {
            "workflow_id": inputs.content_hash,
            "inputs_hash": inputs.content_hash,
            "research_result_hash": research.content_hash,
            "decision_id": inputs.decision.decision_id,
            "arrival_snapshot_id": arrival.snapshot.snapshot_id,
            "as_of": arrival.snapshot.as_of.isoformat(),
            "history_hashes": list(arrival.history_hashes),
            "paper_cash": opening_cash,
            "target_weights": inputs.target.weights,
            "historical_replay": True,
            "reviewed": True,
            "live_trading": False,
            "warnings": [arrival.snapshot.note, allocation_payload["note"]],
        }
    finally:
        repository.close()


def opening_paper_account(cash: float, *, account_id: str) -> PaperAccount:
    value = _positive_cash(cash)
    return PaperAccount(
        account_id=account_id,
        cash=value,
        available_cash=value,
        equity=value,
        ledger=CashLedger(opening_cash=value, closing_cash=value),
        note="Explicit user-configured opening paper cash; not broker cash or order authority.",
    )


def run_selected_workflow(
    kind: str,
    *,
    workflow_id: str = "",
    repository_path: Path | None = None,
    ledger_path: Path | None = None,
    mark_history_hashes: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Synchronous CLI boundary; the desktop uses execute_paper_workflow in a worker."""
    from uuid import uuid4

    from quantlab.app.paths import RuntimePaths

    paths = RuntimePaths.discover()
    job = Job(
        job_id=uuid4().hex,
        type="paper_workflow",
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC).isoformat(),
        parameters={
            "kind": kind,
            "workflow_id": workflow_id,
            "mark_history_hashes": mark_history_hashes,
        },
    )
    return execute_paper_workflow(
        job,
        repository_path=repository_path or paths.database_dir / "agent_desk.sqlite",
        ledger_path=ledger_path or paths.ledger_path,
    )


def market_from_histories(
    repository: AgentRepository,
    history_hashes: tuple[str, ...],
    *,
    as_of: datetime | None = None,
    after: datetime | None = None,
    persist: bool = True,
) -> FrozenPaperMarket:
    """Use a common closed-bar endpoint; never stamp old prices with the wall clock."""
    if not history_hashes:
        raise DataIntegrityError("ARRIVAL_HISTORY_REQUIRED: select frozen real history artifacts")
    histories = tuple(repository.get(item, FrozenMarketHistory) for item in history_hashes)
    if any(item.content_hash != key for item, key in zip(histories, history_hashes, strict=True)):
        raise DataIntegrityError("MARK_HISTORY_HASH_MISMATCH")
    if len({item.instrument for item in histories}) != len(histories):
        raise DataIntegrityError("DUPLICATE_INSTRUMENT_HISTORY: choose one history per security")
    if len({item.interval for item in histories}) != 1:
        raise DataIntegrityError("MARK_INTERVAL_MISMATCH: all histories must share an interval")
    duration = timedelta(seconds=INTERVALS[histories[0].interval])
    endpoints = [set(bar.time + duration for bar in item.candles) for item in histories]
    common = set.intersection(*endpoints)
    if as_of is not None:
        if as_of.tzinfo is None:
            raise DataIntegrityError("MARK_TIMEZONE_REQUIRED")
        common = {time for time in common if time <= as_of}
    if after is not None:
        if after.tzinfo is None:
            raise DataIntegrityError("DECISION_TIMEZONE_REQUIRED")
        common = {time for time in common if time > after}
        if not common:
            raise DataIntegrityError(
                "SUBSEQUENT_ARRIVAL_MARK_REQUIRED: select a later capture, or a portfolio "
                "whose analytical cutoff precedes a sourced closed arrival bar"
            )
    if not common:
        raise DataIntegrityError("NO_COMMON_MARK_TIME: capture aligned real history")
    end = min(common) if after is not None else max(common)
    prices: dict[str, float] = {}
    volumes: dict[str, float | None] = {}
    for history in histories:
        bar = next(bar for bar in history.candles if bar.time + duration == end)
        if not math.isfinite(bar.close) or bar.close <= 0:
            raise DataIntegrityError("INVALID_MARK_PRICE")
        prices[history.instrument] = bar.close
        # This is reported closed-bar volume, not a daily ADV claim.
        volumes[history.instrument] = (
            bar.volume if bar.volume is not None and bar.volume > 0 else None
        )
    key = digest({"histories": sorted(history_hashes), "as_of": end.isoformat()})
    snap = PaperMarketSnapshot(
        snapshot_id=f"historical-mark-{key[:16]}",
        as_of=end,
        prices=prices,
        volumes=volumes,
        tradable={},
        data_kind="REAL",
        source="kite-historical-v3",
        evidence_hashes=history_hashes,
        captured_at=max(item.captured_at for item in histories),
        note=(
            "Historical closed-bar replay mark, not a fresh quote. Bar volume is not ADV. "
            "Tradability is unspecified. Corporate actions, historical availability "
            "and official calendar are NOT_TESTED."
        ),
    )
    frozen = FrozenPaperMarket(
        created_at=max(item.captured_at for item in histories),
        snapshot=snap,
        history_hashes=history_hashes,
    )
    return repository.put(frozen) if persist else frozen


def workflow_choices(repository_path: Path | None = None) -> list[dict[str, Any]]:
    repository = AgentRepository(repository_path)
    try:
        return [
            {
                "workflow_id": item.content_hash,
                "decision_id": item.decision.decision_id,
                "research_result_hash": item.research_result_hash,
                "paper_cash": item.opening_account.cash,
                "arrival_snapshot_id": item.arrival.snapshot.snapshot_id,
                "as_of": item.arrival.snapshot.as_of.isoformat(),
                "historical_replay": True,
                "reviewed": True,
            }
            for item in _compatible_workflows(repository)
        ]
    finally:
        repository.close()


def _compatible_workflows(repository: AgentRepository) -> tuple[PaperWorkflowInputs, ...]:
    """Retain obsolete input contracts in storage without making desktop startup fail.

    A previously frozen workflow that lacks the present parent/cutoff requirements
    cannot feed a new calculation. It is not silently migrated or relabelled.
    """
    valid = []
    for row in repository.store.list_latest("agent_artifacts"):
        if row.get("type") != "PaperWorkflowInputs":
            continue
        try:
            valid.append(PaperWorkflowInputs.model_validate(row["artifact"]))
        except (KeyError, ValueError):
            continue
    return tuple(valid)


def latest_workflow_result(
    kind: str,
    *,
    repository_path: Path | None = None,
    workflow_id: str | None = None,
) -> dict[str, Any] | None:
    """Display query only; never substitutes another run as a computation input."""
    repository = AgentRepository(repository_path)
    try:
        published = {
            item.artifact_hash
            for item in repository.audit_events()
            if item.event == "PAPER_WORKFLOW_COMPLETED"
        }
        valid_workflows = {item.content_hash for item in _compatible_workflows(repository)}
        rows = [
            item
            for item in repository.list(FrozenPaperWorkflowRun)
            if item.kind == kind
            and (workflow_id is None or item.workflow_id == workflow_id)
            and item.content_hash in published
            and item.workflow_id in valid_workflows
        ]
        if not rows:
            return None
        chosen = max(rows, key=lambda row: row.created_at)
        return {
            "result_hash": chosen.content_hash,
            "workflow_id": chosen.workflow_id,
            "kind": chosen.kind,
            "created_at": chosen.created_at.isoformat(),
            "historical_replay": True,
            "data_kind": "REAL",
            **chosen.result,
        }
    finally:
        repository.close()


def workflow_results(
    repository_path: Path,
    *,
    workflow_id: str,
    kind: str,
) -> tuple[FrozenPaperWorkflowRun, ...]:
    repository = AgentRepository(repository_path)
    try:
        published = {
            item.artifact_hash
            for item in repository.audit_events()
            if item.event == "PAPER_WORKFLOW_COMPLETED"
        }
        return tuple(
            sorted(
                (
                    item
                    for item in repository.list(FrozenPaperWorkflowRun)
                    if item.kind == kind
                    and item.workflow_id == workflow_id
                    and item.content_hash in published
                ),
                key=lambda item: item.created_at,
                reverse=True,
            )
        )
    finally:
        repository.close()


def load_workflow(repository: AgentRepository, workflow_id: str) -> PaperWorkflowInputs:
    if not workflow_id or workflow_id in {"last", "seed"}:
        raise DataIntegrityError(
            "WORKFLOW_INPUTS_REQUIRED: review a selected real portfolio, explicit paper cash "
            "and frozen arrival marks; prepare the paper workflow first"
        )
    try:
        item = repository.get(workflow_id, PaperWorkflowInputs)
    except KeyError:
        raise DataIntegrityError(
            "PAPER_WORKFLOW_NOT_FOUND: select a saved reviewed workflow"
        ) from None
    except ValueError:
        raise DataIntegrityError(
            "PAPER_WORKFLOW_SCHEMA_INCOMPATIBLE: preserve the archive and prepare new "
            "inputs with current parent and post-decision arrival requirements"
        ) from None
    # Verify every cited source still resolves; an arbitrary string is not provenance.
    for history_hash in item.arrival.history_hashes:
        repository.get(history_hash, FrozenMarketHistory)
    reconstructed = market_from_histories(
        repository,
        item.arrival.history_hashes,
        as_of=item.arrival.snapshot.as_of,
        persist=False,
    )
    if reconstructed.snapshot != item.arrival.snapshot:
        raise DataIntegrityError("ARRIVAL_SOURCE_BINDING_MISMATCH")
    from quantlab.app.research_workbench import ResearchRunContext, load_research_run

    research = load_research_run(repository.store.path, item.research_result_hash)
    context = repository.get(research.context.content_hash, ResearchRunContext)
    if research.content_hash != item.research_result_hash or context != research.context:
        raise DataIntegrityError("PAPER_RESEARCH_SOURCE_HASH_MISMATCH")
    for history_hash in context.history_hashes:
        if repository.get(history_hash, FrozenMarketHistory).content_hash != history_hash:
            raise DataIntegrityError("PAPER_RESEARCH_HISTORY_HASH_MISMATCH")
    if (
        item.decision.snapshot_id != research.context.input_hash
        or item.decision.decision_time != research.context.analytical_end
        or item.decision.experiment_id != research.run_id
    ):
        raise DataIntegrityError("DECISION_RESEARCH_CONTEXT_MISMATCH")
    capital = repository.get(item.capital_allocation_hash, FrozenCapitalAllocation)
    if (
        capital.research_result_hash != research.content_hash
        or capital.content_hash != item.capital_allocation_hash
        or capital.opening_cash != item.opening_account.equity
        or capital.allocation.decision != item.decision
        or capital.allocation.target != item.target
    ):
        raise DataIntegrityError("CAPITAL_WORKFLOW_BINDING_MISMATCH")
    if not any(
        event.event == "CAPITAL_COMPLETED" and event.artifact_hash == capital.content_hash
        for event in repository.audit_events(capital.allocation.decision.decision_id)
    ):
        raise DataIntegrityError("CAPITAL_NOT_PUBLISHED")
    return item.verified()


def _paper_result(
    repository: AgentRepository, workflow_id: str, result_hash: str = ""
) -> tuple[PaperOMSResult, str]:
    if result_hash:
        _, selected = restore_paper_checkpoint(repository, workflow_id, result_hash)
        return selected, result_hash
    published = {
        item.artifact_hash
        for item in repository.audit_events()
        if item.event == "PAPER_WORKFLOW_COMPLETED"
    }
    runs = [
        item
        for item in repository.list(FrozenPaperWorkflowRun)
        if item.workflow_id == workflow_id
        and item.kind == "paper_oms"
        and item.content_hash in published
    ]
    if not runs:
        raise DataIntegrityError("PAPER_RUN_REQUIRED: submit this reviewed paper workflow first")
    chosen = max(runs, key=lambda item: item.created_at)
    _, result = restore_paper_checkpoint(repository, workflow_id, chosen.content_hash)
    return result, chosen.content_hash


def restore_paper_checkpoint(
    repository: AgentRepository, workflow_id: str, result_hash: str
) -> tuple[PaperWorkflowInputs, PaperOMSResult]:
    """Reopen one published completed paper result without re-running or routing orders.

    This is a completed historical calculation, not a live account recovery or an
    in-flight OMS checkpoint. The caller must retain and specify both exact hashes.
    """
    from quantlab.backtest.spec import config_hash
    from quantlab.paper_oms.identity import hash_fill, hash_plan, hash_run

    if not result_hash or result_hash in {"last", "seed"}:
        raise DataIntegrityError("PAPER_CHECKPOINT_HASH_REQUIRED")
    inputs = load_workflow(repository, workflow_id)
    if inputs.content_hash != workflow_id:
        raise DataIntegrityError("PAPER_CHECKPOINT_WORKFLOW_HASH_MISMATCH")
    try:
        frozen = repository.get(result_hash, FrozenPaperWorkflowRun).verified()
    except (KeyError, ValueError):
        raise DataIntegrityError("PAPER_CHECKPOINT_MISSING_OR_CORRUPT") from None
    if (
        frozen.content_hash != result_hash
        or frozen.kind != "paper_oms"
        or frozen.workflow_id != workflow_id
        or frozen.parent_run_hash
        or frozen.mark_snapshot_hash
    ):
        raise DataIntegrityError("PAPER_CHECKPOINT_IDENTITY_MISMATCH")
    if not any(
        event.event == "PAPER_WORKFLOW_COMPLETED"
        and event.run_id == workflow_id
        and event.artifact_hash == result_hash
        for event in repository.audit_events(workflow_id)
    ):
        raise DataIntegrityError("PAPER_CHECKPOINT_NOT_PUBLISHED")
    if set(PaperOMSResult.model_fields) - frozen.result.keys():
        raise DataIntegrityError("PAPER_CHECKPOINT_INCOMPLETE")
    try:
        paper = PaperOMSResult.model_validate(frozen.result)
    except ValueError:
        raise DataIntegrityError("PAPER_CHECKPOINT_INCOMPLETE") from None
    run = paper.run
    if (
        paper.live_trading
        or run.live_trading
        or paper.decision_id != inputs.decision.decision_id
        or run.decision_hash != inputs.decision.decision_hash
        or run.snapshot_id != inputs.arrival.snapshot.snapshot_id
        or run.account_id != inputs.opening_account.account_id
        or paper.account.account_id != run.account_id
        or run.execution_policy_id != inputs.execution_policy_id
        or run.opening_account_hash != config_hash(inputs.opening_account.model_dump(mode="json"))
        or run.order_count != len(paper.orders)
        or run.fill_count != len(paper.fills)
        or run.run_hash != hash_run(run)
        or run.order_plan_hash != paper.plan.order_plan_hash
        or paper.plan.order_plan_hash != hash_plan(paper.plan)
        or any(
            fill.fill_hash != hash_fill(fill.model_copy(update={"fill_id": ""}))
            or fill.fill_id != f"PF-{fill.fill_hash[:12]}"
            for fill in paper.fills
        )
        or any(
            fill.order_id not in {order.order_id for order in paper.orders}
            for fill in paper.fills
        )
        or len({fill.fill_id for fill in paper.fills}) != len(paper.fills)
        or len({order.order_id for order in paper.orders}) != len(paper.orders)
    ):
        raise DataIntegrityError("PAPER_CHECKPOINT_STATE_MISMATCH")
    return inputs, paper


def _run_paper(inputs: PaperWorkflowInputs, *, persist_result: bool = True) -> PaperOMSResult:
    from quantlab.paper_oms.service import run_paper_oms

    return run_paper_oms(
        PaperOMSRequest(
            decision_id=inputs.decision.decision_id,
            account_id=inputs.opening_account.account_id,
            execution_policy_id=inputs.execution_policy_id,
            snapshot_id=inputs.arrival.snapshot.snapshot_id,
            as_of=inputs.arrival.snapshot.as_of,
            data_kind="REAL",
        ),
        decision=inputs.decision,
        target=inputs.target,
        account=inputs.opening_account,
        snapshot=inputs.arrival.snapshot,
        persist_result=persist_result,
    )


def execute_paper_workflow(
    job: Job,
    repository_path: Path,
    ledger_path: Path,
    fabric_root: Path | None = None,
) -> dict[str, Any]:
    """Background JobService adapter. All parameters are explicit selected identities."""
    if str(job.parameters.get("kind", "paper_oms")) in {"prepare", "capital"}:
        return _execute_paper_workflow(job, repository_path, ledger_path, fabric_root)
    repository = AgentRepository(repository_path)
    try:
        inputs = load_workflow(repository, str(job.parameters.get("workflow_id", "")))
    finally:
        repository.close()
    from quantlab.paper_oms.safety import sourced_simulation_scope

    with sourced_simulation_scope(inputs.content_hash):
        return _execute_paper_workflow(job, repository_path, ledger_path, fabric_root)


def _execute_paper_workflow(
    job: Job,
    repository_path: Path,
    ledger_path: Path,
    fabric_root: Path | None = None,
) -> dict[str, Any]:
    del fabric_root
    parameters = job.parameters
    kind = str(parameters.get("kind", "paper_oms"))
    if kind == "prepare":
        return prepare_workflow(
            repository_path=repository_path,
            ledger_path=ledger_path,
            research_result_hash=str(parameters.get("research_result_hash", "")),
            opening_cash=float(parameters.get("opening_cash", 0.0)),
            arrival_history_hashes=tuple(
                str(item) for item in parameters.get("arrival_history_hashes", ())
            ),
            reviewed=parameters.get("reviewed") is True,
            allow_unverified_liquidity=parameters.get("allow_unverified_liquidity") is True,
            execution_policy_id=str(parameters.get("execution_policy_id", "base")),
            publication_job=job,
        )
    if kind == "capital":
        return allocate_research_capital(
            repository_path=repository_path,
            ledger_path=ledger_path,
            research_result_hash=str(parameters.get("research_result_hash", "")),
            opening_cash=float(parameters.get("opening_cash", 0.0)),
            allow_unverified_liquidity=parameters.get("allow_unverified_liquidity") is True,
            publication_job=job,
        )
    repository = AgentRepository(repository_path)
    try:
        inputs = load_workflow(repository, str(parameters.get("workflow_id", "")))
        if job.cancel_event.is_set():
            return {"cancelled": True, "live_trading": False}
        parent_hash = ""
        mark_hash = ""
        mark_artifact = None
        if kind == "paper_oms":
            result = _run_paper(inputs, persist_result=False)
            payload = result.model_dump(mode="json")
            run_id = result.run.oms_run_id
        elif kind in {"monitoring", "tca"}:
            paper, parent_hash = _paper_result(
                repository, inputs.content_hash, str(parameters.get("paper_result_hash", ""))
            )
            if kind == "monitoring":
                from quantlab.monitoring.models import MonitoringRequest
                from quantlab.monitoring.service import run_monitoring

                mark_histories = tuple(
                    str(item) for item in parameters.get("mark_history_hashes", ())
                )
                if not mark_histories:
                    raise DataIntegrityError(
                        "SUBSEQUENT_REAL_MARKS_REQUIRED: select a later frozen history capture"
                    )
                mark = market_from_histories(repository, mark_histories, persist=False)
                if mark.snapshot.as_of <= inputs.arrival.snapshot.as_of:
                    raise DataIntegrityError(
                        "SUBSEQUENT_MARK_REQUIRED: arrival prices are not subsequent performance"
                    )
                monitored = run_monitoring(
                    MonitoringRequest(
                        oms_run_id=paper.run.oms_run_id, data_kind="REAL", as_of=mark.snapshot.as_of
                    ),
                    paper=paper,
                    decision=inputs.decision,
                    target=inputs.target,
                    snapshot=mark.snapshot,
                    arrival_snapshot=inputs.arrival.snapshot,
                    beginning_equity=inputs.opening_account.equity,
                    persist_result=False,
                )
                payload = monitored.model_dump(mode="json")
                run_id = monitored.run.monitoring_run_id
                mark_hash = mark.content_hash
                mark_artifact = mark
            else:
                from quantlab.tca.enums import TCAKind
                from quantlab.tca.models import TCARequest
                from quantlab.tca.service import run_tca

                tca = run_tca(
                    TCARequest(
                        oms_run_id=paper.run.oms_run_id,
                        kind=TCAKind.MODELLED,
                        data_kind="REAL",
                        as_of=inputs.arrival.snapshot.as_of,
                    ),
                    paper=paper,
                    target=inputs.target,
                    persist_result=False,
                )
                payload = tca.model_dump(mode="json")
                run_id = tca.run.tca_run_id
        elif kind in {"shadow", "twin"}:
            from quantlab.shadow.enums import ShadowMode
            from quantlab.shadow.models import ShadowRequest
            from quantlab.shadow.service import run_shadow_cycle

            original = None
            if kind == "twin":
                original_hash = str(parameters.get("original_run_hash", ""))
                originals = [
                    row
                    for row in workflow_results(
                        repository_path, workflow_id=inputs.content_hash, kind="shadow"
                    )
                    if not original_hash or row.content_hash == original_hash
                ]
                if not originals:
                    raise DataIntegrityError(
                        "PUBLISHED_SHADOW_RUN_REQUIRED: select this workflow's completed shadow run"
                    )
                original = max(originals, key=lambda row: row.created_at)

            request = ShadowRequest(
                mode=ShadowMode.RESEARCH_PAPER,
                decision_time=inputs.arrival.snapshot.as_of,
                available_time=inputs.arrival.snapshot.as_of,
                data_timestamp=inputs.arrival.snapshot.as_of,
                received_timestamp=inputs.arrival.snapshot.as_of,
                historical_replay=True,
                source_captured_at=inputs.arrival.snapshot.captured_at,
                data_kind="REAL",
                strategy_version=inputs.decision.strategy_id,
                execution_policy_id=inputs.execution_policy_id,
            )
            shadow = run_shadow_cycle(
                request,
                decision=inputs.decision,
                target=inputs.target,
                snapshot=inputs.arrival.snapshot,
                account=inputs.opening_account,
                persist_result=False,
            )
            if kind == "twin":
                assert original is not None
                parent_hash = original.content_hash
                expected = original.result
                comparisons = {
                    "snapshot": shadow.snapshot.snapshot_hash
                    == expected["snapshot"]["snapshot_hash"],
                    "target": shadow.cycle.target_portfolio_hash
                    == expected["cycle"]["target_portfolio_hash"],
                    "reconciliation": shadow.reconciliation.reconciliation_hash
                    == expected["reconciliation"]["reconciliation_hash"],
                    "cash": shadow.paper_account.cash == expected["paper_account"]["cash"],
                    "fills": [item.model_dump(mode="json") for item in shadow.fills]
                    == expected["fills"],
                }
                payload = {
                    "replay_status": "MATCH" if all(comparisons.values()) else "MISMATCH",
                    "checks": comparisons,
                    "original_run_hash": original.content_hash,
                    "replayed": shadow.model_dump(mode="json"),
                }
            else:
                payload = shadow.model_dump(mode="json")
            run_id = shadow.cycle.cycle_id
        else:
            raise DataIntegrityError(f"UNSUPPORTED_PAPER_WORKFLOW: {kind}")
        frozen = FrozenPaperWorkflowRun(
            created_at=datetime.now(UTC),
            kind=kind,  # type: ignore[arg-type]
            workflow_id=inputs.content_hash,
            parent_run_hash=parent_hash,
            mark_snapshot_hash=mark_hash,
            result=payload,
        )
        job.begin_publication()
        if mark_artifact is not None:
            repository.put(mark_artifact)
        repository.put(frozen)
        _append_workflow_ledger(frozen, inputs, ledger_path, run_id=run_id)
        repository.audit(
            "PAPER_WORKFLOW_COMPLETED",
            run_id=inputs.content_hash,
            now=frozen.created_at,
            artifact_hash=frozen.content_hash,
        )
        return {
            "kind": kind,
            "run_id": run_id,
            "workflow_id": inputs.content_hash,
            "result_hash": frozen.content_hash,
            "result": payload,
            "data_kind": "REAL",
            "historical_replay": True,
            "live_trading": False,
            "broker_write_enabled": False,
            "note": (
                "Sourced historical inputs with simulated execution. "
                "Not validated alpha or broker fills."
            ),
        }
    finally:
        repository.close()


def _append_workflow_ledger(
    frozen: FrozenPaperWorkflowRun,
    inputs: PaperWorkflowInputs,
    ledger_path: Path,
    *,
    run_id: str,
) -> None:
    from quantlab import __version__
    from quantlab.domain.models import ExperimentRun, ExperimentStatus
    from quantlab.models.registry import ExperimentLedger

    metrics: dict[str, float] = {}
    result = frozen.result
    if frozen.kind == "paper_oms":
        metrics = {
            "order_count": float(result["run"]["order_count"]),
            "fill_count": float(result["run"]["fill_count"]),
            "cash": float(result["account"]["cash"]),
            "equity": float(result["account"]["equity"]),
        }
    elif frozen.kind == "monitoring":
        metrics = {
            "pnl_total": float(result["pnl"]["pnl_total"]),
            "residual_pnl": float(result["pnl"]["residual_pnl"]),
        }
    elif frozen.kind == "tca" and result["shortfall"]["total"] is not None:
        metrics = {"shortfall": float(result["shortfall"]["total"])}
    row = ExperimentRun(
        id=f"{frozen.kind}-{frozen.content_hash[:20]}",
        name=f"{frozen.kind}:historical_replay",
        status=ExperimentStatus.COMPLETED,
        hypothesis=(
            "Sourced historical inputs; simulated non-routable paper accounting, "
            "not validated alpha."
        ),
        dataset_version=inputs.arrival.snapshot.snapshot_id,
        universe=sorted(inputs.target.weights),
        data_kind="REAL",
        snapshot_id=inputs.arrival.snapshot.snapshot_id,
        metrics=metrics,
        application_version=__version__,
        selection_stage=frozen.kind,
        research_type=frozen.kind,
        config_hash=frozen.content_hash,
        decision_id=inputs.decision.decision_id,
        decision_hash=inputs.decision.decision_hash,
        target_portfolio_hash=inputs.target.portfolio_hash,
        paper_account_id=inputs.opening_account.account_id,
        oms_run_id=run_id if frozen.kind == "paper_oms" else "",
        gate_outcome="NOT_TESTED",
        conclusion="Completed calculation, not independent validation or execution authorization.",
    )
    ExperimentLedger(ledger_path).append(row)
