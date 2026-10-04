"""Pure, versioned evidence scoring. LLM opinions never enter quantitative inputs."""

from datetime import UTC, datetime

from quantlab.agents.adjudication_contracts import (
    AdjudicationDecision,
    AdjudicationOutcome,
    AdjudicationPolicy,
    CanonicalMeasurement,
    ComponentDefinition,
    FrozenAdjudicationInput,
    FrozenGateReason,
    FrozenResearchGateEvidence,
    RoleAdjudicationEvidence,
    ScoreComponent,
)
from quantlab.agents.contracts import DataKind, EvidenceStatus, ResearchMode
from quantlab.agents.debate_contracts import DebateStatus
from quantlab.agents.hashing import digest
from quantlab.agents.tool_contracts import ToolName
from quantlab.domain.research import CheckResult
from quantlab.research.gate import GateOutcome, evaluate_research_gate

POLICY_TIME = datetime(2026, 10, 4, tzinfo=UTC)

# Exact metric, engine route, unit. Descriptive beta/regime labels are deliberately absent.
METRIC_SPECS: tuple[tuple[str, ToolName, str], ...] = (
    ("integrity", ToolName.RUN_VALIDATION, "boolean"),
    ("test_set_integrity", ToolName.RUN_VALIDATION, "boolean"),
    ("next_bar_fill", ToolName.RUN_BACKTEST, "boolean"),
    ("walk_forward_windows", ToolName.RUN_VALIDATION, "count"),
    ("oos_sharpe", ToolName.RUN_VALIDATION, "ratio"),
    ("cost_survival_20bps", ToolName.RUN_TCA, "boolean"),
    ("parameter_fragility", ToolName.RUN_VALIDATION, "boolean"),
    ("statistical_evidence", ToolName.RUN_ECONOMETRICS, "check"),
    ("multiple_testing", ToolName.RUN_ECONOMETRICS, "check"),
    ("n_hypotheses", ToolName.RUN_ECONOMETRICS, "count"),
    ("robustness", ToolName.RUN_VALIDATION, "proportion"),
    ("factor_independence", ToolName.QUERY_FACTOR, "proportion"),
    ("regime_fit", ToolName.QUERY_REGIME, "proportion"),
    ("model_evaluation", ToolName.RUN_MODEL_EVALUATION, "check"),
    ("ensemble_evaluation", ToolName.RUN_ENSEMBLE_EVALUATION, "check"),
    ("expected_edge_bps", ToolName.RUN_TCA, "bps"),
    ("estimated_cost_bps", ToolName.RUN_TCA, "bps"),
    ("liquidity", ToolName.RUN_TCA, "proportion"),
    ("canonical_contradiction", ToolName.RUN_VALIDATION, "proportion"),
    ("risk_clear", ToolName.RUN_RISK_ANALYSIS, "boolean"),
)


def default_adjudication_policy() -> AdjudicationPolicy:
    definitions = (
        ("research_quality", "research_quality", 0, 1, 0.10, False),
        ("oos_evidence", "oos_sharpe", 0, 2, 0.16, False),
        ("effect_magnitude", "expected_edge_bps", 0, 20, 0.10, False),
        ("robustness", "robustness", 0, 1, 0.12, False),
        ("factor_independence", "factor_independence", 0, 1, 0.10, False),
        ("regime_fit", "regime_fit", 0, 1, 0.08, False),
        ("cost_resilience", "net_edge_bps", 0, 20, 0.12, False),
        ("liquidity", "liquidity", 0, 1, 0.12, False),
        ("contradiction_severity", "canonical_contradiction", 0, 1, 0.10, True),
        ("agent_calibration", "agent_calibration", 0, 1, 0, False),
    )
    return AdjudicationPolicy(
        created_at=POLICY_TIME,
        policy_id="43-v1",
        schema_version="adjudication-v1",
        required_evidence=tuple(name for name, _, _ in METRIC_SPECS),
        components=tuple(
            ComponentDefinition(
                created_at=POLICY_TIME,
                name=name,
                metric=metric,
                lower=lower,
                upper=upper,
                weight=weight,
                inverse=inverse,
            )
            for name, metric, lower, upper, weight, inverse in definitions
        ),
        blocker_rules=(
            "INVALID_OR_STALE_DATA",
            "INCOMPLETE_DEBATE",
            "REQUIRED_EVIDENCE",
            "RESEARCH_GATE",
            "NET_EDGE",
            "LIQUIDITY",
            "RISK",
            "CONTRADICTION",
            "SYNTHETIC_OR_REPLAY",
        ),
        conflict_threshold=8,
        minimum_score=65,
        minimum_edge_bps=2,
        material_contradiction=0.5,
        minimum_liquidity=0.5,
        maximum_snapshot_age_seconds=300,
    )


