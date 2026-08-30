"""Seed microstructure models. Uncalibrated impact is explicit."""

from __future__ import annotations

from quantlab.backtest.costs import CostSchedule
from quantlab.execution_research.definition import (
    FillKind,
    ImpactKind,
    LatencyKind,
    LiquidityKind,
    MarketMicrostructureDefinition,
    SlippageKind,
    SpreadKind,
)


def seed_execution_models() -> list[MarketMicrostructureDefinition]:
    base_cost = CostSchedule()
    zero = CostSchedule(
        commission_bps=0.0,
        provenance="unrealistic_zero_cost_research_mode",
    )
    return [
        MarketMicrostructureDefinition(
            definition_id="exec_base",
            version="1",
            name="Base configured friction",
            spread_bps=5.0,
            slippage_bps=2.0,
            max_participation=0.20,
            cost=base_cost,
            notes="Configured research default. Not calibrated NSE microstructure.",
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_conservative",
            version="1",
            name="Conservative friction",
            spread_bps=10.0,
            slippage_bps=5.0,
            impact_model=ImpactKind.SQUARE_ROOT,
            impact_k=0.2,
            latency_model=LatencyKind.FIXED,
            latency_sessions=1,
            max_participation=0.10,
            parameter_provenance="uncalibrated_conservative_stress",
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_high_slippage",
            version="1",
            name="High slippage",
            slippage_bps=15.0,
            spread_bps=5.0,
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_wide_spread",
            version="1",
            name="Wide spread",
            spread_bps=25.0,
            slippage_model=SlippageKind.SPREAD_FRACTION,
            spread_fraction=0.5,
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_high_impact",
            version="1",
            name="Uncalibrated square-root impact",
            impact_model=ImpactKind.SQUARE_ROOT,
            impact_k=0.5,
            parameter_provenance="uncalibrated",
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_low_liquidity",
            version="1",
            name="Low participation cap",
            max_participation=0.05,
            fill_model=FillKind.PARTICIPATION_CAPPED,
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_high_latency",
            version="1",
            name="Two-session latency",
            latency_model=LatencyKind.FIXED,
            latency_sessions=2,
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_partial",
            version="1",
            name="Ratio-capped partial fills",
            fill_model=FillKind.RATIO_CAPPED,
            fill_ratio_cap=0.5,
            max_participation=0.20,
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_stressed",
            version="1",
            name="Stressed microstructure",
            spread_model=SpreadKind.VOL_SCALED,
            spread_bps=15.0,
            slippage_bps=10.0,
            impact_model=ImpactKind.PARTICIPATION,
            impact_k=0.4,
            latency_sessions=1,
            latency_model=LatencyKind.FIXED,
            max_participation=0.05,
            parameter_provenance="uncalibrated_stress",
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_zero_cost",
            version="1",
            name="Unrealistic zero-cost mode",
            spread_bps=0.0,
            slippage_model=SlippageKind.NONE,
            slippage_bps=0.0,
            impact_model=ImpactKind.NONE,
            cost=zero,
            fill_model=FillKind.FULL,
            max_participation=1.0,
            liquidity_model=LiquidityKind.BAR_VOLUME,
            notes="Zero-cost is not tradability evidence. Integrity FAIL.",
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_unknown_adv",
            version="1",
            name="Unknown liquidity",
            liquidity_model=LiquidityKind.UNKNOWN,
            notes="Capacity remains NOT_TESTED without volume.",
        ),
        MarketMicrostructureDefinition(
            definition_id="exec_bid_ask",
            version="1",
            name="Historical bid/ask (unavailable)",
            spread_model=SpreadKind.HISTORICAL_BID_ASK,
            notes="No PIT bid/ask dump is bundled. Spread status NOT_TESTED.",
        ),
    ]
