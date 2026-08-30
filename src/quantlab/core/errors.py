"""Typed failures. Trading paths fail closed."""


class QuantLabError(Exception):
    """Base error."""


class SafetyError(QuantLabError):
    """Live or broker path blocked by safety gates."""


class RiskRejectedError(QuantLabError):
    """Firewall rejected a proposed portfolio or order."""


class DataIntegrityError(QuantLabError):
    """Bar, timestamp, or dataset failed validation."""


class LookAheadError(QuantLabError):
    """Feature or label used information not available at as-of time."""


class InfeasiblePortfolio(QuantLabError):
    """Hard constraints cannot be satisfied; they were not relaxed."""


class OptimizationError(QuantLabError):
    """Optimizer failed. No silent fallback to another optimizer."""


class CovarianceError(QuantLabError):
    """Covariance is missing, singular, or not positive semidefinite."""


class AlignmentError(QuantLabError):
    """Alpha, universe, or risk arrays do not share decision_time / security_id."""


class FactorError(QuantLabError):
    """Factor is missing, leaked, misaligned, or not computable from PIT inputs."""


class RegimeError(QuantLabError):
    """Regime/state is leaked, smoothed for prediction, or not computable from PIT inputs."""


class AdaptiveError(QuantLabError):
    """Adaptive learner used future information or an invalid update order."""


class InfeasibleAdaptiveEnsemble(AdaptiveError):
    """Hard ensemble constraints cannot be satisfied; they were not relaxed."""


class ModelError(QuantLabError):
    """Statistical model used future information, a singular fit, or insufficient data."""


class EnsembleError(QuantLabError):
    """Ensemble used future information, incompatible components, or an invalid combination."""


class InfeasibleEnsemble(EnsembleError):
    """Hard ensemble constraints cannot be satisfied; they were not relaxed."""


class ExecutionResearchError(QuantLabError):
    """Execution simulation used future information, an invalid fill, or missing PIT inputs."""


class OrchestrationError(QuantLabError):
    """Research control-plane identity, freeze, lineage, or budget violation."""


class DiscoveryError(QuantLabError):
    """Invalid expression, type error, domain violation, or discovery-search leak."""


class KnowledgeError(QuantLabError):
    """Knowledge-graph identity, provenance, immutability, or claim-strength violation."""


class CapitalError(QuantLabError):
    """Capital-allocation identity, constraint, or decision-immutability violation."""