def freeze_gate_evidence(
    measurements: tuple[CanonicalMeasurement, ...], data_kind: DataKind, now: datetime
) -> FrozenResearchGateEvidence:
    rows = {row.name: row for row in measurements}
    names = (
        "integrity",
        "next_bar_fill",
        "estimated_cost_bps",
        "walk_forward_windows",
        "oos_sharpe",
        "cost_survival_20bps",
        "parameter_fragility",
        "statistical_evidence",
        "n_hypotheses",
        "test_set_integrity",
        "multiple_testing",
    )
    source_hashes = tuple(sorted(rows[name].content_hash for name in names))
    missing = FrozenResearchGateEvidence(
        created_at=now, outcome=None, reasons=(), measurement_hashes=source_hashes
    )
    if any(rows[name].status is not EvidenceStatus.PASS for name in names):
        return missing
    values = {name: rows[name].value for name in names}
    numeric = tuple(
        name for name in names if name not in {"statistical_evidence", "multiple_testing"}
    )
    if any(values[name] is None for name in numeric):
        return missing
    # Values and integer/boolean domains were validated at the canonical capture boundary.
    gate = evaluate_research_gate(
        integrity_failed=values["integrity"] != 1,
        next_bar_fill=values["next_bar_fill"] == 1,
        cost_bps=float(values["estimated_cost_bps"] or 0),
        data_kind=data_kind.value.lower(),
        walk_forward_windows=int(values["walk_forward_windows"] or 0),
        oos_sharpe=values["oos_sharpe"],
        cost_still_positive_at_20bps=values["cost_survival_20bps"] == 1,
        parameter_fragile=values["parameter_fragility"] == 1,
        statistical_status=CheckResult.PASS,
        n_hypotheses=int(values["n_hypotheses"] or 0),
        test_used_for_selection=values["test_set_integrity"] != 1,
        multiple_testing_status=CheckResult.PASS,
    )
    return FrozenResearchGateEvidence(
        created_at=now,
        outcome=gate.outcome,
        measurement_hashes=source_hashes,
        reasons=tuple(
            FrozenGateReason(
                created_at=now, name=row.name, result=row.result, required=row.required
            )
            for row in gate.reasons
        ),
    )


