class AgentError(RuntimeError):
    """A safe error code; never attach credentials or raw provider responses."""


class AgentPermissionError(AgentError):
    pass


class AgentContextError(AgentError):
    pass


class AgentProviderError(AgentError):
    pass
