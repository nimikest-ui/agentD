"""
AgentD - Production-grade LLM agent framework.

Full session logging, persistent memory, token tracking, and Claude CLI integration.
"""

__version__ = "0.1.0"
__author__ = "AgentD Contributors"

from agentd.core import Agent
from agentd.models import AgentDModel

__all__ = [
    "Agent",
    "AgentDModel",
    "__version__",
]
