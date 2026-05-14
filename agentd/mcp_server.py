"""MCP server exposing firecrawl and browser-use tools to the deepagents TUI."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load stored credentials into environment before importing tools
try:
    from deepagents_cli.auth_store import load_credentials as _load_da_creds
    _env_map = {
        "kimi": "MOONSHOT_API_KEY",
        "xiomimimo": "XIOMIMIMO_API_KEY",
        "ollama": "OLLAMA_API_KEY",
        "langsmith": "LANGSMITH_API_KEY",
        "firecrawl": "FIRECRAWL_API_KEY",
    }
    for provider, key in (_load_da_creds() or {}).items():
        env_var = _env_map.get(provider)
        if env_var and key and not os.environ.get(env_var):
            os.environ[env_var] = key
except Exception:
    pass

from mcp.server.fastmcp import FastMCP
from agentd.browser_tools import BrowserToolkit

mcp = FastMCP("agentd-browser-tools")


@mcp.tool()
def firecrawl_scrape(url: str) -> str:
    """Scrape a URL and return the full page content as markdown.
    Use this to read any web page: documentation, articles, product pages, etc."""
    toolkit = BrowserToolkit()
    return toolkit.extract_with_firecrawl(url) or f"No content at {url}"


@mcp.tool()
def firecrawl_search(query: str, limit: int = 5) -> str:
    """Search the web and return results with titles, URLs, and descriptions.
    Use this when you need to find information that may be on the internet."""
    toolkit = BrowserToolkit()
    return toolkit.search_with_firecrawl(query, limit)


@mcp.tool()
async def browser_run(task: str) -> str:
    """Execute a browser automation task using a real Chrome browser.
    Use this for tasks requiring actual browser interaction: logging into sites,
    filling forms, clicking buttons, navigating complex web apps, or anything
    that requires JavaScript execution or authentication."""
    toolkit = BrowserToolkit()
    result = await toolkit.browser_task(task)
    return result or f"Browser task completed: {task}"


if __name__ == "__main__":
    mcp.run()
