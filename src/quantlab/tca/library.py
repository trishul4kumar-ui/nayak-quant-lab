"""Seed TCA policy. Synthetic diagnostic."""

from quantlab.tca.models import CapacityPolicy


def default_policy() -> CapacityPolicy:
    return CapacityPolicy(
        policy_id="CAP-TCA-001",
        max_participation=0.10,
        max_cost_bps=50.0,
        min_net_edge=0.0,
    )
