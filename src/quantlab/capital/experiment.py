"""Capital-allocation experiments. Reuses the JSONL ledger. Not a second ledger."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.capital.allocator import AllocationResult, allocate
from quantlab.capital.definitions import AllocationRequest, CapitalPolicy
from quantlab.capital.integrity import CapitalLeakFlags
from quantlab.capital.library import seed_request
from quantlab.capital.memory import persist, register
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_from_result(result: AllocationResult, request: AllocationRequest) -> ExperimentRun:
    decision = result.decision
    status = (
        ExperimentStatus.PASSED
        if decision.decision_status.value not in {"rejected", "abstain"}
        else ExperimentStatus.FAILED
    )
    return ExperimentRun(
        id=decision.decision_id,
        name=f"capital:{decision.capital_policy_id}",
        hypothesis="Capital allocation is a research decision, not a broker order.",
        status=status,
        git_commit=git_commit(),
        dataset_version=request.snapshot_id,
        universe=sorted(request.scores),
        feature_versions={"capital_policy": decision.capital_policy_id},
        label_definition="not_applicable",
        hyperparameters={
            "sizing": decision.allocation_method,
            "kelly_fraction": "policy",
        },
        training_period="",
        validation_period="",
        test_period="",
        transaction_cost_bps=10.0,
        random_seed=0,
        hypothesis_id="H-MOM-001",
        dataset_id=request.dataset_checksum,
        snapshot_id=request.snapshot_id,
        data_kind=request.data_kind,
        metrics={
            "gross_target": decision.gross_target,
            "net_target": decision.net_target,
            "turnover": decision.turnover_estimate,
            "confidence": decision.confidence,
        },
        integrity=result.integrity.as_str_map(),
        application_version=__version__,
        conclusion=(
            f"status={decision.decision_status.value}; synthetic diagnostics only"
            if request.data_kind == "synthetic"
            else f"status={decision.decision_status.value}"
        ),
        config_hash=decision.decision_hash,
        selection_stage="capital_allocation",
        gate_outcome=request.gate.outcome.value if request.gate else "",
        git_dirty=git_dirty(),
        python_version=environment().get("python", ""),
        tested_count=1,
        selection_policy="capital_policy",
        research_type="capital_allocation",
        decision_id=decision.decision_id,
        capital_policy_id=decision.capital_policy_id,
        risk_budget_id=decision.risk_policy_id,
        allocation_method=decision.allocation_method,
        decision_status=decision.decision_status.value,
        abstention_code=decision.abstention_code.value,
        capital_state=decision.capital_state.value,
        allocation_confidence=decision.confidence,
        target_portfolio_hash=result.target.portfolio_hash,
        knowledge_snapshot_id=request.knowledge_snapshot_id,
    )


def run_allocation_experiment(
    request: AllocationRequest | None = None,
    *,
    ledger_path: Path,
    policy: CapitalPolicy | None = None,
    append: bool = True,
    leaks: CapitalLeakFlags | None = None,
) -> tuple[AllocationResult, ExperimentRun]:
    used = request or seed_request()
    result = allocate(used, policy=policy, leaks=leaks)
    register(result)
    persist(ledger_path.with_name("capital_decisions.json"))
    run = _run_from_result(result, used)
    if append:
        ExperimentLedger(ledger_path).append(run)
    return result, run


def run_named_allocation(
    policy_id: str = "CAP-RESEARCH-001",
    *,
    ledger_path: Path,
    portfolio_id: str = "mom20_topn",
    append: bool = True,
) -> tuple[AllocationResult, ExperimentRun]:
    request = seed_request(policy_id=policy_id)
    request = request.model_copy(update={"portfolio_spec_id": portfolio_id})
    return run_allocation_experiment(request, ledger_path=ledger_path, append=append)
