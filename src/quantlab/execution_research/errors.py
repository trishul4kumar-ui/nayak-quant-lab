"""Re-export execution-research errors. Package must not own a second error hierarchy."""

from quantlab.core.errors import ExecutionResearchError

__all__ = ["ExecutionResearchError"]
