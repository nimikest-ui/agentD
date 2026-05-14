"""
AgentD - Production-grade LLM agent framework.

Full session logging, persistent memory, token tracking, and Claude CLI integration.
"""

__version__ = "0.1.0"
__author__ = "AgentD Contributors"

from agentd.core import Agent
from agentd.models import AgentDModel
from agentd.persistence import make_checkpointer, make_store
from agentd.graph import build_graph, AgentState

from agentd.model_registry import (
    get_models,
    get_model,
    get_models_by_provider,
    list_all_models,
    get_providers,
    register_model,
)

from agentd.auth_store import (
    get_credential,
    set_credential,
    delete_credential,
    load_credentials,
    save_credentials,
    get_supported_keys,
)

__all__ = [
    "Agent",
    "AgentDModel",
    "get_models",
    "get_model",
    "get_models_by_provider",
    "list_all_models",
    "get_providers",
    "register_model",
    "get_credential",
    "set_credential",
    "delete_credential",
    "load_credentials",
    "save_credentials",
    "get_supported_keys",
    "__version__",
    "make_checkpointer",
    "make_store",
    "build_graph",
    "AgentState",
]
