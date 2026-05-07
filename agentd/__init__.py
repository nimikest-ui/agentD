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
    "__version__",
]
