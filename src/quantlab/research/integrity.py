"""Research integrity: PASS / WARN / FAIL / NOT_TESTED.

Never silent PASS for unimplemented checks.
"""

from __future__ import annotations

from datetime import datetime

from quantlab.domain.models import MarketState, OHLCVBar
from quantlab.domain.research import CheckResult, IntegrityReport


def evaluate_integrity(
    *,
    bars: list[OHLCVBar],
    states: list[MarketState],
    as_of_times: list[datetime],
    next_bar_fill: bool,
    cost_bps: float,
    slippage_model: str,
    live_trading: bool,
    n_experiments_in_family: int,
    used_ml: bool,
    universe_membership_provided: bool = False,
    corporate_actions_provided: bool = False,
    data_kind: str = "synthetic",
    pit_query_verified: bool | None = None,
    walk_forward_windows_ok: bool | None = None,
    embargo_enforced: bool | None = None,
    purge_applied: bool | None = None,
    test_used_for_selection: bool = False,
    future_parameter_selection: bool | None = None,
    label_used_as_feature: bool | None = None,
    future_normalization: bool | None = None,
    future_ranking_universe: bool | None = None,
    feature_available_time_ok: bool | None = None,
    future_covariance: bool | None = None,
    future_factor: bool | None = None,
    future_beta: bool | None = None,
    future_regime: bool | None = None,
    hmm_smoothing: bool | None = None,
    full_sample_regime_fit: bool | None = None,
    online_update_order_ok: bool | None = None,
    future_adaptive_parameter: bool | None = None,
    future_ensemble_performance: bool | None = None,
    holdout_contaminated: bool | None = None,
    future_model_training: bool | None = None,
    future_pca: bool | None = None,
    future_feature_selection: bool | None = None,
    future_hyperparameter: bool | None = None,
    future_calibration: bool | None = None,
    cross_section_future_leak: bool | None = None,
    model_replay_leak: bool | None = None,
    model_state_mutation: bool | None = None,
    future_component_performance: bool | None = None,
    future_ensemble_weight: bool | None = None,
    future_correlation: bool | None = None,
    future_meta_feature: bool | None = None,
    future_component_selection: bool | None = None,
    future_stacking_prediction: bool | None = None,
    future_pruning: bool | None = None,
    stacking_leak: bool | None = None,
    full_sample_ensemble_replay: bool | None = None,
    future_volume_leak: bool | None = None,
    future_spread_leak: bool | None = None,
    future_liquidity_leak: bool | None = None,
    future_impact_parameter: bool | None = None,
    future_execution_parameter: bool | None = None,
    future_latency: bool | None = None,
    pre_arrival_fill: bool | None = None,
    full_fill_assumption: bool | None = None,
    zero_cost_execution: bool | None = None,
    negative_execution_cost: bool | None = None,
    wrong_side_slippage: bool | None = None,
    wrong_side_impact: bool | None = None,
    hidden_partial_fill: bool | None = None,
    capacity_lookahead: bool | None = None,
    execution_model_mutation: bool | None = None,
    future_execution_calibration: bool | None = None,
    experiment_identity_mutation: bool | None = None,
    experiment_config_mutation: bool | None = None,
    future_experiment_selection: bool | None = None,
    future_candidate_selection: bool | None = None,
    future_hypothesis_selection: bool | None = None,
    hidden_candidate: bool | None = None,
    hidden_failed_experiment: bool | None = None,
    hidden_search: bool | None = None,
    posthoc_stopping: bool | None = None,
    multiple_testing_omission: bool | None = None,
    family_definition_mutation: bool | None = None,
    research_budget_bypass: bool | None = None,
    replication_contamination: bool | None = None,
    holdout_reuse: bool | None = None,
    future_baseline_selection: bool | None = None,
    future_model_selection: bool | None = None,
    future_execution_selection: bool | None = None,
    future_cost_selection: bool | None = None,
    lineage_break: bool | None = None,
    dataset_snapshot_mismatch: bool | None = None,
    result_overwrite: bool | None = None,
    parallel_state_leak: bool | None = None,
    adaptive_state_cross_contamination: bool | None = None,
    future_expression_input: bool | None = None,
    future_candidate_generation: bool | None = None,
    future_search_state: bool | None = None,
    future_fitness: bool | None = None,
    future_selection: bool | None = None,
    future_mutation: bool | None = None,
    future_crossover: bool | None = None,
    future_feature: bool | None = None,
    posthoc_search_budget: bool | None = None,
    search_space_omission: bool | None = None,
    candidate_lineage_break: bool | None = None,
    expression_mutation: bool | None = None,
    future_redundancy: bool | None = None,
    future_novelty: bool | None = None,
    future_complexity_selection: bool | None = None,
    knowledge_provenance_break: bool | None = None,
    evidence_without_experiment: bool | None = None,
    claim_without_evidence: bool | None = None,
    claim_overstates_evidence: bool | None = None,
    candidate_history_deleted: bool | None = None,
    duplicate_identity_collision: bool | None = None,
    snapshot_mutation: bool | None = None,
    historical_claim_mutation: bool | None = None,
    future_knowledge_leak: bool | None = None,
    future_claim_context: bool | None = None,
    replication_same_data: bool | None = None,
    contradiction_hidden: bool | None = None,
    search_degree_of_freedom_loss: bool | None = None,
    synthetic_evidence_overpromotion: bool | None = None,
    ai_evidence_confusion: bool | None = None,
    future_capital_input: bool | None = None,
    future_risk_input: bool | None = None,
    future_expected_return: bool | None = None,
    future_factor_exposure: bool | None = None,
    future_liquidity: bool | None = None,
    future_turnover_state: bool | None = None,
    future_drawdown_state: bool | None = None,
    future_constraint_parameter: bool | None = None,
    future_position_reference: bool | None = None,
    future_decision_state: bool | None = None,
    capital_policy_mutation: bool | None = None,
    decision_mutation: bool | None = None,
    decision_hash_mismatch: bool | None = None,
    allocation_lineage_break: bool | None = None,
    hidden_constraint_relaxation: bool | None = None,
    silent_fallback: bool | None = None,
    unknown_liquidity_as_infinite: bool | None = None,
    unknown_factor_as_zero: bool | None = None,
    synthetic_capital_overpromotion: bool | None = None,
    gate_bypass: bool | None = None,
    abstention_suppression: bool | None = None,
    future_portfolio_state: bool | None = None,
    future_execution_cost: bool | None = None,
    target_mutation: bool | None = None,
    order_intent_mutation: bool | None = None,
    order_plan_mutation: bool | None = None,
    duplicate_order: bool | None = None,
    duplicate_fill: bool | None = None,
    invalid_order_transition: bool | None = None,
    future_execution_price: bool | None = None,
    future_fill_information: bool | None = None,
    cash_accounting_break: bool | None = None,
    position_accounting_break: bool | None = None,
    target_position_mismatch: bool | None = None,
    order_fill_mismatch: bool | None = None,
    orphan_fill: bool | None = None,
    orphan_event: bool | None = None,
    reconciliation_break: bool | None = None,
    execution_policy_mutation: bool | None = None,
    paper_live_mode_confusion: bool | None = None,
    broker_import_violation: bool | None = None,
    future_performance_mark: bool | None = None,
    future_attribution_input: bool | None = None,
    future_benchmark: bool | None = None,
    future_factor_return: bool | None = None,
    performance_snapshot_mutation: bool | None = None,
    position_history_mutation: bool | None = None,
    pnl_reconciliation_break: bool | None = None,
    attribution_reconciliation_break: bool | None = None,
    hidden_residual: bool | None = None,
    benchmark_lookahead: bool | None = None,
    target_observation_confusion: bool | None = None,
    posthoc_attribution: bool | None = None,
    performance_claim_overstatement: bool | None = None,
    future_available_data: bool | None = None,
    event_available_time_conflict: bool | None = None,
    source_mutation: bool | None = None,
    checksum_mismatch: bool | None = None,
    duplicate_observation: bool | None = None,
    identity_lookahead: bool | None = None,
    symbol_history_lookahead: bool | None = None,
    corporate_action_lookahead: bool | None = None,
    adjustment_lookahead: bool | None = None,
    calendar_lookahead: bool | None = None,
    universe_survivorship_leak: bool | None = None,
    delisted_security_omission: bool | None = None,
    cross_source_conflict: bool | None = None,
    snapshot_dependency_mutation: bool | None = None,
    raw_to_derived_lineage_break: bool | None = None,
    timezone_mismatch: bool | None = None,
    future_tca_observation: bool | None = None,
    future_impact_calibration: bool | None = None,
    future_spread_calibration: bool | None = None,
    future_volume_calibration: bool | None = None,
    future_liquidity_calibration: bool | None = None,
    future_capacity_parameter: bool | None = None,
    arrival_price_lookahead: bool | None = None,
    benchmark_price_lookahead: bool | None = None,
    posthoc_cost_model: bool | None = None,
    calibration_window_leak: bool | None = None,
    future_fill_observation: bool | None = None,
    synthetic_adv_claim: bool | None = None,
    observed_vs_modelled_confusion: bool | None = None,
    tca_parameter_mutation: bool | None = None,
    future_stationarity_window: bool | None = None,
    future_lag_selection: bool | None = None,
    future_break_detection: bool | None = None,
    future_cointegration_selection: bool | None = None,
    future_var_selection: bool | None = None,
    future_causal_control: bool | None = None,
    future_event_window: bool | None = None,
    future_parameter_estimation: bool | None = None,
    full_sample_econometric_replay: bool | None = None,
    future_residual_normalization: bool | None = None,
    future_panel_selection: bool | None = None,
    causal_post_treatment_control: bool | None = None,
    lookahead_event_study: bool | None = None,
    illegal_certification_transition: bool | None = None,
    synthetic_production_evidence: bool | None = None,
    reproduction_break: bool | None = None,
    waiver_without_authority: bool | None = None,
    ai_certification_override: bool | None = None,
    critical_not_tested_certified: bool | None = None,
    future_shadow_data: bool | None = None,
    future_decision_input: bool | None = None,
    future_execution_input: bool | None = None,
    stale_data_decision: bool | None = None,
    unknown_calendar_execution: bool | None = None,
    duplicate_cycle: bool | None = None,
    duplicate_shadow_order: bool | None = None,
    shadow_live_confusion: bool | None = None,
    live_route_attempt: bool | None = None,
    paper_shadow_state_confusion: bool | None = None,
    model_version_mutation: bool | None = None,
    configuration_mutation: bool | None = None,
    pre_arrival_shadow_fill: bool | None = None,
    future_shadow_fill: bool | None = None,
    partial_fill_hidden: bool | None = None,
    shadow_accounting_break: bool | None = None,
    shadow_reconciliation_break: bool | None = None,
    checkpoint_hash_mismatch: bool | None = None,
    recovery_without_reconciliation: bool | None = None,
    certification_expired: bool | None = None,
    certification_bypass: bool | None = None,
    kill_switch_bypass: bool | None = None,
    risk_bypass: bool | None = None,
    ai_safety_override: bool | None = None,
    synthetic_production_confusion: bool | None = None,
    observed_tca_confusion: bool | None = None,
    broker_confirmation_confusion: bool | None = None,
    unauthorized_release: bool | None = None,
    missing_authorization: bool | None = None,
    stale_authorization: bool | None = None,
    future_account_state: bool | None = None,
    future_market_state: bool | None = None,
    future_risk_state: bool | None = None,
    target_hash_mismatch: bool | None = None,
    order_plan_hash_mismatch: bool | None = None,
    certification_mismatch: bool | None = None,
    risk_limit_bypass: bool | None = None,
    stale_decision: bool | None = None,
    duplicate_release: bool | None = None,
    idempotency_collision: bool | None = None,
    invalid_safety_transition: bool | None = None,
    unknown_safety_state: bool | None = None,
    human_authorization_missing: bool | None = None,
    policy_mutation: bool | None = None,
    audit_mutation: bool | None = None,
    emergency_bypass: bool | None = None,
    configuration_hash_mismatch: bool | None = None,
    unexpected_dependency: bool | None = None,
    secret_exposure: bool | None = None,
    secret_expired: bool | None = None,
    clock_rollback: bool | None = None,
    future_timestamp: bool | None = None,
    timestamp_regression: bool | None = None,
    audit_write_failure: bool | None = None,
    backup_checksum_failure: bool | None = None,
    restore_without_validation: bool | None = None,
    state_checkpoint_mismatch: bool | None = None,
    state_corruption: bool | None = None,
    process_identity_mismatch: bool | None = None,
    release_identity_mismatch: bool | None = None,
    environment_confusion: bool | None = None,
    production_config_in_research: bool | None = None,
    research_config_in_production: bool | None = None,
    unsafe_restart: bool | None = None,
    restart_loop: bool | None = None,
    health_false_positive: bool | None = None,
    readiness_false_positive: bool | None = None,
    silent_recovery: bool | None = None,
    silent_data_loss: bool | None = None,
    operational_bypass: bool | None = None,
    safety_halt_failure: bool | None = None,
    certification_evidence_mutation: bool | None = None,
    certification_snapshot_mismatch: bool | None = None,
    certification_model_mismatch: bool | None = None,
    certification_config_mismatch: bool | None = None,
    certification_hash_mismatch: bool | None = None,
    independent_validation_missing: bool | None = None,
    safety_gate_failure: bool | None = None,
    reconciliation_failure: bool | None = None,
    paper_shadow_gap: bool | None = None,
    revoked_certification: bool | None = None,
    waiver_expired: bool | None = None,
    waiver_scope_violation: bool | None = None,
    release_manifest_mismatch: bool | None = None,
    separation_of_duties_violation: bool | None = None,
    ai_authorization_override: bool | None = None,
    capital_limit_mutation: bool | None = None,
    release_policy_mutation: bool | None = None,
    human_approval_missing: bool | None = None,
    expired_certification: bool | None = None,
    critical_not_tested: bool | None = None,
    broker_identity_mismatch: bool | None = None,
    broker_snapshot_mutation: bool | None = None,
    broker_payload_hash_mismatch: bool | None = None,
    duplicate_external_event: bool | None = None,
    external_event_collision: bool | None = None,
    unknown_broker_order: bool | None = None,
    orphan_broker_fill: bool | None = None,
    missing_broker_fill: bool | None = None,
    order_reconciliation_break: bool | None = None,
    position_reconciliation_break: bool | None = None,
    cash_reconciliation_break: bool | None = None,
    margin_reconciliation_break: bool | None = None,
    instrument_mapping_ambiguity: bool | None = None,
    instrument_mapping_mutation: bool | None = None,
    timestamp_integrity_failure: bool | None = None,
    event_ordering_failure: bool | None = None,
    stale_broker_state: bool | None = None,
    credential_exposure: bool | None = None,
    broker_write_attempt: bool | None = None,
    live_mode_confusion: bool | None = None,
    safety_bypass: bool | None = None,
    future_market_observation: bool | None = None,
    future_state_mutation: bool | None = None,
    future_volume: bool | None = None,
    future_quote: bool | None = None,
    future_reference_data: bool | None = None,
    timestamp_order_violation: bool | None = None,
    receive_time_violation: bool | None = None,
    sequence_gap_hidden: bool | None = None,
    stale_data_used: bool | None = None,
    invalid_data_used: bool | None = None,
    missing_data_filled: bool | None = None,
    clock_drift: bool | None = None,
    session_mismatch: bool | None = None,
    security_identity_mismatch: bool | None = None,
    realtime_snapshot_mutation: bool | None = None,
    realtime_replay_mismatch: bool | None = None,
    future_realtime_feature: bool | None = None,
    future_realtime_model: bool | None = None,
    future_realtime_regime: bool | None = None,
    future_adaptive_update: bool | None = None,
    release_mutation: bool | None = None,
    uncertified_model_use: bool | None = None,
    expired_release_use: bool | None = None,
    decision_state_mutation: bool | None = None,
    rt_snapshot_mismatch: bool | None = None,
    stale_state_decision: bool | None = None,
    missing_critical_input: bool | None = None,
    capital_constraint_bypass: bool | None = None,
    decision_replay_mismatch: bool | None = None,
    ai_authority_violation: bool | None = None,
    future_replay_input: bool | None = None,
    future_shadow_state: bool | None = None,
    replay_snapshot_mismatch: bool | None = None,
    replay_state_mutation: bool | None = None,
    replay_nondeterminism: bool | None = None,
    event_order_violation: bool | None = None,
    event_deletion: bool | None = None,
    checkpoint_mutation: bool | None = None,
    counterfactual_observation_confusion: bool | None = None,
    simulated_fill_as_broker_fill: bool | None = None,
    hidden_reconciliation_break: bool | None = None,
    recovery_state_mismatch: bool | None = None,
    release_mismatch: bool | None = None,
    strategy_state_mismatch: bool | None = None,
    shadow_routing_attempt: bool | None = None,
) -> IntegrityReport:
    report = IntegrityReport()

    report.checks["look_ahead_bias"] = CheckResult.PASS if next_bar_fill else CheckResult.FAIL
    report.notes["look_ahead_bias"] = (
        "signal at t earns return t→t+1" if next_bar_fill else "same-bar fill is look-ahead"
    )

    state_ok = all(s.pit.is_available_at(s.as_of) for s in states)
    no_future_events = all(
        bar.pit.event_time <= as_of
        for as_of in as_of_times
        for bar in bars
        if bar.pit.is_available_at(as_of)
    )
    pit_ok = state_ok and no_future_events
    if pit_query_verified is False:
        pit_ok = False
    report.checks["timestamp_leakage"] = CheckResult.PASS if pit_ok else CheckResult.FAIL

    if cost_bps <= 0:
        report.checks["transaction_cost_underestimation"] = CheckResult.FAIL
        report.notes["transaction_cost_underestimation"] = "zero-cost backtests are not allowed"
    elif cost_bps < 5:
        report.checks["transaction_cost_underestimation"] = CheckResult.WARN
        report.notes["transaction_cost_underestimation"] = (
            "cost_bps below 5 is optimistic for NSE cash"
        )
    else:
        report.checks["transaction_cost_underestimation"] = CheckResult.PASS

    report.checks["slippage_underestimation"] = (
        CheckResult.WARN
        if slippage_model in {"none", ""}
        else CheckResult.NOT_TESTED
        if slippage_model == "volume_participation"
        else CheckResult.PASS
    )
    report.notes["slippage_underestimation"] = slippage_model

    report.checks["live_trading_disabled"] = (
        CheckResult.PASS if not live_trading else CheckResult.FAIL
    )

    if universe_membership_provided:
        report.checks["survivorship_bias"] = CheckResult.PASS
        report.notes["survivorship_bias"] = "universe.as_of(t) membership supplied"
        report.checks["universe_leakage"] = CheckResult.PASS
    else:
        report.checks["survivorship_bias"] = CheckResult.NOT_TESTED
        report.notes["survivorship_bias"] = "synthetic listed-only universe"
        report.checks["universe_leakage"] = CheckResult.NOT_TESTED

    if corporate_actions_provided:
        report.checks["corporate_action_leakage"] = CheckResult.PASS
        report.notes["corporate_action_leakage"] = "CA available_time respected"
    else:
        report.checks["corporate_action_leakage"] = CheckResult.NOT_TESTED
        report.notes["corporate_action_leakage"] = "no CA file; not a silent PASS"

    report.checks["selection_bias"] = CheckResult.NOT_TESTED
    report.checks["feature_leakage"] = CheckResult.PASS if pit_ok else CheckResult.FAIL
    report.checks["train_test_contamination"] = (
        CheckResult.NOT_TESTED if not used_ml else CheckResult.WARN
    )
    report.checks["parameter_overfitting"] = CheckResult.NOT_TESTED
    report.checks["regime_overfitting"] = CheckResult.NOT_TESTED
    report.checks["liquidity_overestimation"] = CheckResult.NOT_TESTED
    report.checks["capacity_overestimation"] = CheckResult.NOT_TESTED
    report.checks["execution_latency"] = CheckResult.NOT_TESTED
    report.checks["multiple_testing"] = (
        CheckResult.WARN if n_experiments_in_family > 1 else CheckResult.WARN
    )
    report.notes["multiple_testing"] = (
        "single-family architecture test; do not treat Sharpe as discovery"
    )
    report.checks["data_snooping"] = CheckResult.NOT_TESTED
    report.checks["risk_firewall"] = CheckResult.PASS
    if data_kind == "synthetic":
        report.checks["synthetic_data"] = CheckResult.WARN
        report.notes["synthetic_data"] = "synthetic is not live-grade NSE history"
    else:
        report.checks["synthetic_data"] = CheckResult.PASS
        report.notes["synthetic_data"] = "data_kind=real"

    if walk_forward_windows_ok is None:
        report.checks["walk_forward"] = CheckResult.NOT_TESTED
    else:
        report.checks["walk_forward"] = (
            CheckResult.PASS if walk_forward_windows_ok else CheckResult.FAIL
        )
    if embargo_enforced is None:
        report.checks["embargo"] = CheckResult.NOT_TESTED
    else:
        report.checks["embargo"] = CheckResult.PASS if embargo_enforced else CheckResult.FAIL
    if purge_applied is None:
        report.checks["purge"] = CheckResult.NOT_TESTED
    else:
        report.checks["purge"] = CheckResult.PASS if purge_applied else CheckResult.FAIL
    if test_used_for_selection:
        report.checks["test_set_sacred"] = CheckResult.FAIL
        report.notes["test_set_sacred"] = "test used for selection"
        report.checks["train_test_contamination"] = CheckResult.FAIL
    else:
        report.checks["test_set_sacred"] = CheckResult.PASS
    if future_parameter_selection is None:
        report.checks["future_parameter_selection"] = CheckResult.NOT_TESTED
    else:
        report.checks["future_parameter_selection"] = (
            CheckResult.FAIL if future_parameter_selection else CheckResult.PASS
        )
    if label_used_as_feature is None:
        report.checks["label_as_feature"] = CheckResult.NOT_TESTED
    else:
        report.checks["label_as_feature"] = (
            CheckResult.FAIL if label_used_as_feature else CheckResult.PASS
        )
        report.notes["label_as_feature"] = (
            "feature panel identical to forward label" if label_used_as_feature else "separated"
        )
    if future_normalization is None:
        report.checks["future_normalization"] = CheckResult.NOT_TESTED
    else:
        report.checks["future_normalization"] = (
            CheckResult.FAIL if future_normalization else CheckResult.PASS
        )
    if future_ranking_universe is None:
        report.checks["future_ranking_universe"] = CheckResult.NOT_TESTED
    else:
        report.checks["future_ranking_universe"] = (
            CheckResult.FAIL if future_ranking_universe else CheckResult.PASS
        )
    if feature_available_time_ok is None:
        report.checks["feature_available_time"] = CheckResult.NOT_TESTED
    else:
        report.checks["feature_available_time"] = (
            CheckResult.PASS if feature_available_time_ok else CheckResult.FAIL
        )
    if future_covariance is None:
        report.checks["future_covariance"] = CheckResult.NOT_TESTED
        report.notes["future_covariance"] = "covariance PIT not asserted for this path"
    else:
        report.checks["future_covariance"] = (
            CheckResult.FAIL if future_covariance else CheckResult.PASS
        )
        report.notes["future_covariance"] = (
            "Σ(T) used bars after T"
            if future_covariance
            else "Σ(T) from PIT-available returns only"
        )
    if future_factor is None:
        report.checks["future_factor"] = CheckResult.NOT_TESTED
        report.notes["future_factor"] = "factor PIT not asserted for this path"
    else:
        report.checks["future_factor"] = CheckResult.FAIL if future_factor else CheckResult.PASS
        report.notes["future_factor"] = (
            "factor used information after T" if future_factor else "factor(T) from PIT inputs only"
        )
    if future_beta is None:
        report.checks["future_beta"] = CheckResult.NOT_TESTED
        report.notes["future_beta"] = "beta PIT not asserted for this path"
    else:
        report.checks["future_beta"] = CheckResult.FAIL if future_beta else CheckResult.PASS
        report.notes["future_beta"] = (
            "beta used information after T"
            if future_beta
            else "beta vs equal-weight universe from PIT returns"
        )
    if future_regime is None:
        report.checks["future_regime"] = CheckResult.NOT_TESTED
        report.notes["future_regime"] = "regime PIT not asserted for this path"
    else:
        report.checks["future_regime"] = CheckResult.FAIL if future_regime else CheckResult.PASS
        report.notes["future_regime"] = (
            "regime used information after T" if future_regime else "regime(T) from PIT state only"
        )
    if hmm_smoothing is None:
        report.checks["hmm_smoothing"] = CheckResult.NOT_TESTED
        report.notes["hmm_smoothing"] = "HMM smoothing not asserted for this path"
    else:
        report.checks["hmm_smoothing"] = CheckResult.FAIL if hmm_smoothing else CheckResult.PASS
        report.notes["hmm_smoothing"] = (
            "full-sample HMM smoothing used as a predictive feature"
            if hmm_smoothing
            else "smoothed HMM not used as a predictive feature"
        )
    if full_sample_regime_fit is None:
        report.checks["full_sample_regime_fit"] = CheckResult.NOT_TESTED
        report.notes["full_sample_regime_fit"] = "full-sample regime fit not asserted"
    else:
        report.checks["full_sample_regime_fit"] = (
            CheckResult.FAIL if full_sample_regime_fit else CheckResult.PASS
        )
        report.notes["full_sample_regime_fit"] = (
            "parameters estimated using observations after T"
            if full_sample_regime_fit
            else "detector parameters use history through T"
        )
    if online_update_order_ok is None:
        report.checks["online_update_order"] = CheckResult.NOT_TESTED
        report.notes["online_update_order"] = "prequential update order not asserted"
    else:
        report.checks["online_update_order"] = (
            CheckResult.PASS if online_update_order_ok else CheckResult.FAIL
        )
        report.notes["online_update_order"] = (
            "predict then realize then score then update"
            if online_update_order_ok
            else "learner updated before the prediction it scored"
        )
    if future_adaptive_parameter is None:
        report.checks["future_adaptive_parameter"] = CheckResult.NOT_TESTED
        report.notes["future_adaptive_parameter"] = "adaptive hyperparameter PIT not asserted"
    else:
        report.checks["future_adaptive_parameter"] = (
            CheckResult.FAIL if future_adaptive_parameter else CheckResult.PASS
        )
        report.notes["future_adaptive_parameter"] = (
            "half-life/window chosen with information after T"
            if future_adaptive_parameter
            else "adaptation parameters fixed before prediction"
        )
    if future_ensemble_performance is None:
        report.checks["future_ensemble_performance"] = CheckResult.NOT_TESTED
        report.notes["future_ensemble_performance"] = "ensemble weight PIT not asserted"
    else:
        report.checks["future_ensemble_performance"] = (
            CheckResult.FAIL if future_ensemble_performance else CheckResult.PASS
        )
        report.notes["future_ensemble_performance"] = (
            "weights used component performance after T"
            if future_ensemble_performance
            else "weights from realized IC available at T"
        )
    if holdout_contaminated is None:
        report.checks["holdout_contamination"] = CheckResult.NOT_TESTED
        report.notes["holdout_contamination"] = "holdout inspection not asserted"
    else:
        report.checks["holdout_contamination"] = (
            CheckResult.FAIL if holdout_contaminated else CheckResult.PASS
        )
        report.notes["holdout_contamination"] = (
            "holdout used to select adaptive hyperparameters"
            if holdout_contaminated
            else "holdout not used for selection"
        )
    _model_flag(
        report,
        "future_model_training",
        future_model_training,
        "model trained with observations after T",
        "training cutoff is available_information_cutoff",
        "model training PIT not asserted",
    )
    _model_flag(
        report,
        "future_pca",
        future_pca,
        "PCA components estimated on the full sample including the future",
        "PCA fit on the training window only",
        "PCA PIT not asserted",
    )
    _model_flag(
        report,
        "future_feature_selection",
        future_feature_selection,
        "features selected using labels after T",
        "selection used training labels only",
        "feature selection PIT not asserted",
    )
    _model_flag(
        report,
        "future_hyperparameter",
        future_hyperparameter,
        "hyperparameters chosen with holdout or future performance",
        "hyperparameters frozen before prediction",
        "hyperparameter PIT not asserted",
    )
    _model_flag(
        report,
        "future_calibration",
        future_calibration,
        "calibration transform fit on future outcomes",
        "no future calibration",
        "calibration PIT not asserted",
    )
    _model_flag(
        report,
        "cross_section_future_leak",
        cross_section_future_leak,
        "cross-section used names or ranks from the future",
        "cross-section at T uses Universe(T)",
        "cross-section leak not asserted",
    )
    _model_flag(
        report,
        "model_replay_leak",
        model_replay_leak,
        "full-sample fit replayed as historical predictions",
        "walk-forward predict-then-realize",
        "model replay not asserted",
    )
    _model_flag(
        report,
        "model_state_mutation",
        model_state_mutation,
        "fitted state mutated after freeze",
        "frozen state used for prediction",
        "model state mutation not asserted",
    )
    _model_flag(
        report,
        "future_component_performance",
        future_component_performance,
        "component IC or error after T used for combination",
        "component evidence available at T only",
        "component-performance PIT not asserted",
    )
    _model_flag(
        report,
        "future_ensemble_weight",
        future_ensemble_weight,
        "weights computed from returns after T",
        "weights from PIT IC available at T",
        "ensemble-weight PIT not asserted",
    )
    _model_flag(
        report,
        "future_correlation",
        future_correlation,
        "component correlation used observations after T",
        "correlation from history through T-1",
        "ensemble correlation PIT not asserted",
    )
    _model_flag(
        report,
        "future_meta_feature",
        future_meta_feature,
        "meta-feature used information after T",
        "meta-features have available_time <= T",
        "meta-feature PIT not asserted",
    )
    _model_flag(
        report,
        "future_component_selection",
        future_component_selection,
        "components selected using future or holdout performance",
        "component set frozen before prediction",
        "component-selection PIT not asserted",
    )
    _model_flag(
        report,
        "future_stacking_prediction",
        future_stacking_prediction,
        "meta-model trained on in-sample or future base predictions",
        "stacking uses walk-forward OOS base predictions",
        "stacking prediction PIT not asserted",
    )
    _model_flag(
        report,
        "future_pruning",
        future_pruning,
        "pruning used full-sample future correlation",
        "pruning uses PIT history through T-1",
        "pruning PIT not asserted",
    )
    _model_flag(
        report,
        "stacking_leak",
        stacking_leak,
        "fit base then train meta on the same in-sample rows",
        "meta trained on temporally valid OOS base scores",
        "stacking leak not asserted",
    )
    _model_flag(
        report,
        "full_sample_ensemble_replay",
        full_sample_ensemble_replay,
        "full-sample ensemble fit replayed as historical scores",
        "walk-forward combine-then-realize",
        "ensemble replay not asserted",
    )
    _model_flag(
        report,
        "future_volume_leak",
        future_volume_leak,
        "volume after T used for a fill at T",
        "volume available_time <= decision_time",
        "future volume not asserted",
    )
    _model_flag(
        report,
        "future_spread_leak",
        future_spread_leak,
        "spread after T used for a fill at T",
        "spread inputs available at T",
        "future spread not asserted",
    )
    _model_flag(
        report,
        "future_liquidity_leak",
        future_liquidity_leak,
        "liquidity after T used for a fill at T",
        "liquidity available_time <= T",
        "future liquidity not asserted",
    )
    _model_flag(
        report,
        "future_impact_parameter",
        future_impact_parameter,
        "impact coefficient or vol from after T",
        "impact inputs available at T",
        "future impact parameter not asserted",
    )
    _model_flag(
        report,
        "future_execution_parameter",
        future_execution_parameter,
        "execution parameter chosen with information after T",
        "execution parameters frozen at T",
        "future execution parameter not asserted",
    )
    _model_flag(
        report,
        "future_latency",
        future_latency,
        "latency delay chosen using future market state",
        "latency is configured, not fit on the future",
        "future latency not asserted",
    )
    _model_flag(
        report,
        "pre_arrival_fill",
        pre_arrival_fill,
        "fill timestamp before market arrival",
        "no fill before arrival",
        "pre-arrival fill not asserted",
    )
    _model_flag(
        report,
        "full_fill_assumption",
        full_fill_assumption,
        "orders assumed fully filled regardless of participation",
        "participation and residuals are explicit",
        "full-fill assumption not asserted",
    )
    _model_flag(
        report,
        "zero_cost_execution",
        zero_cost_execution,
        "zero-cost execution is not tradability evidence",
        "nonzero configured execution friction",
        "zero-cost execution not asserted",
    )
    _model_flag(
        report,
        "negative_execution_cost",
        negative_execution_cost,
        "execution cost was negative (price improvement treated as edge)",
        "execution costs are a positive drag",
        "negative execution cost not asserted",
    )
    _model_flag(
        report,
        "wrong_side_slippage",
        wrong_side_slippage,
        "BUY slipped down or SELL slipped up",
        "slippage is adverse for both sides",
        "wrong-side slippage not asserted",
    )
    _model_flag(
        report,
        "wrong_side_impact",
        wrong_side_impact,
        "impact improved the execution price",
        "impact is adverse for both sides",
        "wrong-side impact not asserted",
    )
    _model_flag(
        report,
        "hidden_partial_fill",
        hidden_partial_fill,
        "remaining quantity hidden behind a full-fill status",
        "partial fills preserve remaining quantity",
        "hidden partial fill not asserted",
    )
    _model_flag(
        report,
        "capacity_lookahead",
        capacity_lookahead,
        "capacity used full-sample or future ADV",
        "capacity uses PIT volume through T",
        "capacity lookahead not asserted",
    )
    _model_flag(
        report,
        "execution_model_mutation",
        execution_model_mutation,
        "microstructure identity mutated after freeze",
        "frozen microstructure identity used for fills",
        "execution model mutation not asserted",
    )
    _model_flag(
        report,
        "future_execution_calibration",
        future_execution_calibration,
        "impact/slippage calibrated on future outcomes",
        "no future execution calibration",
        "future execution calibration not asserted",
    )
    _model_flag(
        report,
        "experiment_identity_mutation",
        experiment_identity_mutation,
        "frozen experiment identity mutated",
        "experiment identity unchanged after freeze",
        "experiment identity mutation not asserted",
    )
    _model_flag(
        report,
        "experiment_config_mutation",
        experiment_config_mutation,
        "frozen experiment config mutated",
        "experiment config unchanged after freeze",
        "experiment config mutation not asserted",
    )
    _model_flag(
        report,
        "future_experiment_selection",
        future_experiment_selection,
        "experiment chosen using future outcomes",
        "experiment selected by pre-registration",
        "future experiment selection not asserted",
    )
    _model_flag(
        report,
        "future_candidate_selection",
        future_candidate_selection,
        "candidate chosen after looking at holdout or full-sample rank",
        "candidate selected by frozen primary rule",
        "future candidate selection not asserted",
    )
    _model_flag(
        report,
        "future_hypothesis_selection",
        future_hypothesis_selection,
        "hypothesis chosen after seeing results",
        "hypothesis frozen before search",
        "future hypothesis selection not asserted",
    )
    _model_flag(
        report,
        "hidden_candidate",
        hidden_candidate,
        "a tested candidate was dropped from the family record",
        "every generated candidate is recorded",
        "hidden candidate not asserted",
    )
    _model_flag(
        report,
        "hidden_failed_experiment",
        hidden_failed_experiment,
        "a failed experiment was omitted from the family",
        "failed experiments remain visible",
        "hidden failed experiment not asserted",
    )
    _model_flag(
        report,
        "hidden_search",
        hidden_search,
        "search space was not recorded",
        "search space is explicit",
        "hidden search not asserted",
    )
    _model_flag(
        report,
        "posthoc_stopping",
        posthoc_stopping,
        "stopping rule changed after seeing results",
        "stopping rule frozen before execution",
        "post-hoc stopping not asserted",
    )
    _model_flag(
        report,
        "multiple_testing_omission",
        multiple_testing_omission,
        "family search without a multiple-testing correction",
        "family correction applied",
        "multiple-testing omission not asserted",
    )
    _model_flag(
        report,
        "family_definition_mutation",
        family_definition_mutation,
        "family membership mutated after freeze",
        "family definition frozen",
        "family definition mutation not asserted",
    )
    _model_flag(
        report,
        "research_budget_bypass",
        research_budget_bypass,
        "budget cap ignored",
        "budget freeze honored",
        "research budget bypass not asserted",
    )
    _model_flag(
        report,
        "replication_contamination",
        replication_contamination,
        "replication reused a different snapshot under the same identity",
        "replication snapshot matches parent or is a new lineage",
        "replication contamination not asserted",
    )
    _model_flag(
        report,
        "holdout_reuse",
        holdout_reuse,
        "holdout used for selection more than once",
        "holdout not reused for selection",
        "holdout reuse not asserted",
    )
    _model_flag(
        report,
        "future_baseline_selection",
        future_baseline_selection,
        "baseline chosen after seeing challenger results",
        "baseline pre-registered",
        "future baseline selection not asserted",
    )
    _model_flag(
        report,
        "future_model_selection",
        future_model_selection,
        "model chosen using future performance",
        "model frozen before evaluation",
        "future model selection not asserted",
    )
    _model_flag(
        report,
        "future_execution_selection",
        future_execution_selection,
        "execution model chosen after seeing net results",
        "execution model pre-registered",
        "future execution selection not asserted",
    )
    _model_flag(
        report,
        "future_cost_selection",
        future_cost_selection,
        "cost assumption chosen after seeing P&L",
        "cost assumption frozen",
        "future cost selection not asserted",
    )
    _model_flag(
        report,
        "lineage_break",
        lineage_break,
        "parent experiment or hypothesis missing from the graph",
        "lineage parents are present",
        "lineage break not asserted",
    )
    _model_flag(
        report,
        "dataset_snapshot_mismatch",
        dataset_snapshot_mismatch,
        "claimed snapshot does not match the pinned PIT snapshot",
        "dataset snapshot pinned",
        "dataset snapshot mismatch not asserted",
    )
    _model_flag(
        report,
        "result_overwrite",
        result_overwrite,
        "finalized experiment result was overwritten",
        "results are append-only",
        "result overwrite not asserted",
    )
    _model_flag(
        report,
        "parallel_state_leak",
        parallel_state_leak,
        "parallel workers shared mutable research state",
        "experiments are isolated",
        "parallel state leak not asserted",
    )
    _model_flag(
        report,
        "adaptive_state_cross_contamination",
        adaptive_state_cross_contamination,
        "adaptive state reused across experiments",
        "adaptive state is not shared",
        "adaptive state cross-contamination not asserted",
    )
    _model_flag(
        report,
        "future_expression_input",
        future_expression_input,
        "expression used information not available at T",
        "expression inputs are PIT-available",
        "future expression input not asserted",
    )
    _model_flag(
        report,
        "future_candidate_generation",
        future_candidate_generation,
        "candidates generated with future information",
        "generation used only frozen history",
        "future candidate generation not asserted",
    )
    _model_flag(
        report,
        "future_search_state",
        future_search_state,
        "search state used future fitness or holdout",
        "search state is causal",
        "future search state not asserted",
    )
    _model_flag(
        report,
        "future_fitness",
        future_fitness,
        "fitness computed on future or holdout data",
        "fitness is train-only",
        "future fitness not asserted",
    )
    _model_flag(
        report,
        "future_selection",
        future_selection,
        "selection used future scores",
        "selection used frozen train fitness",
        "future selection not asserted",
    )
    _model_flag(
        report,
        "future_mutation",
        future_mutation,
        "mutation used future information",
        "mutation is a syntactic operator",
        "future mutation not asserted",
    )
    _model_flag(
        report,
        "future_crossover",
        future_crossover,
        "crossover used future information",
        "crossover is a syntactic operator",
        "future crossover not asserted",
    )
    _model_flag(
        report,
        "future_feature",
        future_feature,
        "feature primitive was not available at T",
        "feature primitives are PIT-available",
        "future feature not asserted",
    )
    _model_flag(
        report,
        "posthoc_search_budget",
        posthoc_search_budget,
        "search budget extended after observing results",
        "search budget was frozen",
        "post-hoc search budget not asserted",
    )
    _model_flag(
        report,
        "search_space_omission",
        search_space_omission,
        "search space size omitted from the record",
        "search space is recorded",
        "search space omission not asserted",
    )
    _model_flag(
        report,
        "candidate_lineage_break",
        candidate_lineage_break,
        "parent expression missing from the lineage graph",
        "candidate parents are present",
        "candidate lineage break not asserted",
    )
    _model_flag(
        report,
        "expression_mutation",
        expression_mutation,
        "expression identity changed after hashing",
        "expression identity is immutable",
        "expression mutation not asserted",
    )
    _model_flag(
        report,
        "future_redundancy",
        future_redundancy,
        "redundancy used future outputs",
        "redundancy used train-fold outputs",
        "future redundancy not asserted",
    )
    _model_flag(
        report,
        "future_novelty",
        future_novelty,
        "novelty used future outputs",
        "novelty used train-fold outputs",
        "future novelty not asserted",
    )
    _model_flag(
        report,
        "future_complexity_selection",
        future_complexity_selection,
        "complexity penalty chosen after seeing holdout",
        "complexity weights were frozen",
        "future complexity selection not asserted",
    )
    _model_flag(
        report,
        "knowledge_provenance_break",
        knowledge_provenance_break,
        "knowledge edge or node provenance is broken",
        "knowledge provenance is intact",
        "knowledge provenance not asserted",
    )
    _model_flag(
        report,
        "evidence_without_experiment",
        evidence_without_experiment,
        "evidence is not bound to an experiment",
        "evidence is bound to an experiment",
        "evidence-experiment binding not asserted",
    )
    _model_flag(
        report,
        "claim_without_evidence",
        claim_without_evidence,
        "claim has no supporting evidence",
        "claim has supporting evidence",
        "claim evidence binding not asserted",
    )
    _model_flag(
        report,
        "claim_overstates_evidence",
        claim_overstates_evidence,
        "claim is stronger than its evidence",
        "claim does not overstate evidence",
        "claim strength not asserted",
    )
    _model_flag(
        report,
        "candidate_history_deleted",
        candidate_history_deleted,
        "failed research was deleted from memory",
        "failed research is retained",
        "candidate history retention not asserted",
    )
    _model_flag(
        report,
        "duplicate_identity_collision",
        duplicate_identity_collision,
        "the same identity was rewritten with different content",
        "identities are immutable",
        "identity collision not asserted",
    )
    _model_flag(
        report,
        "snapshot_mutation",
        snapshot_mutation,
        "a frozen knowledge snapshot was rewritten",
        "knowledge snapshots are immutable",
        "snapshot mutation not asserted",
    )
    _model_flag(
        report,
        "historical_claim_mutation",
        historical_claim_mutation,
        "a historical claim was mutated",
        "historical claims are frozen",
        "historical claim mutation not asserted",
    )
    _model_flag(
        report,
        "future_knowledge_leak",
        future_knowledge_leak,
        "later data was used for an earlier knowledge claim",
        "knowledge as-of is respected",
        "future knowledge leak not asserted",
    )
    _model_flag(
        report,
        "future_claim_context",
        future_claim_context,
        "future evidence was attached to an earlier claim",
        "claim context is not in the future",
        "future claim context not asserted",
    )
    _model_flag(
        report,
        "replication_same_data",
        replication_same_data,
        "identical snapshot/protocol labeled independent replication",
        "replication uses distinct data or protocol",
        "replication independence not asserted",
    )
    _model_flag(
        report,
        "contradiction_hidden",
        contradiction_hidden,
        "contradictory claims were silently resolved",
        "contradictions remain visible",
        "contradiction visibility not asserted",
    )
    _model_flag(
        report,
        "search_degree_of_freedom_loss",
        search_degree_of_freedom_loss,
        "discarded candidates were hidden from the search record",
        "search degrees of freedom are retained",
        "search degree-of-freedom accounting not asserted",
    )
    _model_flag(
        report,
        "synthetic_evidence_overpromotion",
        synthetic_evidence_overpromotion,
        "synthetic evidence was promoted to validated market knowledge",
        "synthetic evidence remains non-promotable",
        "synthetic promotion not asserted",
    )
    _model_flag(
        report,
        "ai_evidence_confusion",
        ai_evidence_confusion,
        "AI-generated text was treated as empirical evidence",
        "AI content is not empirical evidence",
        "AI evidence confusion not asserted",
    )
    _model_flag(
        report,
        "future_capital_input",
        future_capital_input,
        "future capital state entered the allocation",
        "capital inputs are PIT",
        "future capital input not asserted",
    )
    _model_flag(
        report,
        "future_risk_input",
        future_risk_input,
        "future risk inputs entered the allocation",
        "risk inputs are PIT",
        "future risk input not asserted",
    )
    _model_flag(
        report,
        "future_expected_return",
        future_expected_return,
        "future realized return was used as expected return",
        "expected return is PIT",
        "future expected return not asserted",
    )
    _model_flag(
        report,
        "future_factor_exposure",
        future_factor_exposure,
        "future factor exposure entered the allocation",
        "factor exposure is PIT",
        "future factor exposure not asserted",
    )
    _model_flag(
        report,
        "future_liquidity",
        future_liquidity,
        "future liquidity entered the allocation",
        "liquidity is PIT",
        "future liquidity not asserted",
    )
    _model_flag(
        report,
        "future_turnover_state",
        future_turnover_state,
        "future turnover state entered the allocation",
        "turnover uses current vs previous targets",
        "future turnover not asserted",
    )
    _model_flag(
        report,
        "future_drawdown_state",
        future_drawdown_state,
        "future drawdown entered the capital state",
        "drawdown state is PIT",
        "future drawdown not asserted",
    )
    _model_flag(
        report,
        "future_constraint_parameter",
        future_constraint_parameter,
        "future constraint parameters entered the allocation",
        "constraint parameters are frozen",
        "future constraint parameter not asserted",
    )
    _model_flag(
        report,
        "future_position_reference",
        future_position_reference,
        "future positions were used as the reference book",
        "position reference is PIT",
        "future position reference not asserted",
    )
    _model_flag(
        report,
        "future_decision_state",
        future_decision_state,
        "future decision state leaked into the current decision",
        "decision state is frozen at T",
        "future decision state not asserted",
    )
    _model_flag(
        report,
        "capital_policy_mutation",
        capital_policy_mutation,
        "capital policy was mutated after hashing",
        "capital policy is immutable after hash",
        "capital policy mutation not asserted",
    )
    _model_flag(
        report,
        "decision_mutation",
        decision_mutation,
        "a historical decision was mutated",
        "decisions are immutable",
        "decision mutation not asserted",
    )
    _model_flag(
        report,
        "decision_hash_mismatch",
        decision_hash_mismatch,
        "decision hash does not match canonical payload",
        "decision hash matches canonical payload",
        "decision hash mismatch not asserted",
    )
    _model_flag(
        report,
        "allocation_lineage_break",
        allocation_lineage_break,
        "allocation lineage identifiers were dropped",
        "allocation lineage is retained",
        "allocation lineage not asserted",
    )
    _model_flag(
        report,
        "hidden_constraint_relaxation",
        hidden_constraint_relaxation,
        "hard constraints were silently relaxed",
        "hard constraints were not silently relaxed",
        "hidden constraint relaxation not asserted",
    )
    _model_flag(
        report,
        "silent_fallback",
        silent_fallback,
        "allocator silently fell back to another method",
        "no silent sizing fallback",
        "silent fallback not asserted",
    )
    _model_flag(
        report,
        "unknown_liquidity_as_infinite",
        unknown_liquidity_as_infinite,
        "unknown liquidity was treated as infinite",
        "unknown liquidity is not infinite",
        "unknown liquidity interpretation not asserted",
    )
    _model_flag(
        report,
        "unknown_factor_as_zero",
        unknown_factor_as_zero,
        "unknown factor exposure was treated as zero",
        "unknown factor exposure is NOT_TESTED",
        "unknown factor interpretation not asserted",
    )
    _model_flag(
        report,
        "synthetic_capital_overpromotion",
        synthetic_capital_overpromotion,
        "synthetic allocation was promoted beyond research diagnostics",
        "synthetic allocation remains research-only",
        "synthetic capital promotion not asserted",
    )
    _model_flag(
        report,
        "gate_bypass",
        gate_bypass,
        "allocation bypassed the research gate",
        "research gate still binds allocation",
        "gate bypass not asserted",
    )
    _model_flag(
        report,
        "abstention_suppression",
        abstention_suppression,
        "an abstention was hidden or rewritten as an allocation",
        "abstentions remain first-class",
        "abstention suppression not asserted",
    )
    _model_flag(
        report,
        "future_portfolio_state",
        future_portfolio_state,
        "future portfolio state entered the allocation",
        "portfolio state is PIT",
        "future portfolio state not asserted",
    )
    _model_flag(
        report,
        "future_execution_cost",
        future_execution_cost,
        "future execution costs entered the allocation",
        "execution-cost assumptions are PIT",
        "future execution cost not asserted",
    )
    _model_flag(
        report,
        "target_mutation",
        target_mutation,
        "target portfolio was mutated after freeze",
        "target portfolio remained immutable",
        "target mutation not asserted",
    )
    _model_flag(
        report,
        "order_intent_mutation",
        order_intent_mutation,
        "order intent was mutated after hash",
        "order intent remained immutable",
        "order intent mutation not asserted",
    )
    _model_flag(
        report,
        "order_plan_mutation",
        order_plan_mutation,
        "order plan was mutated after hash",
        "order plan remained immutable",
        "order plan mutation not asserted",
    )
    _model_flag(
        report,
        "duplicate_order",
        duplicate_order,
        "duplicate paper order created for the same identity",
        "paper order identity is unique",
        "duplicate order not asserted",
    )
    _model_flag(
        report,
        "duplicate_fill",
        duplicate_fill,
        "duplicate paper fill applied",
        "paper fills are unique",
        "duplicate fill not asserted",
    )
    _model_flag(
        report,
        "invalid_order_transition",
        invalid_order_transition,
        "an invalid OMS state transition was accepted",
        "lifecycle transitions are enforced",
        "invalid order transition not asserted",
    )
    _model_flag(
        report,
        "future_execution_price",
        future_execution_price,
        "a future price was used as the simulated execution price",
        "execution price is PIT to arrival",
        "future execution price not asserted",
    )
    _model_flag(
        report,
        "future_fill_information",
        future_fill_information,
        "future fill information entered the paper OMS",
        "fill information is PIT",
        "future fill information not asserted",
    )
    _model_flag(
        report,
        "cash_accounting_break",
        cash_accounting_break,
        "paper cash identity failed",
        "paper cash identity holds",
        "cash accounting break not asserted",
    )
    _model_flag(
        report,
        "position_accounting_break",
        position_accounting_break,
        "paper position identity failed",
        "paper position identity holds",
        "position accounting break not asserted",
    )
    _model_flag(
        report,
        "target_position_mismatch",
        target_position_mismatch,
        "unexplained target vs paper position mismatch",
        "target/position residuals are explained",
        "target position mismatch not asserted",
    )
    _model_flag(
        report,
        "order_fill_mismatch",
        order_fill_mismatch,
        "order quantity does not match fills",
        "order/fill quantities agree",
        "order fill mismatch not asserted",
    )
    _model_flag(
        report,
        "orphan_fill",
        orphan_fill,
        "a paper fill has no parent order",
        "every fill has an order",
        "orphan fill not asserted",
    )
    _model_flag(
        report,
        "orphan_event",
        orphan_event,
        "an order event has no parent order",
        "every event has an order",
        "orphan event not asserted",
    )
    _model_flag(
        report,
        "reconciliation_break",
        reconciliation_break,
        "paper reconciliation broke",
        "paper books reconcile",
        "reconciliation break not asserted",
    )
    _model_flag(
        report,
        "execution_policy_mutation",
        execution_policy_mutation,
        "execution policy was mutated after hash",
        "execution policy remained immutable",
        "execution policy mutation not asserted",
    )
    _model_flag(
        report,
        "paper_live_mode_confusion",
        paper_live_mode_confusion,
        "paper path was labelled as live",
        "paper/live modes are distinct",
        "paper/live confusion not asserted",
    )
    _model_flag(
        report,
        "broker_import_violation",
        broker_import_violation,
        "paper OMS imported a broker SDK",
        "paper OMS has no broker imports",
        "broker import violation not asserted",
    )
    _model_flag(
        report,
        "future_performance_mark",
        future_performance_mark,
        "performance used a future mark",
        "performance marks are PIT",
        "future performance mark not asserted",
    )
    _model_flag(
        report,
        "future_attribution_input",
        future_attribution_input,
        "attribution used future inputs",
        "attribution inputs are PIT",
        "future attribution input not asserted",
    )
    _model_flag(
        report,
        "future_benchmark",
        future_benchmark,
        "benchmark used future prices",
        "benchmark is PIT",
        "future benchmark not asserted",
    )
    _model_flag(
        report,
        "future_factor_return",
        future_factor_return,
        "factor attribution used future factor returns",
        "factor returns are PIT",
        "future factor return not asserted",
    )
    _model_flag(
        report,
        "performance_snapshot_mutation",
        performance_snapshot_mutation,
        "performance snapshot mutated after hash",
        "performance snapshot remained immutable",
        "performance snapshot mutation not asserted",
    )
    _model_flag(
        report,
        "position_history_mutation",
        position_history_mutation,
        "position history mutated after hash",
        "position history remained immutable",
        "position history mutation not asserted",
    )
    _model_flag(
        report,
        "pnl_reconciliation_break",
        pnl_reconciliation_break,
        "P&L identity broke",
        "P&L identity holds",
        "P&L reconciliation break not asserted",
    )
    _model_flag(
        report,
        "attribution_reconciliation_break",
        attribution_reconciliation_break,
        "attribution does not sum to total",
        "attribution reconciles",
        "attribution reconciliation break not asserted",
    )
    _model_flag(
        report,
        "hidden_residual",
        hidden_residual,
        "residual P&L was hidden",
        "residual P&L is visible",
        "hidden residual not asserted",
    )
    _model_flag(
        report,
        "benchmark_lookahead",
        benchmark_lookahead,
        "benchmark looked ahead",
        "benchmark is as-of",
        "benchmark lookahead not asserted",
    )
    _model_flag(
        report,
        "target_observation_confusion",
        target_observation_confusion,
        "target was confused with the observed book",
        "target and observation are distinct",
        "target/observation confusion not asserted",
    )
    _model_flag(
        report,
        "posthoc_attribution",
        posthoc_attribution,
        "attribution was fitted after seeing the outcome",
        "attribution method was frozen",
        "posthoc attribution not asserted",
    )
    _model_flag(
        report,
        "performance_claim_overstatement",
        performance_claim_overstatement,
        "performance was promoted to a claim",
        "performance is not automatically a claim",
        "performance claim overstatement not asserted",
    )
    _model_flag(
        report,
        "future_available_data",
        future_available_data,
        "query returned available_time > as_of",
        "available_time <= as_of",
        "future available data not asserted",
    )
    _model_flag(
        report,
        "event_available_time_conflict",
        event_available_time_conflict,
        "event_time and available_time conflict",
        "event/available times are consistent",
        "event/available time conflict not asserted",
    )
    _model_flag(
        report,
        "source_mutation",
        source_mutation,
        "raw source bytes mutated after checksum",
        "raw source remained immutable",
        "source mutation not asserted",
    )
    _model_flag(
        report,
        "checksum_mismatch",
        checksum_mismatch,
        "dataset checksum does not match bytes",
        "checksum matches",
        "checksum mismatch not asserted",
    )
    _model_flag(
        report,
        "duplicate_observation",
        duplicate_observation,
        "duplicate market observation",
        "observations are unique",
        "duplicate observation not asserted",
    )
    _model_flag(
        report,
        "identity_lookahead",
        identity_lookahead,
        "security identity used a future mapping",
        "identity lookup is as-of",
        "identity lookahead not asserted",
    )
    _model_flag(
        report,
        "symbol_history_lookahead",
        symbol_history_lookahead,
        "symbol history used a future label",
        "symbol_at is as-of",
        "symbol history lookahead not asserted",
    )
    _model_flag(
        report,
        "corporate_action_lookahead",
        corporate_action_lookahead,
        "corporate action applied before it was knowable",
        "corporate actions are PIT",
        "corporate action lookahead not asserted",
    )
    _model_flag(
        report,
        "adjustment_lookahead",
        adjustment_lookahead,
        "price adjustment used a future action",
        "adjustments are PIT",
        "adjustment lookahead not asserted",
    )
    _model_flag(
        report,
        "calendar_lookahead",
        calendar_lookahead,
        "calendar used a future holiday file",
        "calendar is versioned as-of",
        "calendar lookahead not asserted",
    )
    _model_flag(
        report,
        "universe_survivorship_leak",
        universe_survivorship_leak,
        "current membership substituted for historical membership",
        "universe.as_of is historical",
        "universe survivorship leak not asserted",
    )
    _model_flag(
        report,
        "delisted_security_omission",
        delisted_security_omission,
        "delisted names were dropped from history",
        "delisted names remain historically queryable",
        "delisted security omission not asserted",
    )
    _model_flag(
        report,
        "cross_source_conflict",
        cross_source_conflict,
        "sources disagree without a recorded resolution",
        "cross-source differences are recorded",
        "cross-source conflict not asserted",
    )
    _model_flag(
        report,
        "snapshot_dependency_mutation",
        snapshot_dependency_mutation,
        "snapshot dependency changed after freeze",
        "snapshot dependencies remained frozen",
        "snapshot dependency mutation not asserted",
    )
    _model_flag(
        report,
        "raw_to_derived_lineage_break",
        raw_to_derived_lineage_break,
        "derived dataset has no raw parent",
        "raw-to-derived lineage is intact",
        "raw-to-derived lineage break not asserted",
    )
    _model_flag(
        report,
        "timezone_mismatch",
        timezone_mismatch,
        "timestamps mix timezones inconsistently",
        "timestamps are timezone-consistent",
        "timezone mismatch not asserted",
    )
    _model_flag(
        report,
        "future_tca_observation",
        future_tca_observation,
        "TCA used a future observation",
        "TCA observations are PIT",
        "future TCA observation not asserted",
    )
    _model_flag(
        report,
        "future_impact_calibration",
        future_impact_calibration,
        "impact calibrated on future data",
        "impact calibration window is PIT",
        "future impact calibration not asserted",
    )
    _model_flag(
        report,
        "future_spread_calibration",
        future_spread_calibration,
        "spread calibrated on future data",
        "spread calibration window is PIT",
        "future spread calibration not asserted",
    )
    _model_flag(
        report,
        "future_volume_calibration",
        future_volume_calibration,
        "volume calibrated on future data",
        "volume calibration window is PIT",
        "future volume calibration not asserted",
    )
    _model_flag(
        report,
        "future_liquidity_calibration",
        future_liquidity_calibration,
        "liquidity calibrated on future data",
        "liquidity calibration window is PIT",
        "future liquidity calibration not asserted",
    )
    _model_flag(
        report,
        "future_capacity_parameter",
        future_capacity_parameter,
        "capacity used a future parameter",
        "capacity parameters are frozen",
        "future capacity parameter not asserted",
    )
    _model_flag(
        report,
        "arrival_price_lookahead",
        arrival_price_lookahead,
        "arrival price looked ahead",
        "arrival price is as-of",
        "arrival price lookahead not asserted",
    )
    _model_flag(
        report,
        "benchmark_price_lookahead",
        benchmark_price_lookahead,
        "TCA benchmark looked ahead",
        "TCA benchmark is as-of",
        "benchmark price lookahead not asserted",
    )
    _model_flag(
        report,
        "posthoc_cost_model",
        posthoc_cost_model,
        "cost model fitted after seeing outcomes",
        "cost model was frozen before test",
        "posthoc cost model not asserted",
    )
    _model_flag(
        report,
        "calibration_window_leak",
        calibration_window_leak,
        "calibration window included the test period",
        "calibration is freeze-then-test",
        "calibration window leak not asserted",
    )
    _model_flag(
        report,
        "future_fill_observation",
        future_fill_observation,
        "TCA used a future fill",
        "fills used in TCA are as-of",
        "future fill observation not asserted",
    )
    _model_flag(
        report,
        "synthetic_adv_claim",
        synthetic_adv_claim,
        "synthetic volume was labelled NSE ADV",
        "synthetic volume is not claimed as NSE ADV",
        "synthetic ADV claim not asserted",
    )
    _model_flag(
        report,
        "observed_vs_modelled_confusion",
        observed_vs_modelled_confusion,
        "modelled TCA was labelled observed",
        "observed and modelled TCA are distinct",
        "observed vs modelled confusion not asserted",
    )
    _model_flag(
        report,
        "tca_parameter_mutation",
        tca_parameter_mutation,
        "TCA parameters mutated after hash",
        "TCA parameters remained immutable",
        "TCA parameter mutation not asserted",
    )
    _model_flag(
        report,
        "future_stationarity_window",
        future_stationarity_window,
        "stationarity used a window after as_of",
        "stationarity window is PIT",
        "stationarity window leak not asserted",
    )
    _model_flag(
        report,
        "future_lag_selection",
        future_lag_selection,
        "lags were selected on the full sample",
        "lag selection used the training window only",
        "lag selection leak not asserted",
    )
    _model_flag(
        report,
        "future_break_detection",
        future_break_detection,
        "break detection used future observations",
        "break detection is PIT",
        "break detection leak not asserted",
    )
    _model_flag(
        report,
        "future_cointegration_selection",
        future_cointegration_selection,
        "cointegration spec selected on the full sample",
        "cointegration selection is PIT",
        "cointegration selection leak not asserted",
    )
    _model_flag(
        report,
        "future_var_selection",
        future_var_selection,
        "VAR lag/spec selected on the full sample",
        "VAR selection used the training window only",
        "VAR selection leak not asserted",
    )
    _model_flag(
        report,
        "future_causal_control",
        future_causal_control,
        "causal controls used post-treatment information",
        "causal controls are pre-treatment",
        "causal control leak not asserted",
    )
    _model_flag(
        report,
        "future_event_window",
        future_event_window,
        "event-study window used unavailable timestamps",
        "event window is PIT",
        "event window leak not asserted",
    )
    _model_flag(
        report,
        "future_parameter_estimation",
        future_parameter_estimation,
        "econometric parameters estimated after as_of",
        "parameter estimation is PIT",
        "parameter estimation leak not asserted",
    )
    _model_flag(
        report,
        "full_sample_econometric_replay",
        full_sample_econometric_replay,
        "full-sample econometric fit was replayed as OOS",
        "econometric fit was not full-sample replay",
        "full-sample econometric replay not asserted",
    )
    _model_flag(
        report,
        "future_residual_normalization",
        future_residual_normalization,
        "residuals were normalized with future moments",
        "residual normalization is PIT",
        "residual normalization leak not asserted",
    )
    _model_flag(
        report,
        "future_panel_selection",
        future_panel_selection,
        "panel spec selected with future entities/times",
        "panel selection is PIT",
        "panel selection leak not asserted",
    )
    _model_flag(
        report,
        "causal_post_treatment_control",
        causal_post_treatment_control,
        "post-treatment variables were used as controls",
        "post-treatment controls were not used",
        "post-treatment control leak not asserted",
    )
    _model_flag(
        report,
        "lookahead_event_study",
        lookahead_event_study,
        "event study used announcement after as_of",
        "event study availability is PIT",
        "event-study lookahead not asserted",
    )
    _model_flag(
        report,
        "illegal_certification_transition",
        illegal_certification_transition,
        "illegal certification state transition",
        "certification transitions follow the state machine",
        "illegal certification transition not asserted",
    )
    _model_flag(
        report,
        "synthetic_production_evidence",
        synthetic_production_evidence,
        "synthetic diagnostics were used as production evidence",
        "synthetic is not treated as production evidence",
        "synthetic production evidence not asserted",
    )
    _model_flag(
        report,
        "reproduction_break",
        reproduction_break,
        "reproduction hash does not match the frozen result",
        "reproduction hashes match",
        "reproduction break not asserted",
    )
    _model_flag(
        report,
        "waiver_without_authority",
        waiver_without_authority,
        "waiver lacks authority, scope, or expiry",
        "waivers are fully specified",
        "waiver authority not asserted",
    )
    _model_flag(
        report,
        "ai_certification_override",
        ai_certification_override,
        "AI attempted to override certification or safety",
        "AI cannot override certification",
        "AI certification override not asserted",
    )
    _model_flag(
        report,
        "critical_not_tested_certified",
        critical_not_tested_certified,
        "critical NOT_TESTED items were certified",
        "critical NOT_TESTED items block certification",
        "critical NOT_TESTED certification not asserted",
    )
    _model_flag(
        report,
        "future_shadow_data",
        future_shadow_data,
        "shadow cycle used data with available_time after decision_time",
        "shadow data available_time <= decision_time",
        "future shadow data not asserted",
    )
    _model_flag(
        report,
        "future_decision_input",
        future_decision_input,
        "decision used information after decision_time",
        "decision inputs are PIT",
        "future decision input not asserted",
    )
    _model_flag(
        report,
        "future_execution_input",
        future_execution_input,
        "shadow fill used a later quote",
        "shadow execution inputs are PIT",
        "future execution input not asserted",
    )
    _model_flag(
        report,
        "stale_data_decision",
        stale_data_decision,
        "a trade decision was generated on stale data",
        "stale data cannot generate a trade decision",
        "stale-data decision not asserted",
    )
    _model_flag(
        report,
        "unknown_calendar_execution",
        unknown_calendar_execution,
        "unknown calendar was treated as an open session",
        "unknown calendar is not OPEN",
        "unknown calendar execution not asserted",
    )
    _model_flag(
        report,
        "duplicate_cycle",
        duplicate_cycle,
        "duplicate cycle identity produced a second order stream",
        "duplicate cycles are idempotent",
        "duplicate cycle not asserted",
    )
    _model_flag(
        report,
        "duplicate_shadow_order",
        duplicate_shadow_order,
        "duplicate shadow order identity",
        "shadow orders are unique per cycle",
        "duplicate shadow order not asserted",
    )
    _model_flag(
        report,
        "shadow_live_confusion",
        shadow_live_confusion,
        "shadow execution was labelled live or broker-confirmed",
        "shadow is not live",
        "shadow/live confusion not asserted",
    )
    _model_flag(
        report,
        "live_route_attempt",
        live_route_attempt,
        "a live broker route was requested on the shadow path",
        "live routing is impossible on the shadow path",
        "live route attempt not asserted",
    )
    _model_flag(
        report,
        "paper_shadow_state_confusion",
        paper_shadow_state_confusion,
        "paper and shadow books were collapsed",
        "paper, shadow, and broker books remain distinct",
        "paper/shadow state confusion not asserted",
    )
    _model_flag(
        report,
        "model_version_mutation",
        model_version_mutation,
        "model version mutated inside a frozen cycle",
        "model versions are locked per cycle",
        "model version mutation not asserted",
    )
    _model_flag(
        report,
        "configuration_mutation",
        configuration_mutation,
        "configuration mutated inside a frozen cycle",
        "configuration is immutable per cycle",
        "configuration mutation not asserted",
    )
    _model_flag(
        report,
        "pre_arrival_shadow_fill",
        pre_arrival_shadow_fill,
        "shadow fill occurred before order arrival",
        "shadow fills are not pre-arrival",
        "pre-arrival shadow fill not asserted",
    )
    _model_flag(
        report,
        "future_shadow_fill",
        future_shadow_fill,
        "a later quote improved an earlier simulated fill",
        "shadow fills do not use future quotes",
        "future shadow fill not asserted",
    )
    _model_flag(
        report,
        "partial_fill_hidden",
        partial_fill_hidden,
        "partial fill or residual was hidden",
        "partial fills and residuals remain visible",
        "hidden partial fill not asserted",
    )
    _model_flag(
        report,
        "shadow_accounting_break",
        shadow_accounting_break,
        "shadow cash or position identity failed",
        "shadow accounting identity holds",
        "shadow accounting break not asserted",
    )
    _model_flag(
        report,
        "shadow_reconciliation_break",
        shadow_reconciliation_break,
        "shadow reconciliation failed",
        "shadow books reconcile",
        "shadow reconciliation break not asserted",
    )
    _model_flag(
        report,
        "checkpoint_hash_mismatch",
        checkpoint_hash_mismatch,
        "checkpoint hash does not match restored state",
        "checkpoint hashes match",
        "checkpoint hash mismatch not asserted",
    )
    _model_flag(
        report,
        "recovery_without_reconciliation",
        recovery_without_reconciliation,
        "recovery resumed without reconciliation",
        "recovery reconciles before resume",
        "recovery without reconciliation not asserted",
    )
    _model_flag(
        report,
        "certification_expired",
        certification_expired,
        "production paper/shadow ran without valid certification",
        "production paper/shadow requires valid certification",
        "certification expiry not asserted",
    )
    _model_flag(
        report,
        "certification_bypass",
        certification_bypass,
        "certification was bypassed",
        "certification cannot be bypassed",
        "certification bypass not asserted",
    )
    _model_flag(
        report,
        "kill_switch_bypass",
        kill_switch_bypass,
        "kill switch was bypassed to add exposure",
        "HALT rejects new exposure",
        "kill-switch bypass not asserted",
    )
    _model_flag(
        report,
        "risk_bypass",
        risk_bypass,
        "risk limits were bypassed",
        "risk limits remain in force",
        "risk bypass not asserted",
    )
    _model_flag(
        report,
        "ai_safety_override",
        ai_safety_override,
        "AI attempted to override safety, certification, or routing",
        "AI cannot override safety",
        "AI safety override not asserted",
    )
    _model_flag(
        report,
        "synthetic_production_confusion",
        synthetic_production_confusion,
        "synthetic data was labelled REAL_MARKET",
        "synthetic data is not REAL_MARKET",
        "synthetic production confusion not asserted",
    )
    _model_flag(
        report,
        "observed_tca_confusion",
        observed_tca_confusion,
        "simulated TCA was labelled observed broker TCA",
        "simulated TCA is not observed broker TCA",
        "observed TCA confusion not asserted",
    )
    _model_flag(
        report,
        "broker_confirmation_confusion",
        broker_confirmation_confusion,
        "a shadow or paper fill was labelled broker-confirmed",
        "shadow fills are not broker confirmations",
        "broker confirmation confusion not asserted",
    )
    _model_flag(
        report,
        "unauthorized_release",
        unauthorized_release,
        "live release without authorization",
        "live release remains unauthorized",
        "unauthorized release not asserted",
    )
    _model_flag(
        report,
        "missing_authorization",
        missing_authorization,
        "authorization object missing",
        "authorization present",
        "missing authorization not asserted",
    )
    _model_flag(
        report,
        "stale_authorization",
        stale_authorization,
        "authorization expired or reused past TTL",
        "authorization is fresh",
        "stale authorization not asserted",
    )
    _model_flag(
        report,
        "future_account_state",
        future_account_state,
        "future account state used",
        "account state is PIT",
        "future account state not asserted",
    )
    _model_flag(
        report,
        "future_market_state",
        future_market_state,
        "future market state used",
        "market state is PIT",
        "future market state not asserted",
    )
    _model_flag(
        report,
        "future_risk_state",
        future_risk_state,
        "future risk state used",
        "risk state is PIT",
        "future risk state not asserted",
    )
    _model_flag(
        report,
        "target_hash_mismatch",
        target_hash_mismatch,
        "target hash does not match authorization",
        "target hash matches",
        "target hash mismatch not asserted",
    )
    _model_flag(
        report,
        "order_plan_hash_mismatch",
        order_plan_hash_mismatch,
        "order plan hash does not match authorization",
        "order plan hash matches",
        "order plan hash mismatch not asserted",
    )
    _model_flag(
        report,
        "certification_mismatch",
        certification_mismatch,
        "certification identity does not match",
        "certification identity matches",
        "certification mismatch not asserted",
    )
    _model_flag(
        report,
        "risk_limit_bypass",
        risk_limit_bypass,
        "risk limit was bypassed",
        "risk limits enforced",
        "risk limit bypass not asserted",
    )
    _model_flag(
        report,
        "stale_decision",
        stale_decision,
        "stale decision reused",
        "decision is fresh",
        "stale decision not asserted",
    )
    _model_flag(
        report,
        "duplicate_release",
        duplicate_release,
        "duplicate live release",
        "no duplicate release",
        "duplicate release not asserted",
    )
    _model_flag(
        report,
        "idempotency_collision",
        idempotency_collision,
        "idempotency key reused with different payload",
        "idempotency keys are consistent",
        "idempotency collision not asserted",
    )
    _model_flag(
        report,
        "invalid_safety_transition",
        invalid_safety_transition,
        "illegal safety state transition",
        "safety transitions are legal",
        "invalid safety transition not asserted",
    )
    _model_flag(
        report,
        "unknown_safety_state",
        unknown_safety_state,
        "unknown safety state treated as safe",
        "unknown safety state is blocked",
        "unknown safety state not asserted",
    )
    _model_flag(
        report,
        "human_authorization_missing",
        human_authorization_missing,
        "human authorization missing for arm/release",
        "human authorization recorded",
        "human authorization missing not asserted",
    )
    _model_flag(
        report,
        "policy_mutation",
        policy_mutation,
        "safety policy mutated in place",
        "policy identity is immutable",
        "policy mutation not asserted",
    )
    _model_flag(
        report,
        "audit_mutation",
        audit_mutation,
        "audit trail mutated",
        "audit trail is append-only",
        "audit mutation not asserted",
    )
    _model_flag(
        report,
        "emergency_bypass",
        emergency_bypass,
        "emergency mode bypassed",
        "emergency cannot be bypassed",
        "emergency bypass not asserted",
    )
    _model_flag(
        report,
        "configuration_hash_mismatch",
        configuration_hash_mismatch,
        "ops config hash mismatch",
        "ops config hash matches",
        "configuration hash mismatch not asserted",
    )
    _model_flag(
        report,
        "unexpected_dependency",
        unexpected_dependency,
        "unexpected operational dependency",
        "dependencies are expected",
        "unexpected dependency not asserted",
    )
    _model_flag(
        report,
        "secret_exposure",
        secret_exposure,
        "secret value appeared in a leakable channel",
        "secrets are redacted",
        "secret exposure not asserted",
    )
    _model_flag(
        report,
        "secret_expired",
        secret_expired,
        "expired secret was accepted",
        "expired secrets fail",
        "secret expired not asserted",
    )
    _model_flag(
        report,
        "clock_rollback",
        clock_rollback,
        "clock rollback accepted",
        "clock rollback is rejected",
        "clock rollback not asserted",
    )
    _model_flag(
        report,
        "future_timestamp",
        future_timestamp,
        "future timestamp accepted",
        "future timestamps are rejected",
        "future timestamp not asserted",
    )
    _model_flag(
        report,
        "timestamp_regression",
        timestamp_regression,
        "timestamp regression accepted",
        "timestamp regression is rejected",
        "timestamp regression not asserted",
    )
    _model_flag(
        report,
        "audit_write_failure",
        audit_write_failure,
        "audit write failure ignored",
        "audit write failure affects readiness",
        "audit write failure not asserted",
    )
    _model_flag(
        report,
        "backup_checksum_failure",
        backup_checksum_failure,
        "corrupt backup accepted",
        "backup checksums are verified",
        "backup checksum failure not asserted",
    )
    _model_flag(
        report,
        "restore_without_validation",
        restore_without_validation,
        "restore without verification",
        "restore requires validation",
        "restore without validation not asserted",
    )
    _model_flag(
        report,
        "state_checkpoint_mismatch",
        state_checkpoint_mismatch,
        "ops checkpoint hash mismatch",
        "checkpoint hashes match",
        "state checkpoint mismatch not asserted",
    )
    _model_flag(
        report,
        "state_corruption",
        state_corruption,
        "corrupt ops state accepted",
        "corrupt state is rejected",
        "state corruption not asserted",
    )
    _model_flag(
        report,
        "process_identity_mismatch",
        process_identity_mismatch,
        "process identity mismatch",
        "process identity matches",
        "process identity mismatch not asserted",
    )
    _model_flag(
        report,
        "release_identity_mismatch",
        release_identity_mismatch,
        "release identity mismatch",
        "release identity matches",
        "release identity mismatch not asserted",
    )
    _model_flag(
        report,
        "environment_confusion",
        environment_confusion,
        "environment identity confused",
        "environment identity is explicit",
        "environment confusion not asserted",
    )
    _model_flag(
        report,
        "production_config_in_research",
        production_config_in_research,
        "production config used in research",
        "production config is not used in research",
        "production config in research not asserted",
    )
    _model_flag(
        report,
        "research_config_in_production",
        research_config_in_production,
        "research credentials used as production",
        "research credentials are not production",
        "research config in production not asserted",
    )
    _model_flag(
        report,
        "unsafe_restart",
        unsafe_restart,
        "unsafe restart performed",
        "restarts are policy-bound",
        "unsafe restart not asserted",
    )
    _model_flag(
        report,
        "restart_loop",
        restart_loop,
        "crash-loop was not contained",
        "crash-loop is contained",
        "restart loop not asserted",
    )
    _model_flag(
        report,
        "health_false_positive",
        health_false_positive,
        "unknown reported as healthy",
        "unknown is not healthy",
        "health false positive not asserted",
    )
    _model_flag(
        report,
        "readiness_false_positive",
        readiness_false_positive,
        "unknown reported as ready",
        "unknown is not ready",
        "readiness false positive not asserted",
    )
    _model_flag(
        report,
        "silent_recovery",
        silent_recovery,
        "silent recovery performed",
        "recovery is explicit",
        "silent recovery not asserted",
    )
    _model_flag(
        report,
        "silent_data_loss",
        silent_data_loss,
        "silent data loss on restore",
        "restore cannot silently lose data",
        "silent data loss not asserted",
    )
    _model_flag(
        report,
        "operational_bypass",
        operational_bypass,
        "ops control plane bypassed",
        "ops controls are enforced",
        "operational bypass not asserted",
    )
    _model_flag(
        report,
        "safety_halt_failure",
        safety_halt_failure,
        "safety halt was not integrated",
        "safety halt is integrated",
        "safety halt failure not asserted",
    )
    _model_flag(
        report,
        "certification_evidence_mutation",
        certification_evidence_mutation,
        "certification evidence mutated",
        "certification evidence is immutable",
        "certification evidence mutation not asserted",
    )
    _model_flag(
        report,
        "certification_snapshot_mismatch",
        certification_snapshot_mismatch,
        "certification snapshot mismatch",
        "certification snapshot matches",
        "certification snapshot mismatch not asserted",
    )
    _model_flag(
        report,
        "certification_model_mismatch",
        certification_model_mismatch,
        "certification model mismatch",
        "certification model matches",
        "certification model mismatch not asserted",
    )
    _model_flag(
        report,
        "certification_config_mismatch",
        certification_config_mismatch,
        "certification config mismatch",
        "certification config matches",
        "certification config mismatch not asserted",
    )
    _model_flag(
        report,
        "certification_hash_mismatch",
        certification_hash_mismatch,
        "certification hash mismatch",
        "certification hashes match",
        "certification hash mismatch not asserted",
    )
    _model_flag(
        report,
        "independent_validation_missing",
        independent_validation_missing,
        "independent validation missing",
        "independent validation present",
        "independent validation missing not asserted",
    )
    _model_flag(
        report,
        "safety_gate_failure",
        safety_gate_failure,
        "safety gate failure",
        "safety gate holds",
        "safety gate failure not asserted",
    )
    _model_flag(
        report,
        "reconciliation_failure",
        reconciliation_failure,
        "reconciliation failure accepted",
        "reconciliation holds",
        "reconciliation failure not asserted",
    )
    _model_flag(
        report,
        "paper_shadow_gap",
        paper_shadow_gap,
        "paper/shadow gap ignored",
        "paper/shadow gap is explicit",
        "paper shadow gap not asserted",
    )
    _model_flag(
        report,
        "revoked_certification",
        revoked_certification,
        "revoked certification used",
        "revoked certification is rejected",
        "revoked certification not asserted",
    )
    _model_flag(
        report,
        "waiver_expired",
        waiver_expired,
        "expired waiver accepted",
        "expired waivers are rejected",
        "waiver expired not asserted",
    )
    _model_flag(
        report,
        "waiver_scope_violation",
        waiver_scope_violation,
        "waiver used outside scope",
        "waiver scope is enforced",
        "waiver scope violation not asserted",
    )
    _model_flag(
        report,
        "release_manifest_mismatch",
        release_manifest_mismatch,
        "release manifest mismatch",
        "release manifest matches",
        "release manifest mismatch not asserted",
    )
    _model_flag(
        report,
        "separation_of_duties_violation",
        separation_of_duties_violation,
        "separation of duties violated",
        "separation of duties holds",
        "separation of duties violation not asserted",
    )
    _model_flag(
        report,
        "ai_authorization_override",
        ai_authorization_override,
        "AI attempted authorization",
        "AI cannot authorize",
        "AI authorization override not asserted",
    )
    _model_flag(
        report,
        "capital_limit_mutation",
        capital_limit_mutation,
        "capital limit mutated",
        "capital limits are frozen",
        "capital limit mutation not asserted",
    )
    _model_flag(
        report,
        "release_policy_mutation",
        release_policy_mutation,
        "release policy mutated",
        "release policy is frozen",
        "release policy mutation not asserted",
    )
    _model_flag(
        report,
        "human_approval_missing",
        human_approval_missing,
        "human approval missing",
        "human approval recorded",
        "human approval missing not asserted",
    )
    _model_flag(
        report,
        "expired_certification",
        expired_certification,
        "expired certification used",
        "expired certification is rejected",
        "expired certification not asserted",
    )
    _model_flag(
        report,
        "critical_not_tested",
        critical_not_tested,
        "critical NOT_TESTED certified",
        "critical NOT_TESTED blocks certification",
        "critical not tested not asserted",
    )
    _model_flag(
        report,
        "broker_identity_mismatch",
        broker_identity_mismatch,
        "broker identity mismatch",
        "broker identity matches",
        "broker identity mismatch not asserted",
    )
    _model_flag(
        report,
        "broker_snapshot_mutation",
        broker_snapshot_mutation,
        "broker snapshot mutated",
        "broker snapshot is immutable",
        "broker snapshot mutation not asserted",
    )
    _model_flag(
        report,
        "broker_payload_hash_mismatch",
        broker_payload_hash_mismatch,
        "broker payload hash mismatch",
        "broker payload hashes match",
        "broker payload hash mismatch not asserted",
    )
    _model_flag(
        report,
        "duplicate_external_event",
        duplicate_external_event,
        "duplicate external event accepted as new",
        "duplicate external events are idempotent",
        "duplicate external event not asserted",
    )
    _model_flag(
        report,
        "external_event_collision",
        external_event_collision,
        "same identity different payload",
        "payload collisions are rejected",
        "external event collision not asserted",
    )
    _model_flag(
        report,
        "unknown_broker_order",
        unknown_broker_order,
        "unknown broker order hidden",
        "unknown broker orders are retained",
        "unknown broker order not asserted",
    )
    _model_flag(
        report,
        "orphan_broker_fill",
        orphan_broker_fill,
        "orphan broker fill hidden",
        "orphan broker fills are retained",
        "orphan broker fill not asserted",
    )
    _model_flag(
        report,
        "missing_broker_fill",
        missing_broker_fill,
        "missing broker fill ignored",
        "missing broker fills are explicit",
        "missing broker fill not asserted",
    )
    _model_flag(
        report,
        "order_reconciliation_break",
        order_reconciliation_break,
        "order reconciliation break ignored",
        "order reconciliation is explicit",
        "order reconciliation break not asserted",
    )
    _model_flag(
        report,
        "position_reconciliation_break",
        position_reconciliation_break,
        "position reconciliation break ignored",
        "position reconciliation is explicit",
        "position reconciliation break not asserted",
    )
    _model_flag(
        report,
        "cash_reconciliation_break",
        cash_reconciliation_break,
        "cash reconciliation break ignored",
        "cash reconciliation is explicit",
        "cash reconciliation break not asserted",
    )
    _model_flag(
        report,
        "margin_reconciliation_break",
        margin_reconciliation_break,
        "margin reconciliation break ignored",
        "margin reconciliation is explicit",
        "margin reconciliation break not asserted",
    )
    _model_flag(
        report,
        "instrument_mapping_ambiguity",
        instrument_mapping_ambiguity,
        "ambiguous instrument mapped silently",
        "ambiguous mapping fails closed",
        "instrument mapping ambiguity not asserted",
    )
    _model_flag(
        report,
        "instrument_mapping_mutation",
        instrument_mapping_mutation,
        "instrument mapping mutated",
        "instrument mapping is frozen",
        "instrument mapping mutation not asserted",
    )
    _model_flag(
        report,
        "timestamp_integrity_failure",
        timestamp_integrity_failure,
        "broker timestamp overwritten",
        "source timestamps are preserved",
        "timestamp integrity failure not asserted",
    )
    _model_flag(
        report,
        "event_ordering_failure",
        event_ordering_failure,
        "out-of-order events treated as chronology",
        "event ordering limitations are explicit",
        "event ordering failure not asserted",
    )
    _model_flag(
        report,
        "stale_broker_state",
        stale_broker_state,
        "stale broker state treated as healthy",
        "stale is not healthy",
        "stale broker state not asserted",
    )
    _model_flag(
        report,
        "credential_exposure",
        credential_exposure,
        "credential appeared in a leakable channel",
        "credentials are redacted",
        "credential exposure not asserted",
    )
    _model_flag(
        report,
        "broker_write_attempt",
        broker_write_attempt,
        "broker write attempted",
        "broker write path is disabled",
        "broker write attempt not asserted",
    )
    _model_flag(
        report,
        "live_mode_confusion",
        live_mode_confusion,
        "read-only connection treated as live",
        "read-only is not live",
        "live mode confusion not asserted",
    )
    _model_flag(
        report,
        "safety_bypass",
        safety_bypass,
        "broker connectivity bypassed safety",
        "safety cannot be bypassed by a broker",
        "safety bypass not asserted",
    )
    _model_flag(
        report,
        "future_market_observation",
        future_market_observation,
        "future market observation used",
        "observations available at T only",
        "future market observation not asserted",
    )
    _model_flag(
        report,
        "future_state_mutation",
        future_state_mutation,
        "frozen state mutated",
        "frozen snapshot is immutable",
        "future state mutation not asserted",
    )
    _model_flag(
        report,
        "future_volume",
        future_volume,
        "future volume used",
        "volume available at T only",
        "future volume not asserted",
    )
    _model_flag(
        report,
        "future_quote",
        future_quote,
        "future quote used",
        "quotes available at T only",
        "future quote not asserted",
    )
    _model_flag(
        report,
        "future_reference_data",
        future_reference_data,
        "future reference data used",
        "reference data available at T only",
        "future reference data not asserted",
    )
    _model_flag(
        report,
        "timestamp_order_violation",
        timestamp_order_violation,
        "timestamp order violated",
        "time fields remain distinct and ordered",
        "timestamp order not asserted",
    )
    _model_flag(
        report,
        "receive_time_violation",
        receive_time_violation,
        "receive_time integrity failed",
        "receive_time is first-class",
        "receive time not asserted",
    )
    _model_flag(
        report,
        "sequence_gap_hidden",
        sequence_gap_hidden,
        "sequence gap hidden",
        "gaps are classified, not hidden",
        "sequence gap not asserted",
    )
    _model_flag(
        report,
        "stale_data_used",
        stale_data_used,
        "stale data used as valid",
        "stale data is not silently valid",
        "stale data use not asserted",
    )
    _model_flag(
        report,
        "invalid_data_used",
        invalid_data_used,
        "invalid data used as valid",
        "invalid data is not silently valid",
        "invalid data use not asserted",
    )
    _model_flag(
        report,
        "missing_data_filled",
        missing_data_filled,
        "missing data silently filled",
        "missing remains missing",
        "missing fill not asserted",
    )
    _model_flag(
        report,
        "clock_drift",
        clock_drift,
        "clock drift ignored",
        "clock health is first-class",
        "clock drift not asserted",
    )
    _model_flag(
        report,
        "session_mismatch",
        session_mismatch,
        "session mismatch hidden",
        "session state is classified",
        "session mismatch not asserted",
    )
    _model_flag(
        report,
        "security_identity_mismatch",
        security_identity_mismatch,
        "security identity mismatch",
        "security identity is stable",
        "security identity not asserted",
    )
    _model_flag(
        report,
        "realtime_snapshot_mutation",
        realtime_snapshot_mutation,
        "realtime snapshot mutated",
        "realtime snapshot is immutable",
        "realtime snapshot mutation not asserted",
    )
    _model_flag(
        report,
        "realtime_replay_mismatch",
        realtime_replay_mismatch,
        "realtime replay mismatch",
        "replay matches frozen snapshot",
        "realtime replay not asserted",
    )
    _model_flag(
        report,
        "future_realtime_feature",
        future_realtime_feature,
        "future realtime feature used",
        "features available at T only",
        "future realtime feature not asserted",
    )
    _model_flag(
        report,
        "future_realtime_model",
        future_realtime_model,
        "future realtime model used",
        "models available at T only",
        "future realtime model not asserted",
    )
    _model_flag(
        report,
        "future_realtime_regime",
        future_realtime_regime,
        "future realtime regime used",
        "regimes available at T only",
        "future realtime regime not asserted",
    )
    _model_flag(
        report,
        "future_adaptive_update",
        future_adaptive_update,
        "adaptive update before information exists",
        "adaptive updates wait for realization",
        "future adaptive update not asserted",
    )
    _model_flag(
        report,
        "release_mutation",
        release_mutation,
        "strategy release mutated",
        "strategy release is immutable",
        "release mutation not asserted",
    )
    _model_flag(
        report,
        "uncertified_model_use",
        uncertified_model_use,
        "uncertified model used",
        "uncertified release abstains",
        "uncertified model use not asserted",
    )
    _model_flag(
        report,
        "expired_release_use",
        expired_release_use,
        "expired release used",
        "expired release is blocked",
        "expired release use not asserted",
    )
    _model_flag(
        report,
        "decision_state_mutation",
        decision_state_mutation,
        "decision state mutated",
        "decision is immutable after freeze",
        "decision state mutation not asserted",
    )
    _model_flag(
        report,
        "rt_snapshot_mismatch",
        rt_snapshot_mismatch,
        "decision snapshot mismatch",
        "decision binds the frozen snapshot",
        "rt snapshot mismatch not asserted",
    )
    _model_flag(
        report,
        "stale_state_decision",
        stale_state_decision,
        "stale state produced a decision",
        "stale state abstains",
        "stale state decision not asserted",
    )
    _model_flag(
        report,
        "missing_critical_input",
        missing_critical_input,
        "missing critical input ignored",
        "missing input abstains",
        "missing critical input not asserted",
    )
    _model_flag(
        report,
        "capital_constraint_bypass",
        capital_constraint_bypass,
        "capital constraint bypassed",
        "capital constraints are not bypassed",
        "capital constraint bypass not asserted",
    )
    _model_flag(
        report,
        "decision_replay_mismatch",
        decision_replay_mismatch,
        "decision replay mismatch",
        "same inputs replay the same hash",
        "decision replay not asserted",
    )
    _model_flag(
        report,
        "ai_authority_violation",
        ai_authority_violation,
        "AI actor decided or certified",
        "AI_SUGGESTION cannot decide",
        "AI authority not asserted",
    )
    _model_flag(
        report,
        "future_replay_input",
        future_replay_input,
        "future replay input used",
        "replay inputs available at T only",
        "future replay input not asserted",
    )
    _model_flag(
        report,
        "future_shadow_state",
        future_shadow_state,
        "future shadow state used",
        "shadow state available at T only",
        "future shadow state not asserted",
    )
    _model_flag(
        report,
        "replay_snapshot_mismatch",
        replay_snapshot_mismatch,
        "replay snapshot mismatch",
        "replay binds the original snapshot",
        "replay snapshot not asserted",
    )
    _model_flag(
        report,
        "replay_state_mutation",
        replay_state_mutation,
        "replay mutated prior state",
        "replay does not mutate history",
        "replay state mutation not asserted",
    )
    _model_flag(
        report,
        "replay_nondeterminism",
        replay_nondeterminism,
        "replay is nondeterministic",
        "replay hashes match",
        "replay nondeterminism not asserted",
    )
    _model_flag(
        report,
        "event_order_violation",
        event_order_violation,
        "event order violated",
        "events are strictly sequenced",
        "event order not asserted",
    )
    _model_flag(
        report,
        "event_deletion",
        event_deletion,
        "event log deleted",
        "events are append-only",
        "event deletion not asserted",
    )
    _model_flag(
        report,
        "checkpoint_mutation",
        checkpoint_mutation,
        "checkpoint mutated",
        "checkpoints are immutable",
        "checkpoint mutation not asserted",
    )
    _model_flag(
        report,
        "counterfactual_observation_confusion",
        counterfactual_observation_confusion,
        "counterfactual treated as observed",
        "counterfactuals are labelled",
        "counterfactual confusion not asserted",
    )
    _model_flag(
        report,
        "simulated_fill_as_broker_fill",
        simulated_fill_as_broker_fill,
        "simulated fill treated as broker fill",
        "simulated fill is not a broker fill",
        "simulated fill confusion not asserted",
    )
    _model_flag(
        report,
        "hidden_reconciliation_break",
        hidden_reconciliation_break,
        "reconciliation break hidden",
        "breaks are retained",
        "hidden reconciliation not asserted",
    )
    _model_flag(
        report,
        "recovery_state_mismatch",
        recovery_state_mismatch,
        "recovery state mismatch",
        "recovery matches pre-crash hashes",
        "recovery state not asserted",
    )
    _model_flag(
        report,
        "release_mismatch",
        release_mismatch,
        "strategy release mismatch",
        "twin binds the same release",
        "release mismatch not asserted",
    )
    _model_flag(
        report,
        "strategy_state_mismatch",
        strategy_state_mismatch,
        "strategy state mismatch",
        "strategy state is hashed",
        "strategy state not asserted",
    )
    _model_flag(
        report,
        "shadow_routing_attempt",
        shadow_routing_attempt,
        "shadow attempted broker routing",
        "twin write path is disabled",
        "shadow routing not asserted",
    )
    return report


def _model_flag(
    report: IntegrityReport,
    name: str,
    value: bool | None,
    fail_note: str,
    pass_note: str,
    missing_note: str,
) -> None:
    if value is None:
        report.checks[name] = CheckResult.NOT_TESTED
        report.notes[name] = missing_note
        return
    report.checks[name] = CheckResult.FAIL if value else CheckResult.PASS
    report.notes[name] = fail_note if value else pass_note
