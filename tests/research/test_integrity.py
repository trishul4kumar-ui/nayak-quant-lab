from datetime import UTC, datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.research.integrity import evaluate_integrity


def _bar(day: datetime) -> OHLCVBar:
    pit = PointInTime(event_time=day, effective_time=day, available_time=day, ingestion_time=day)
    return OHLCVBar(
        instrument=InstrumentId.parse("NSE:TCS"),
        pit=pit,
        open=10,
        high=11,
        low=9,
        close=10,
    )


def test_zero_cost_fails() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    report = evaluate_integrity(
        bars=[_bar(day)],
        states=[],
        as_of_times=[day],
        next_bar_fill=True,
        cost_bps=0.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
    )
    assert report.checks["transaction_cost_underestimation"] is CheckResult.FAIL
    assert report.failed()


def test_same_bar_fill_fails_lookahead() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    report = evaluate_integrity(
        bars=[_bar(day)],
        states=[],
        as_of_times=[day],
        next_bar_fill=False,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
    )
    assert report.checks["look_ahead_bias"] is CheckResult.FAIL


def test_unimplemented_checks_are_not_tested() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    report = evaluate_integrity(
        bars=[_bar(day)],
        states=[],
        as_of_times=[day],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
    )
    assert report.checks["survivorship_bias"] is CheckResult.NOT_TESTED
    assert report.checks["corporate_action_leakage"] is CheckResult.NOT_TESTED
    assert report.checks["look_ahead_bias"] is CheckResult.PASS
    assert report.checks["walk_forward"] is CheckResult.NOT_TESTED
    assert report.checks["embargo"] is CheckResult.NOT_TESTED
    assert report.checks["purge"] is CheckResult.NOT_TESTED
    assert report.checks["future_parameter_selection"] is CheckResult.NOT_TESTED
    assert report.checks["label_as_feature"] is CheckResult.NOT_TESTED
    assert report.checks["future_normalization"] is CheckResult.NOT_TESTED
    assert report.checks["future_ranking_universe"] is CheckResult.NOT_TESTED
    assert report.checks["feature_available_time"] is CheckResult.NOT_TESTED
    assert report.checks["future_covariance"] is CheckResult.NOT_TESTED
    assert report.checks["future_factor"] is CheckResult.NOT_TESTED
    assert report.checks["future_beta"] is CheckResult.NOT_TESTED
    assert report.checks["future_regime"] is CheckResult.NOT_TESTED
    assert report.checks["hmm_smoothing"] is CheckResult.NOT_TESTED
    assert report.checks["full_sample_regime_fit"] is CheckResult.NOT_TESTED
    assert report.checks["online_update_order"] is CheckResult.NOT_TESTED
    assert report.checks["future_adaptive_parameter"] is CheckResult.NOT_TESTED
    assert report.checks["future_ensemble_performance"] is CheckResult.NOT_TESTED
    assert report.checks["holdout_contamination"] is CheckResult.NOT_TESTED
    assert report.checks["future_model_training"] is CheckResult.NOT_TESTED
    assert report.checks["future_pca"] is CheckResult.NOT_TESTED
    assert report.checks["future_feature_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_hyperparameter"] is CheckResult.NOT_TESTED
    assert report.checks["future_calibration"] is CheckResult.NOT_TESTED
    assert report.checks["cross_section_future_leak"] is CheckResult.NOT_TESTED
    assert report.checks["model_replay_leak"] is CheckResult.NOT_TESTED
    assert report.checks["model_state_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_component_performance"] is CheckResult.NOT_TESTED
    assert report.checks["future_ensemble_weight"] is CheckResult.NOT_TESTED
    assert report.checks["future_correlation"] is CheckResult.NOT_TESTED
    assert report.checks["future_meta_feature"] is CheckResult.NOT_TESTED
    assert report.checks["future_component_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_stacking_prediction"] is CheckResult.NOT_TESTED
    assert report.checks["future_pruning"] is CheckResult.NOT_TESTED
    assert report.checks["stacking_leak"] is CheckResult.NOT_TESTED
    assert report.checks["full_sample_ensemble_replay"] is CheckResult.NOT_TESTED
    assert report.checks["future_volume_leak"] is CheckResult.NOT_TESTED
    assert report.checks["future_spread_leak"] is CheckResult.NOT_TESTED
    assert report.checks["future_liquidity_leak"] is CheckResult.NOT_TESTED
    assert report.checks["future_impact_parameter"] is CheckResult.NOT_TESTED
    assert report.checks["future_execution_parameter"] is CheckResult.NOT_TESTED
    assert report.checks["future_latency"] is CheckResult.NOT_TESTED
    assert report.checks["pre_arrival_fill"] is CheckResult.NOT_TESTED
    assert report.checks["full_fill_assumption"] is CheckResult.NOT_TESTED
    assert report.checks["zero_cost_execution"] is CheckResult.NOT_TESTED
    assert report.checks["negative_execution_cost"] is CheckResult.NOT_TESTED
    assert report.checks["wrong_side_slippage"] is CheckResult.NOT_TESTED
    assert report.checks["wrong_side_impact"] is CheckResult.NOT_TESTED
    assert report.checks["hidden_partial_fill"] is CheckResult.NOT_TESTED
    assert report.checks["capacity_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["execution_model_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_execution_calibration"] is CheckResult.NOT_TESTED
    assert report.checks["experiment_identity_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["experiment_config_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_experiment_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_candidate_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_hypothesis_selection"] is CheckResult.NOT_TESTED
    assert report.checks["hidden_candidate"] is CheckResult.NOT_TESTED
    assert report.checks["hidden_failed_experiment"] is CheckResult.NOT_TESTED
    assert report.checks["hidden_search"] is CheckResult.NOT_TESTED
    assert report.checks["posthoc_stopping"] is CheckResult.NOT_TESTED
    assert report.checks["multiple_testing_omission"] is CheckResult.NOT_TESTED
    assert report.checks["family_definition_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["research_budget_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["replication_contamination"] is CheckResult.NOT_TESTED
    assert report.checks["holdout_reuse"] is CheckResult.NOT_TESTED
    assert report.checks["future_baseline_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_model_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_execution_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_cost_selection"] is CheckResult.NOT_TESTED
    assert report.checks["lineage_break"] is CheckResult.NOT_TESTED
    assert report.checks["dataset_snapshot_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["result_overwrite"] is CheckResult.NOT_TESTED
    assert report.checks["parallel_state_leak"] is CheckResult.NOT_TESTED
    assert report.checks["adaptive_state_cross_contamination"] is CheckResult.NOT_TESTED
    assert report.checks["future_expression_input"] is CheckResult.NOT_TESTED
    assert report.checks["future_candidate_generation"] is CheckResult.NOT_TESTED
    assert report.checks["future_search_state"] is CheckResult.NOT_TESTED
    assert report.checks["future_fitness"] is CheckResult.NOT_TESTED
    assert report.checks["future_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_crossover"] is CheckResult.NOT_TESTED
    assert report.checks["future_feature"] is CheckResult.NOT_TESTED
    assert report.checks["posthoc_search_budget"] is CheckResult.NOT_TESTED
    assert report.checks["search_space_omission"] is CheckResult.NOT_TESTED
    assert report.checks["candidate_lineage_break"] is CheckResult.NOT_TESTED
    assert report.checks["expression_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_redundancy"] is CheckResult.NOT_TESTED
    assert report.checks["future_novelty"] is CheckResult.NOT_TESTED
    assert report.checks["future_complexity_selection"] is CheckResult.NOT_TESTED
    assert report.checks["knowledge_provenance_break"] is CheckResult.NOT_TESTED
    assert report.checks["evidence_without_experiment"] is CheckResult.NOT_TESTED
    assert report.checks["claim_without_evidence"] is CheckResult.NOT_TESTED
    assert report.checks["claim_overstates_evidence"] is CheckResult.NOT_TESTED
    assert report.checks["candidate_history_deleted"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_identity_collision"] is CheckResult.NOT_TESTED
    assert report.checks["snapshot_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["historical_claim_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_knowledge_leak"] is CheckResult.NOT_TESTED
    assert report.checks["future_claim_context"] is CheckResult.NOT_TESTED
    assert report.checks["replication_same_data"] is CheckResult.NOT_TESTED
    assert report.checks["contradiction_hidden"] is CheckResult.NOT_TESTED
    assert report.checks["search_degree_of_freedom_loss"] is CheckResult.NOT_TESTED
    assert report.checks["synthetic_evidence_overpromotion"] is CheckResult.NOT_TESTED
    assert report.checks["ai_evidence_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["future_capital_input"] is CheckResult.NOT_TESTED
    assert report.checks["future_risk_input"] is CheckResult.NOT_TESTED
    assert report.checks["future_expected_return"] is CheckResult.NOT_TESTED
    assert report.checks["future_factor_exposure"] is CheckResult.NOT_TESTED
    assert report.checks["future_liquidity"] is CheckResult.NOT_TESTED
    assert report.checks["future_turnover_state"] is CheckResult.NOT_TESTED
    assert report.checks["future_drawdown_state"] is CheckResult.NOT_TESTED
    assert report.checks["future_constraint_parameter"] is CheckResult.NOT_TESTED
    assert report.checks["future_position_reference"] is CheckResult.NOT_TESTED
    assert report.checks["future_decision_state"] is CheckResult.NOT_TESTED
    assert report.checks["capital_policy_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["decision_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["decision_hash_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["allocation_lineage_break"] is CheckResult.NOT_TESTED
    assert report.checks["hidden_constraint_relaxation"] is CheckResult.NOT_TESTED
    assert report.checks["silent_fallback"] is CheckResult.NOT_TESTED
    assert report.checks["unknown_liquidity_as_infinite"] is CheckResult.NOT_TESTED
    assert report.checks["unknown_factor_as_zero"] is CheckResult.NOT_TESTED
    assert report.checks["synthetic_capital_overpromotion"] is CheckResult.NOT_TESTED
    assert report.checks["gate_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["abstention_suppression"] is CheckResult.NOT_TESTED
    assert report.checks["future_portfolio_state"] is CheckResult.NOT_TESTED
    assert report.checks["future_execution_cost"] is CheckResult.NOT_TESTED
    assert report.checks["target_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["order_intent_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["order_plan_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_order"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_fill"] is CheckResult.NOT_TESTED
    assert report.checks["invalid_order_transition"] is CheckResult.NOT_TESTED
    assert report.checks["future_execution_price"] is CheckResult.NOT_TESTED
    assert report.checks["future_fill_information"] is CheckResult.NOT_TESTED
    assert report.checks["cash_accounting_break"] is CheckResult.NOT_TESTED
    assert report.checks["position_accounting_break"] is CheckResult.NOT_TESTED
    assert report.checks["target_position_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["order_fill_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["orphan_fill"] is CheckResult.NOT_TESTED
    assert report.checks["orphan_event"] is CheckResult.NOT_TESTED
    assert report.checks["reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["execution_policy_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["paper_live_mode_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["broker_import_violation"] is CheckResult.NOT_TESTED
    assert report.checks["future_performance_mark"] is CheckResult.NOT_TESTED
    assert report.checks["future_attribution_input"] is CheckResult.NOT_TESTED
    assert report.checks["future_benchmark"] is CheckResult.NOT_TESTED
    assert report.checks["future_factor_return"] is CheckResult.NOT_TESTED
    assert report.checks["performance_snapshot_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["position_history_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["pnl_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["attribution_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["hidden_residual"] is CheckResult.NOT_TESTED
    assert report.checks["benchmark_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["target_observation_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["posthoc_attribution"] is CheckResult.NOT_TESTED
    assert report.checks["performance_claim_overstatement"] is CheckResult.NOT_TESTED
    assert report.checks["future_available_data"] is CheckResult.NOT_TESTED
    assert report.checks["event_available_time_conflict"] is CheckResult.NOT_TESTED
    assert report.checks["source_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["checksum_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_observation"] is CheckResult.NOT_TESTED
    assert report.checks["identity_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["symbol_history_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["corporate_action_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["adjustment_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["calendar_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["universe_survivorship_leak"] is CheckResult.NOT_TESTED
    assert report.checks["delisted_security_omission"] is CheckResult.NOT_TESTED
    assert report.checks["cross_source_conflict"] is CheckResult.NOT_TESTED
    assert report.checks["snapshot_dependency_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["raw_to_derived_lineage_break"] is CheckResult.NOT_TESTED
    assert report.checks["timezone_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["future_tca_observation"] is CheckResult.NOT_TESTED
    assert report.checks["future_impact_calibration"] is CheckResult.NOT_TESTED
    assert report.checks["future_spread_calibration"] is CheckResult.NOT_TESTED
    assert report.checks["future_volume_calibration"] is CheckResult.NOT_TESTED
    assert report.checks["future_liquidity_calibration"] is CheckResult.NOT_TESTED
    assert report.checks["future_capacity_parameter"] is CheckResult.NOT_TESTED
    assert report.checks["arrival_price_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["benchmark_price_lookahead"] is CheckResult.NOT_TESTED
    assert report.checks["posthoc_cost_model"] is CheckResult.NOT_TESTED
    assert report.checks["calibration_window_leak"] is CheckResult.NOT_TESTED
    assert report.checks["future_fill_observation"] is CheckResult.NOT_TESTED
    assert report.checks["synthetic_adv_claim"] is CheckResult.NOT_TESTED
    assert report.checks["observed_vs_modelled_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["tca_parameter_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_stationarity_window"] is CheckResult.NOT_TESTED
    assert report.checks["future_lag_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_break_detection"] is CheckResult.NOT_TESTED
    assert report.checks["future_cointegration_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_var_selection"] is CheckResult.NOT_TESTED
    assert report.checks["future_causal_control"] is CheckResult.NOT_TESTED
    assert report.checks["future_event_window"] is CheckResult.NOT_TESTED
    assert report.checks["future_parameter_estimation"] is CheckResult.NOT_TESTED
    assert report.checks["full_sample_econometric_replay"] is CheckResult.NOT_TESTED
    assert report.checks["future_residual_normalization"] is CheckResult.NOT_TESTED
    assert report.checks["future_panel_selection"] is CheckResult.NOT_TESTED
    assert report.checks["causal_post_treatment_control"] is CheckResult.NOT_TESTED
    assert report.checks["lookahead_event_study"] is CheckResult.NOT_TESTED
    assert report.checks["illegal_certification_transition"] is CheckResult.NOT_TESTED
    assert report.checks["synthetic_production_evidence"] is CheckResult.NOT_TESTED
    assert report.checks["reproduction_break"] is CheckResult.NOT_TESTED
    assert report.checks["waiver_without_authority"] is CheckResult.NOT_TESTED
    assert report.checks["ai_certification_override"] is CheckResult.NOT_TESTED
    assert report.checks["critical_not_tested_certified"] is CheckResult.NOT_TESTED
    assert report.checks["future_shadow_data"] is CheckResult.NOT_TESTED
    assert report.checks["future_decision_input"] is CheckResult.NOT_TESTED
    assert report.checks["future_execution_input"] is CheckResult.NOT_TESTED
    assert report.checks["stale_data_decision"] is CheckResult.NOT_TESTED
    assert report.checks["unknown_calendar_execution"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_cycle"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_shadow_order"] is CheckResult.NOT_TESTED
    assert report.checks["shadow_live_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["live_route_attempt"] is CheckResult.NOT_TESTED
    assert report.checks["paper_shadow_state_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["model_version_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["configuration_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["pre_arrival_shadow_fill"] is CheckResult.NOT_TESTED
    assert report.checks["future_shadow_fill"] is CheckResult.NOT_TESTED
    assert report.checks["partial_fill_hidden"] is CheckResult.NOT_TESTED
    assert report.checks["shadow_accounting_break"] is CheckResult.NOT_TESTED
    assert report.checks["shadow_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["checkpoint_hash_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["recovery_without_reconciliation"] is CheckResult.NOT_TESTED
    assert report.checks["certification_expired"] is CheckResult.NOT_TESTED
    assert report.checks["certification_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["kill_switch_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["risk_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["ai_safety_override"] is CheckResult.NOT_TESTED
    assert report.checks["synthetic_production_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["observed_tca_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["broker_confirmation_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["unauthorized_release"] is CheckResult.NOT_TESTED
    assert report.checks["missing_authorization"] is CheckResult.NOT_TESTED
    assert report.checks["stale_authorization"] is CheckResult.NOT_TESTED
    assert report.checks["future_account_state"] is CheckResult.NOT_TESTED
    assert report.checks["future_market_state"] is CheckResult.NOT_TESTED
    assert report.checks["future_risk_state"] is CheckResult.NOT_TESTED
    assert report.checks["target_hash_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["order_plan_hash_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["certification_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["risk_limit_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["stale_decision"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_release"] is CheckResult.NOT_TESTED
    assert report.checks["idempotency_collision"] is CheckResult.NOT_TESTED
    assert report.checks["invalid_safety_transition"] is CheckResult.NOT_TESTED
    assert report.checks["unknown_safety_state"] is CheckResult.NOT_TESTED
    assert report.checks["human_authorization_missing"] is CheckResult.NOT_TESTED
    assert report.checks["policy_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["audit_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["emergency_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["configuration_hash_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["unexpected_dependency"] is CheckResult.NOT_TESTED
    assert report.checks["secret_exposure"] is CheckResult.NOT_TESTED
    assert report.checks["secret_expired"] is CheckResult.NOT_TESTED
    assert report.checks["clock_rollback"] is CheckResult.NOT_TESTED
    assert report.checks["future_timestamp"] is CheckResult.NOT_TESTED
    assert report.checks["timestamp_regression"] is CheckResult.NOT_TESTED
    assert report.checks["audit_write_failure"] is CheckResult.NOT_TESTED
    assert report.checks["backup_checksum_failure"] is CheckResult.NOT_TESTED
    assert report.checks["restore_without_validation"] is CheckResult.NOT_TESTED
    assert report.checks["state_checkpoint_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["state_corruption"] is CheckResult.NOT_TESTED
    assert report.checks["process_identity_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["release_identity_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["environment_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["production_config_in_research"] is CheckResult.NOT_TESTED
    assert report.checks["research_config_in_production"] is CheckResult.NOT_TESTED
    assert report.checks["unsafe_restart"] is CheckResult.NOT_TESTED
    assert report.checks["restart_loop"] is CheckResult.NOT_TESTED
    assert report.checks["health_false_positive"] is CheckResult.NOT_TESTED
    assert report.checks["readiness_false_positive"] is CheckResult.NOT_TESTED
    assert report.checks["silent_recovery"] is CheckResult.NOT_TESTED
    assert report.checks["silent_data_loss"] is CheckResult.NOT_TESTED
    assert report.checks["operational_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["safety_halt_failure"] is CheckResult.NOT_TESTED
    assert report.checks["certification_evidence_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["certification_snapshot_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["certification_model_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["certification_config_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["certification_hash_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["independent_validation_missing"] is CheckResult.NOT_TESTED
    assert report.checks["safety_gate_failure"] is CheckResult.NOT_TESTED
    assert report.checks["reconciliation_failure"] is CheckResult.NOT_TESTED
    assert report.checks["paper_shadow_gap"] is CheckResult.NOT_TESTED
    assert report.checks["revoked_certification"] is CheckResult.NOT_TESTED
    assert report.checks["waiver_expired"] is CheckResult.NOT_TESTED
    assert report.checks["waiver_scope_violation"] is CheckResult.NOT_TESTED
    assert report.checks["release_manifest_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["separation_of_duties_violation"] is CheckResult.NOT_TESTED
    assert report.checks["ai_authorization_override"] is CheckResult.NOT_TESTED
    assert report.checks["capital_limit_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["release_policy_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["human_approval_missing"] is CheckResult.NOT_TESTED
    assert report.checks["expired_certification"] is CheckResult.NOT_TESTED
    assert report.checks["critical_not_tested"] is CheckResult.NOT_TESTED
    assert report.checks["broker_identity_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["broker_snapshot_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["broker_payload_hash_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["duplicate_external_event"] is CheckResult.NOT_TESTED
    assert report.checks["external_event_collision"] is CheckResult.NOT_TESTED
    assert report.checks["unknown_broker_order"] is CheckResult.NOT_TESTED
    assert report.checks["orphan_broker_fill"] is CheckResult.NOT_TESTED
    assert report.checks["missing_broker_fill"] is CheckResult.NOT_TESTED
    assert report.checks["order_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["position_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["cash_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["margin_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["instrument_mapping_ambiguity"] is CheckResult.NOT_TESTED
    assert report.checks["instrument_mapping_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["timestamp_integrity_failure"] is CheckResult.NOT_TESTED
    assert report.checks["event_ordering_failure"] is CheckResult.NOT_TESTED
    assert report.checks["stale_broker_state"] is CheckResult.NOT_TESTED
    assert report.checks["credential_exposure"] is CheckResult.NOT_TESTED
    assert report.checks["broker_write_attempt"] is CheckResult.NOT_TESTED
    assert report.checks["live_mode_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["safety_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["future_market_observation"] is CheckResult.NOT_TESTED
    assert report.checks["future_state_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["future_volume"] is CheckResult.NOT_TESTED
    assert report.checks["future_quote"] is CheckResult.NOT_TESTED
    assert report.checks["future_reference_data"] is CheckResult.NOT_TESTED
    assert report.checks["timestamp_order_violation"] is CheckResult.NOT_TESTED
    assert report.checks["receive_time_violation"] is CheckResult.NOT_TESTED
    assert report.checks["sequence_gap_hidden"] is CheckResult.NOT_TESTED
    assert report.checks["stale_data_used"] is CheckResult.NOT_TESTED
    assert report.checks["invalid_data_used"] is CheckResult.NOT_TESTED
    assert report.checks["missing_data_filled"] is CheckResult.NOT_TESTED
    assert report.checks["clock_drift"] is CheckResult.NOT_TESTED
    assert report.checks["session_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["security_identity_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["realtime_snapshot_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["realtime_replay_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["future_realtime_feature"] is CheckResult.NOT_TESTED
    assert report.checks["future_realtime_model"] is CheckResult.NOT_TESTED
    assert report.checks["future_realtime_regime"] is CheckResult.NOT_TESTED
    assert report.checks["future_adaptive_update"] is CheckResult.NOT_TESTED
    assert report.checks["release_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["uncertified_model_use"] is CheckResult.NOT_TESTED
    assert report.checks["expired_release_use"] is CheckResult.NOT_TESTED
    assert report.checks["decision_state_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["rt_snapshot_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["stale_state_decision"] is CheckResult.NOT_TESTED
    assert report.checks["missing_critical_input"] is CheckResult.NOT_TESTED
    assert report.checks["capital_constraint_bypass"] is CheckResult.NOT_TESTED
    assert report.checks["decision_replay_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["ai_authority_violation"] is CheckResult.NOT_TESTED
    assert report.checks["future_replay_input"] is CheckResult.NOT_TESTED
    assert report.checks["future_shadow_state"] is CheckResult.NOT_TESTED
    assert report.checks["replay_snapshot_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["replay_state_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["replay_nondeterminism"] is CheckResult.NOT_TESTED
    assert report.checks["event_order_violation"] is CheckResult.NOT_TESTED
    assert report.checks["event_deletion"] is CheckResult.NOT_TESTED
    assert report.checks["checkpoint_mutation"] is CheckResult.NOT_TESTED
    assert report.checks["counterfactual_observation_confusion"] is CheckResult.NOT_TESTED
    assert report.checks["simulated_fill_as_broker_fill"] is CheckResult.NOT_TESTED
    assert report.checks["hidden_reconciliation_break"] is CheckResult.NOT_TESTED
    assert report.checks["recovery_state_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["release_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["strategy_state_mismatch"] is CheckResult.NOT_TESTED
    assert report.checks["shadow_routing_attempt"] is CheckResult.NOT_TESTED


def test_live_trading_flag_fails_integrity() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    report = evaluate_integrity(
        bars=[_bar(day)],
        states=[],
        as_of_times=[day],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=True,
        n_experiments_in_family=1,
        used_ml=False,
    )
    assert report.checks["live_trading_disabled"] is CheckResult.FAIL
    assert report.failed()


def test_test_used_for_selection_fails() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    report = evaluate_integrity(
        bars=[_bar(day)],
        states=[],
        as_of_times=[day],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
        test_used_for_selection=True,
    )
    assert report.checks["test_set_sacred"] is CheckResult.FAIL
    assert report.failed()
