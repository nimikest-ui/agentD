#!/usr/bin/env python3
"""
Browser Tools Integration for AgentD
Combines Browser-Use and Firecrawl for comprehensive web research
"""

from typing import Optional, Dict, Any
import json
import os

import importlib.util
BROWSER_USE_AVAILABLE = importlib.util.find_spec("browser_use") is not None


def _make_browser_llm():
    """Create a browser-use chat model based on the current TUI model config.

    browser-use's ``Agent`` requires a ``browser_use.llm.BaseChatModel`` (it reads
    ``llm.provider`` internally) — NOT a LangChain chat model. Passing a LangChain
    ``ChatOpenAI`` here is what raised:
        AttributeError: 'ChatOpenAI' object has no attribute 'provider'
    so every browser_run task failed. Use browser-use's own LLM wrappers instead.
    """
    from agentd.config import load_deepagents_config
    config = load_deepagents_config()
    provider_spec = config.get("models", {}).get("recent", "agentd-cli:sonnet")

    provider, _, model = provider_spec.partition(":")
    if not model:
        model = provider
        provider = "agentd-cli"

    if provider == "agentd-cli":
        from browser_use.llm import ChatAnthropic
        return ChatAnthropic(model="claude-haiku-4-5-20251001")

    providers = config.get("models", {}).get("providers", {})
    prov_cfg = providers.get(provider, {})
    api_key_env = prov_cfg.get("api_key_env", "")
    api_key = os.environ.get(api_key_env, "placeholder")
    base_url = prov_cfg.get("base_url")

    _hardcoded_base_urls = {
        "kimi": "https://api.moonshot.cn/v1",
        "xiomimimo": "https://api.xiaoai.plus/v1",
        "ollama": "https://ollama.com/v1",
    }
    if not base_url:
        base_url = _hardcoded_base_urls.get(provider)

    from browser_use.llm import ChatOpenAI
    return ChatOpenAI(model=model, base_url=base_url, api_key=api_key)


try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False


class BrowserToolkit:
    """Unified browser tools for AgentD"""

    def __init__(self, model: str = "haiku"):
        self.model = model
        self.browser_available = BROWSER_USE_AVAILABLE
        self.firecrawl_available = FIRECRAWL_AVAILABLE
        self.firecrawl = None

        if FIRECRAWL_AVAILABLE:
            try:
                self.firecrawl = FirecrawlApp(api_key="dummy")
            except:
                self.firecrawl = None

    def get_status(self) -> Dict[str, Any]:
        """Get status of available browser tools"""
        return {
            "model": self.model,
            "browser_use": self.browser_available,
            "firecrawl": self.firecrawl_available and self.firecrawl is not None,
            "features": {
                "web_scraping": self.browser_available or (self.firecrawl is not None),
                "form_filling": self.browser_available,
                "authentication": self.browser_available,
                "google_login": self.browser_available,
                "data_extraction": self.firecrawl is not None,
                "search": self.browser_available,
            }
        }

    async def search_and_extract(self, query: str) -> Dict[str, Any]:
        """Search and extract data (requires configuration)"""
        if not self.browser_available and not self.firecrawl:
            return {
                "error": "No browser tools configured",
                "browser_use": self.browser_available,
                "firecrawl": self.firecrawl is not None,
                "message": "Install browser-use and/or firecrawl-py to enable web research"
            }

        return {
            "query": query,
            "browser_use": self.browser_available,
            "firecrawl": self.firecrawl is not None,
            "status": "ready",
        }

    def extract_with_firecrawl(self, url: str) -> Optional[str]:
        """Extract markdown from URL using Firecrawl API."""
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if not api_key:
            return "Error: FIRECRAWL_API_KEY not set. Run '/auth' in TUI or set the env var."
        try:
            from firecrawl import FirecrawlApp
            app = FirecrawlApp(api_key=api_key)
            doc = app.scrape(url, formats=["markdown"])
            return doc.markdown or f"No markdown content at {url}"
        except Exception as e:
            return f"Firecrawl error scraping {url}: {e}"

    def search_with_firecrawl(self, query: str, limit: int = 5) -> str:
        """Search the web using Firecrawl and return results as markdown."""
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if not api_key:
            return "Error: FIRECRAWL_API_KEY not set. Run '/auth' in TUI or set the env var."
        try:
            from firecrawl import FirecrawlApp
            app = FirecrawlApp(api_key=api_key)
            results = app.search(query, limit=limit)
            lines = [f"# Search results for: {query}\n"]
            for r in results.results:
                lines.append(f"## [{r.title}]({r.url})")
                if r.description:
                    lines.append(r.description)
                lines.append("")
            return "\n".join(lines)
        except Exception as e:
            return f"Firecrawl search error for '{query}': {e}"

    async def browser_task(self, instruction: str) -> Optional[str]:
        """Execute task using Browser-Use with the currently configured TUI model."""
        if not self.browser_available:
            return (
                "Error: browser_use not available. "
                "Run: /root/agentD/venv/bin/pip install browser-use "
                "&& /root/agentD/venv/bin/playwright install chromium"
            )
        try:
            from browser_use import Agent as BrowserAgent
            llm = _make_browser_llm()
            agent = BrowserAgent(task=instruction, llm=llm)
            history = await agent.run()
            if hasattr(history, "final_result"):
                return str(history.final_result())
            return str(history)
        except Exception as e:
            return f"Browser task error: {type(e).__name__}: {e}"


# Convenience functions for AgentD
def get_browser_status() -> Dict[str, Any]:
    """Quick status check"""
    toolkit = BrowserToolkit()
    return toolkit.get_status()


def install_instructions() -> str:
    """Get installation instructions"""
    return """
╔══════════════════════════════════════════════════════════════════╗
║     AgentD Browser Tools - Installation Instructions             ║
╚══════════════════════════════════════════════════════════════════╝

✅ Browser-Use (Already Installed)
   • Full browser automation with vision
   • Form filling, authentication, multi-step workflows
   • JavaScript rendering, network interception
   • Chrome profile reuse for Google login

✅ Firecrawl (Already Installed)
   • Fast, LLM-optimized data extraction
   • Handles JavaScript-rendered content
   • Returns structured JSON/Markdown
   • Perfect for bulk data extraction

🔑 Optional: Configure Firecrawl API Key
   1. Get API key from https://firecrawl.dev
   2. Set environment variable:
      export FIRECRAWL_API_KEY="your-api-key"

🚀 Usage:
   from agentd.browser_tools import get_browser_status
   print(get_browser_status())

📚 Documentation:
   • Browser-Use: https://github.com/browser-use/browser-use
   • Firecrawl: https://firecrawl.dev
   • AgentD: /root/agentD/README.md
"""


if __name__ == "__main__":
    print(install_instructions())
    toolkit = BrowserToolkit()
    print("\n✅ Browser Tools Status:")
    print(json.dumps(toolkit.get_status(), indent=2))