def _role_scores(
    frame: FrozenAdjudicationInput,
    evidence: RoleAdjudicationEvidence,
    policy: AdjudicationPolicy,
) -> tuple[tuple[ScoreComponent, ...], tuple[str, ...]]:
    rows = {row.name: row for row in evidence.measurements}
    if set(rows) != {name for name, _, _ in METRIC_SPECS}:
        raise ValueError("canonical adjudication metric set mismatch")
    specs = {name: (tool, unit) for name, tool, unit in METRIC_SPECS}
    for name, row in rows.items():
        if (row.canonical_tool, row.unit) != specs[name]:
            raise ValueError("canonical adjudication route mismatch")
        if row.value is not None and (
            (row.unit == "boolean" and row.value not in {0, 1})
            or (row.unit == "count" and (row.value < 1 or row.value != int(row.value)))
            or (row.unit == "proportion" and not 0 <= row.value <= 1)
            or (row.name == "estimated_cost_bps" and row.value < 0)
        ):
            raise ValueError("invalid canonical metric domain")
    blockers: list[str] = []
    role = evidence.role.value
    for name in policy.required_evidence:
        required_row = rows.get(name)
        if (
            required_row is None
            or required_row.status is not EvidenceStatus.PASS
            or (required_row.value is None and required_row.unit != "check")
        ):
            status = required_row.status if required_row else "MISSING"
            blockers.append(f"{role}:REQUIRED_{name}:{status}")
    frozen_gate = freeze_gate_evidence(evidence.measurements, frame.data_kind, frame.created_at)
    if frozen_gate != evidence.research_gate:
        raise ValueError("canonical research gate derivation mismatch")
    gate = frozen_gate.outcome
    gate_reasons = tuple(
        row.name for row in frozen_gate.reasons if row.result is not CheckResult.PASS
    )
    refs = tuple(sorted({key for row in rows.values() for key in row.result_hashes}))
    gate_status = (
        EvidenceStatus.PASS if gate is GateOutcome.RESEARCH_CANDIDATE else EvidenceStatus.NOT_TESTED
    )
    if gate is not GateOutcome.RESEARCH_CANDIDATE:
        blockers.append(f"{role}:RESEARCH_GATE:{gate.value if gate else 'NOT_TESTED'}")
        blockers.extend(f"{role}:GATE_{reason}" for reason in gate_reasons)
    rows["research_quality"] = CanonicalMeasurement(
        created_at=frame.created_at,
        name="research_quality",
        canonical_tool=ToolName.RUN_VALIDATION,
        unit="proportion",
        status=gate_status,
        value=1 if gate_status is EvidenceStatus.PASS else None,
        result_hashes=refs,
    )
    gross, costs = rows["expected_edge_bps"], rows["estimated_cost_bps"]
    net = None
    if (
        gross.status is costs.status is EvidenceStatus.PASS
        and gross.value is not None
        and costs.value is not None
        and set(gross.result_hashes) & set(costs.result_hashes)
    ):
        net = gross.value - costs.value
        if net <= policy.minimum_edge_bps or costs.value <= 0:
            blockers.append(f"{role}:NO_COST_ADJUSTED_EDGE")
    else:
        blockers.append(f"{role}:COST_ADJUSTED_EDGE_UNKNOWN")
    rows["net_edge_bps"] = CanonicalMeasurement(
        created_at=frame.created_at,
        name="net_edge_bps",
        canonical_tool=ToolName.RUN_TCA,
        unit="bps",
        status=EvidenceStatus.PASS if net is not None else EvidenceStatus.NOT_TESTED,
        value=net,
        result_hashes=tuple(sorted(set(gross.result_hashes + costs.result_hashes))),
    )
    if rows["risk_clear"].status is not EvidenceStatus.PASS or rows["risk_clear"].value != 1:
        blockers.append(f"{role}:RISK_UNKNOWN_OR_BLOCKED")
    liquidity = rows["liquidity"]
    if (
        liquidity.status is not EvidenceStatus.PASS
        or liquidity.value is None
        or liquidity.value < policy.minimum_liquidity
    ):
        blockers.append(f"{role}:LIQUIDITY_UNKNOWN_OR_POOR")
    contradiction = rows["canonical_contradiction"]
    if contradiction.value is not None and contradiction.value >= policy.material_contradiction:
        blockers.append(f"{role}:MATERIAL_CANONICAL_CONTRADICTION")
    components = []
    for definition in policy.components:
        metric = rows.get(definition.metric)
        value = None
        status = metric.status if metric else EvidenceStatus.NOT_TESTED
        if metric and status is EvidenceStatus.PASS and metric.value is not None:
            value = min(
                1.0,
                max(0.0, (metric.value - definition.lower) / (definition.upper - definition.lower)),
            )
            value = 1 - value if definition.inverse else value
        components.append(
            ScoreComponent(
                created_at=frame.created_at,
                role=evidence.role,
                name=definition.name,
                status=status,
                normalized_value=value,
                weight=definition.weight,
                points=round(100 * definition.weight * (value or 0), 8),
                evidence_refs=metric.result_hashes if metric else (),
            )
        )
    return tuple(components), tuple(blockers)


