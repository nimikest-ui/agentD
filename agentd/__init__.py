"""
AgentD - Production-grade LLM agent framework.

Full session logging, persistent memory, token tracking, and Claude CLI integration.
"""

__version__ = "0.1.0"
__author__ = "AgentD Contributors"

from agentd.core import Agent
from agentd.models import AgentDModel
from agentd.browser_tools import BrowserToolkit, get_browser_status
from agentd.pentester_skill import PentesterSkill, handle_pentester_skill
from agentd.research_tools import (
    ResearchTools,
    get_research_tools,
    browse_url,
    search_web,
    scrape_content,
    process_markdown,
    extract_entities,
    structure_findings,
    analyze_patterns,
    assess_impact,
    identify_gaps,
    save_to_memory,
    create_graph_node,
    link_nodes,
    save_skill_insight,
)
from agentd.persistence import make_checkpointer, make_store
from agentd.graph import build_graph, AgentState

from agentd.tracing import (
    configure_langsmith,
    get_langsmith_client,
    create_anthropic_client,
    trace_run,
    traceable,
)

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
    "BrowserToolkit",
    "get_browser_status",
    "PentesterSkill",
    "handle_pentester_skill",
    "ResearchTools",
    "get_research_tools",
    "browse_url",
    "search_web",
    "scrape_content",
    "process_markdown",
    "extract_entities",
    "structure_findings",
    "analyze_patterns",
    "assess_impact",
    "identify_gaps",
    "save_to_memory",
    "create_graph_node",
    "link_nodes",
    "save_skill_insight",
    "configure_langsmith",
    "get_langsmith_client",
    "create_anthropic_client",
    "trace_run",
    "traceable",
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
