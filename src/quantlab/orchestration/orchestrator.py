"""Thin orchestrator façade. Implementation lives in runner.py."""

from quantlab.orchestration.experiment import (
    run_named_orchestration_experiment,
    run_orchestration_experiment,
)
from quantlab.orchestration.planner import plan_experiment, preregister

__all__ = [
    "plan_experiment",
    "preregister",
    "run_named_orchestration_experiment",
    "run_orchestration_experiment",
]