def adjudicate(frame: FrozenAdjudicationInput, policy: AdjudicationPolicy) -> AdjudicationDecision:
    """Same frozen inputs/policy give byte-identical results; no clock, I/O or LLM."""
    frame, policy = frame.verified(), policy.verified()
    if frame.policy_hash != policy.content_hash:
        raise ValueError("adjudication policy identity mismatch")
    bull, bull_blocks = _role_scores(frame, frame.bull, policy)
    bear, bear_blocks = _role_scores(frame, frame.bear, policy)
    components = bull + bear
    blockers = list(bull_blocks + bear_blocks)
    warnings = [
        "RAW_CONFIDENCE_AND_PROSE_NOT_SCORED",
        "CALIBRATION_NOT_AVAILABLE_PHASE_48",
        "DESCRIPTIVE_BETA_IS_NOT_INDEPENDENT_EDGE",
        "DOMINANCE_IS_NOT_EXECUTION_AUTHORITY",
    ]
    stale = frame.created_at >= frame.expires_at or frame.data_quality != "valid"
    if frame.mode is not ResearchMode.REPLAY:
        stale = (
            stale
            or frame.data_freshness != "fresh"
            or (frame.created_at - frame.as_of).total_seconds()
            > policy.maximum_snapshot_age_seconds
        )
    if stale:
        blockers.append("INVALID_OR_STALE_DATA")
    if frame.debate_status is not DebateStatus.COMPLETE:
        blockers.append("INCOMPLETE_DEBATE")
    if frame.data_kind is DataKind.SYNTHETIC or frame.mode is ResearchMode.REPLAY:
        blockers.append("SYNTHETIC_OR_REPLAY_NOT_CURRENT_MARKET_EVIDENCE")
    bull_score = round(sum(row.points for row in bull), 8)
    bear_score = round(sum(row.points for row in bear), 8)
    outcome = AdjudicationOutcome.NO_TRADE
    if stale or "INCOMPLETE_DEBATE" in blockers:
        outcome = AdjudicationOutcome.INSUFFICIENT_DATA
    elif any(
        "REQUIRED_" in reason
        and not any(name in reason for name in ("REQUIRED_risk_clear:", "REQUIRED_liquidity:"))
        and reason.endswith(":FAIL")
        or ":GATE_" in reason
        or reason.endswith(":RESEARCH_GATE:reject")
        for reason in blockers
    ):
        outcome = AdjudicationOutcome.VALIDATION_BLOCKED
    elif any("NO_COST_ADJUSTED_EDGE" in reason for reason in blockers):
        outcome = AdjudicationOutcome.NO_EDGE
    elif any("MATERIAL_CANONICAL_CONTRADICTION" in reason for reason in blockers):
        outcome = AdjudicationOutcome.CONFLICTED
    elif any(
        (
            "REQUIRED_" in reason
            and not any(name in reason for name in ("REQUIRED_risk_clear:", "REQUIRED_liquidity:"))
        )
        or "COST_ADJUSTED_EDGE_UNKNOWN" in reason
        for reason in blockers
    ):
        outcome = AdjudicationOutcome.INSUFFICIENT_DATA
    elif any("RISK_UNKNOWN_OR_BLOCKED" in reason for reason in blockers):
        outcome = AdjudicationOutcome.RISK_BLOCKED
    elif any("LIQUIDITY_UNKNOWN_OR_POOR" in reason for reason in blockers):
        outcome = AdjudicationOutcome.LIQUIDITY_BLOCKED
    elif blockers:
        outcome = AdjudicationOutcome.NO_TRADE
    elif max(bull_score, bear_score) < policy.minimum_score:
        outcome = AdjudicationOutcome.LOW_CONFIDENCE
    elif abs(bull_score - bear_score) <= policy.conflict_threshold:
        outcome = AdjudicationOutcome.CONFLICTED
    else:
        outcome = (
            AdjudicationOutcome.BULL_DOMINANT
            if bull_score > bear_score
            else AdjudicationOutcome.BEAR_DOMINANT
        )
    semantic = {
        "policy_hash": policy.content_hash,
        "outcome": outcome,
        "scores": (bull_score, bear_score),
        "components": [
            (row.role, row.name, row.status, row.normalized_value, row.weight, row.points)
            for row in components
        ],
        "hard_blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
    }
    return AdjudicationDecision(
        created_at=frame.created_at,
        input_hash=frame.content_hash,
        transcript_hash=frame.transcript_hash,
        snapshot_hash=frame.snapshot_hash,
        policy_id=policy.policy_id,
        policy_hash=policy.content_hash,
        outcome=outcome,
        no_trade=outcome
        not in {AdjudicationOutcome.BULL_DOMINANT, AdjudicationOutcome.BEAR_DOMINANT},
        bull_score=bull_score,
        bear_score=bear_score,
        score_components=components,
        hard_blockers=tuple(sorted(set(blockers))),
        warnings=tuple(sorted(set(warnings))),
        evidence_refs=frame.evidence_refs,
        result_hash=digest(semantic),
    )
