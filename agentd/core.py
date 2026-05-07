"""
AgentD Core - Main Agent class and utilities.
"""

from agentd.models import AgentDModel, AGENTD_CLI_PROVIDER

__all__ = [
    "Agent",
    "AgentDModel",
    "AGENTD_CLI_PROVIDER",
]


class Agent:
    """AgentD Agent - Wrapper for LangGraph agent with Claude CLI backend."""

    def __init__(self, model: str = "sonnet", **kwargs):
        """Initialize an AgentD agent.

        Args:
            model: Model name (default: sonnet)
            **kwargs: Additional arguments
        """
        self.model_name = model
        self.agent_model = AgentDModel(model=model)

    def __repr__(self):
        return f"Agent(model={self.model_name})"