class InfeasibleCapitalAllocation(CapitalError):
    """Hard capital constraints cannot be satisfied; they were not relaxed."""

    def __init__(
        self,
        message: str,
        *,
        violated_constraints: list[str] | None = None,
        required_adjustment: str = "",
        current_candidate: dict[str, float] | None = None,
        feasibility_diagnostics: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.violated_constraints = violated_constraints or []
        self.required_adjustment = required_adjustment
        self.current_candidate = current_candidate or {}
        self.feasibility_diagnostics = feasibility_diagnostics or {}


class PaperOMSError(QuantLabError):
    """Paper OMS identity, lifecycle, accounting, or reconciliation violation."""


class OMSValidationError(PaperOMSError):
    """Paper order failed validation before simulated submission."""


class InvalidOrderTransition(PaperOMSError):
    """Lifecycle transition is not permitted."""


class DuplicateOrderError(PaperOMSError):
    """Idempotency key already produced a paper order."""


class InsufficientCashError(PaperOMSError):
    """Paper account cash cannot cover the requested buy."""


class InsufficientPositionError(PaperOMSError):
    """Paper account cannot sell more than it holds."""


class PaperSafetyError(SafetyError):
    """Paper OMS refused a live, broker, or credentialed path."""


class ReconciliationError(PaperOMSError):
    """Target, orders, fills, positions, or cash do not reconcile."""


class AccountingInvariantError(PaperOMSError):
    """Cash or position identity failed. This is FAIL, not a warning."""


class OrderPlanningError(PaperOMSError):
    """Target cannot be converted into a paper order plan without silent resize."""


class UnsupportedOrderTypeError(PaperOMSError):
    """Order type is not supported on the paper path."""


class MonitoringError(QuantLabError):
    """Portfolio monitoring, performance, or attribution identity violation."""


class PerformanceReconciliationError(MonitoringError):
    """P&L or attribution identity failed. This is FAIL, not a warning."""


class AttributionError(MonitoringError):
    """Attribution requested a causal split that is not available."""


class MarketDataError(DataIntegrityError):
    """Production market-data provenance, identity, or quality violation."""


class SecurityMasterError(MarketDataError):
    """Historical security identity or symbol mapping is missing or leaked."""


class CorporateActionError(MarketDataError):
    """Corporate-action timing, adjustment, or provenance is invalid."""


class SnapshotError(MarketDataError):
    """Research snapshot dependency hash does not match frozen inputs."""


class TCAError(QuantLabError):
    """Transaction-cost, calibration, capacity, or fragility identity violation."""


class CalibrationError(TCAError):
    """Execution-model calibration used future data or insufficient evidence."""


class CapacityError(TCAError):
    """Capacity was requested without liquidity evidence or a policy."""


class EconometricsError(QuantLabError):
    """Econometric identity, PIT window, or specification violation."""


class CausalResearchError(EconometricsError):
    """Causal claim requested without an explicit identification strategy."""


class CertificationError(QuantLabError):
    """Model-risk certification, validation, or state-machine violation."""


class IllegalCertificationTransition(CertificationError):
    """Certification state transition is not permitted."""


class ReproductionBreak(CertificationError):
    """Reproduced result hash does not match the frozen validation result."""


class WaiverError(CertificationError):
    """Waiver is missing authority, scope, or expiry."""


class ShadowError(QuantLabError):
    """Production paper/shadow identity, freshness, or safety violation."""


class InvalidShadowTransition(ShadowError):
    """Shadow mode or cycle transition is not permitted."""


class StaleDataError(ShadowError):
    """Market data exceeded the freshness policy."""


class LiveRouteAttempt(ShadowError):
    """A live broker route was requested on the shadow path."""


class CheckpointError(ShadowError):
    """Checkpoint hash mismatch or corrupt recovery state."""


class ShadowCertificationError(ShadowError):
    """Production paper/shadow refused to run without valid certification."""


class GatewayError(QuantLabError):
    """Live-trading safety gateway refused a request. Not a broker error."""


class InvalidSafetyTransition(GatewayError):
    """Safety state transition is not permitted."""


class AuthorizationError(GatewayError):
    """Execution authorization is missing, stale, mutated, or expired."""


class KillSwitchError(GatewayError):
    """A kill switch blocks the request. Kill switches never create orders."""


class ReleaseBlocked(GatewayError):
    """Live release is blocked. LIVE_TRADING remains false."""


class OpsError(QuantLabError):
    """Operational control-plane failure. Not a trading or broker error."""


class InvalidOpsTransition(OpsError):
    """Ops lifecycle transition is not permitted."""


class SecretExposureError(OpsError):
    """A secret value was requested in a leakable channel."""


class BackupError(OpsError):
    """Backup verification or restore validation failed."""


class ClockError(OpsError):
    """Clock rollback or future timestamp rejected."""


class ReleaseGateError(QuantLabError):
    """Live-trading certification/release gate refused a request."""


class InvalidReleaseTransition(ReleaseGateError):
    """Certification or promotion transition is not permitted."""


class CertificationBlocked(ReleaseGateError):
    """Certification cannot proceed. CERTIFIED is not live."""


class ReleaseWaiverError(ReleaseGateError):
    """Release waiver is expired, out of scope, or attempts to waive safety."""


class BrokerGatewayError(QuantLabError):
    """Broker gateway refused a request. Read-only; not a live route."""


class InvalidBrokerTransition(BrokerGatewayError):
    """Broker connection transition is not permitted."""


class BrokerWriteError(BrokerGatewayError):
    """Write/order path is disabled. BROKER_WRITE_ENABLED=false."""


class BrokerReconcileError(BrokerGatewayError):
    """Broker reconciliation mismatch. Differences are retained."""


class RealTimeDataError(QuantLabError):
    """Real-time market-data gateway refused a request. Observe-only."""


class InvalidFeedTransition(RealTimeDataError):
    """Feed connection transition is not permitted."""


class StaleObservationError(RealTimeDataError):
    """Stale or invalid observation cannot be treated as valid."""


class SequenceIntegrityError(RealTimeDataError):
    """Sequence gap, duplicate, or out-of-order observation."""


class RealTimeDecisionError(QuantLabError):
    """Real-time decision engine refused a request. Not an order."""


class InvalidDecisionTransition(RealTimeDecisionError):
    """Decision-cycle transition is not permitted."""


class DecisionBlocked(RealTimeDecisionError):
    """Decision abstained or blocked. TargetPortfolio is not an order."""


class UncertifiedReleaseError(RealTimeDecisionError):
    """Unknown, expired, or uncertified strategy release. ABSTAIN."""


class DigitalTwinError(QuantLabError):
    """Digital-twin / shadow replay refused a request. Not a broker."""


class InvalidTwinTransition(DigitalTwinError):
    """Twin lifecycle transition is not permitted."""


class ReplayMismatch(DigitalTwinError):
    """Replay hashes do not match the original run."""


class TwinRoutingError(DigitalTwinError):
    """Shadow/twin write path is disabled. No broker routing."""


class TwinCheckpointError(DigitalTwinError):
    """Twin checkpoint restore failed. Distinct from paper shadow checkpoints."""
