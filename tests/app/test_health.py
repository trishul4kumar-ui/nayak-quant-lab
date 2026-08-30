from pathlib import Path

from quantlab.app.health import ComponentStatus, run_health_checks
from quantlab.app.mode import AppMode
from quantlab.app.paths import RuntimePaths
from quantlab.core.config import LiveSafetyGates, Settings


def test_broker_optional_in_research(tmp_path: Path) -> None:
    paths = RuntimePaths.discover(tmp_path)
    paths.ensure()
    report = run_health_checks(paths, Settings(), LiveSafetyGates(), AppMode.RESEARCH)
    broker = report.by_name("broker_gateway")
    assert broker is not None
    assert broker.required is False
    assert broker.status is ComponentStatus.OPTIONAL
    assert report.research_ready()
    factor = report.by_name("factor_engine")
    assert factor is not None
    assert factor.status is ComponentStatus.OK
    risk_model = report.by_name("research_risk_model")
    assert risk_model is not None
    assert risk_model.status is ComponentStatus.OK
    firewall = report.by_name("risk_engine")
    assert firewall is not None
    assert firewall.status is ComponentStatus.OK
    regime = report.by_name("regime_engine")
    assert regime is not None
    assert regime.status is ComponentStatus.OK
    adaptive = report.by_name("adaptive_engine")
    assert adaptive is not None
    assert adaptive.status is ComponentStatus.OK
    learning = report.by_name("learning_engine")
    assert learning is not None
    assert learning.status is ComponentStatus.OK
    ensemble = report.by_name("ensemble_engine")
    assert ensemble is not None
    assert ensemble.status is ComponentStatus.OK
    execution_research = report.by_name("execution_research_engine")
    assert execution_research is not None
    assert execution_research.status is ComponentStatus.OK
    orchestration = report.by_name("orchestration_engine")
    assert orchestration is not None
    assert orchestration.status is ComponentStatus.OK
    discovery = report.by_name("discovery_engine")
    assert discovery is not None
    assert discovery.status is ComponentStatus.OK
    knowledge = report.by_name("knowledge_engine")
    assert knowledge is not None
    assert knowledge.status is ComponentStatus.OK
    capital = report.by_name("capital_engine")
    assert capital is not None
    assert capital.status is ComponentStatus.OK
    paper = report.by_name("paper_oms_engine")
    assert paper is not None
    assert paper.status is ComponentStatus.OK
    monitoring = report.by_name("monitoring_engine")
    assert monitoring is not None
    assert monitoring.status is ComponentStatus.OK
    market_data = report.by_name("market_data_engine")
    assert market_data is not None
    assert market_data.status is ComponentStatus.OK
    tca = report.by_name("tca_engine")
    assert tca is not None
    assert tca.status is ComponentStatus.OK
    econometrics = report.by_name("econometrics_engine")
    assert econometrics is not None
    assert econometrics.status is ComponentStatus.OK
    certification = report.by_name("certification_engine")
    assert certification is not None
    assert certification.status is ComponentStatus.OK
    shadow = report.by_name("shadow_engine")
    assert shadow is not None
    assert shadow.status is ComponentStatus.OK
    safety = report.by_name("safety_engine")
    assert safety is not None
    assert safety.status is ComponentStatus.OK
    ops = report.by_name("ops_engine")
    assert ops is not None
    assert ops.status is ComponentStatus.OK
    release = report.by_name("release_engine")
    assert release is not None
    assert release.status is ComponentStatus.OK
    realtime_data = report.by_name("realtime_data_engine")
    assert realtime_data is not None
    assert realtime_data.status is ComponentStatus.OK
    realtime_decision = report.by_name("realtime_decision_engine")
    assert realtime_decision is not None
    assert realtime_decision.status is ComponentStatus.OK
    twin = report.by_name("digital_twin_engine")
    assert twin is not None
    assert twin.status is ComponentStatus.OK
