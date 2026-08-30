"""Re-export knowledge errors. Package must not own a second error hierarchy."""

from quantlab.core.errors import KnowledgeError

__all__ = ["KnowledgeError"]
