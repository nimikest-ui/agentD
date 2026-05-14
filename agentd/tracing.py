"""
LangSmith Tracing Configuration for AgentD.

Provides traceable decorators and Anthropic SDK client wrapper for automatic
tracing of LLM calls, tool usage, and application workflows.
"""

import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from langsmith import traceable, Client
import anthropic
from langsmith.wrappers import wrap_anthropic


def configure_langsmith(
    api_key: Optional[str] = None,
    project_name: str = "default",
    workspace_id: Optional[str] = None,
) -> None:
    """Configure LangSmith environment variables.

    Args:
        api_key: LangSmith API key (defaults to LANGSMITH_API_KEY env var)
        project_name: Project name for traces (defaults to "default")
        workspace_id: Workspace ID (optional, for multi-workspace accounts)
    """
    # Load .env file, searching from current working directory
    load_dotenv(
        dotenv_path=str(Path.cwd() / ".env"),
        verbose=False,
    )

    # If no API key provided, try to load from auth store
    if not api_key:
        try:
            from agentd.auth_store import get_credential
            api_key = get_credential("LANGSMITH_API_KEY")
        except Exception:
            pass

    if api_key:
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_PROJECT"] = project_name

        if workspace_id:
            os.environ["LANGSMITH_WORKSPACE_ID"] = workspace_id


def get_langsmith_client() -> Client:
    """Get LangSmith client instance."""
    return Client()


def create_anthropic_client(
    api_key: Optional[str] = None,
    enable_tracing: bool = True,
) -> anthropic.Anthropic:
    """Create Anthropic client with optional LangSmith tracing.

    Args:
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        enable_tracing: Enable LangSmith tracing (default: True)

    Returns:
        Anthropic client, optionally wrapped for LangSmith tracing
    """
    client = anthropic.Anthropic(api_key=api_key)

    if enable_tracing and os.environ.get("LANGSMITH_TRACING") == "true":
        client = wrap_anthropic(client)

    return client


def trace_run(
    name: str,
    run_type: str = "chain",
    **trace_kwargs,
) -> Callable:
    """Decorator to trace function execution with LangSmith.

    Args:
        name: Name of the run (appears in LangSmith UI)
        run_type: Type of run - "chain", "tool", "agent", "llm", "retriever"
        **trace_kwargs: Additional kwargs passed to @traceable

    Example:
        @trace_run(name="My Workflow", run_type="chain")
        def my_workflow(query: str):
            return "result"
    """
    def decorator(func: Callable) -> Callable:
        traced_func = traceable(
            name=name,
            run_type=run_type,
            **trace_kwargs,
        )(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return traced_func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "configure_langsmith",
    "get_langsmith_client",
    "create_anthropic_client",
    "trace_run",
    "traceable",
]
