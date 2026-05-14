"""AgentD Core — Agent class with LangGraph persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore

from agentd.models import (
    AgentDModel,
    CopilotModel,
    KimiModel,
    OllamaModel,
    XiaomiModel,
    AGENTD_CLI_PROVIDER,
    COPILOT_CLI_PROVIDER,
    KIMI_PROVIDER,
    OLLAMA_PROVIDER,
    XIOMIMIMO_PROVIDER,
)
from agentd.graph import build_graph
from agentd.persistence import make_store

__all__ = ["Agent", "AgentDModel", "KimiModel", "XiaomiModel", "AGENTD_CLI_PROVIDER", "KIMI_PROVIDER", "XIOMIMIMO_PROVIDER"]


def _config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def _detect_provider(model: str) -> str:
    """Detect provider from model name or return default."""
    import os
    from agentd.models import OLLAMA_COMMON_MODELS

    model_lower = model.lower()

    # Kimi/Moonshot models
    if any(x in model_lower for x in ["kimi", "moonshot"]):
        return KIMI_PROVIDER

    # Xiaomi MiMo models
    if any(x in model_lower for x in ["mimo", "xiaomi"]):
        return XIOMIMIMO_PROVIDER

    # Ollama models: colon-style tags (llama2:13b) or common model names
    if ":" in model and not any(x in model_lower for x in ["sonnet", "claude", "copilot"]):
        return OLLAMA_PROVIDER

    # Check if it's a known Ollama common model (e.g., llama2, mistral, phi)
    if model in OLLAMA_COMMON_MODELS:
        return OLLAMA_PROVIDER

    # Check environment variable
    env_provider = os.environ.get("AGENTD_PROVIDER", AGENTD_CLI_PROVIDER)
    return env_provider


class Agent:
    """AgentD Agent — LangGraph graph with SqliteSaver checkpointing."""

    @staticmethod
    def _create_model(model: str, provider: Optional[str] = None, **kwargs: Any):
        """Create the appropriate model instance based on provider.

        Handles both plain model names (e.g., "kimi-k2.6") and
        prefixed names (e.g., "kimi:kimi-k2.6") by splitting on ':'.
        """
        # Strip provider prefix if present (e.g., "kimi:kimi-k2.6" -> "kimi-k2.6")
        model_name = model.split(":")[-1] if ":" in model else model

        if provider is None:
            provider = _detect_provider(model)

        if provider == COPILOT_CLI_PROVIDER:
            return CopilotModel(model=model_name, **kwargs)
        elif provider == KIMI_PROVIDER:
            return KimiModel(model=model_name, **kwargs)
        elif provider == XIOMIMIMO_PROVIDER:
            return XiaomiModel(model=model_name, **kwargs)
        elif provider == OLLAMA_PROVIDER:
            return OllamaModel(model=model_name, **kwargs)
        else:
            return AgentDModel(model=model_name, **kwargs)

    def __init__(
        self,
        model: str = "sonnet",
        provider: Optional[str] = None,
        db_path: str | Path | None = None,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        store: Optional[BaseStore] = None,
        **kwargs,
    ):
        # Initialize logging on first Agent creation
        try:
            from agentd.logging_config import setup_logging
            setup_logging()
        except Exception:
            pass  # Logging setup failure shouldn't break the agent

        self.model_name = model
        self.agent_model = self._create_model(model, provider, **kwargs)
        self._store = store or make_store()
        self._owns_cm = False

        if checkpointer is not None:
            self._checkpointer = checkpointer
        else:
            from agentd.persistence import make_checkpointer, DEFAULT_DB_PATH
            self._cm = make_checkpointer(db_path or DEFAULT_DB_PATH)
            self._checkpointer = self._cm.__enter__()
            self._owns_cm = True

        self.graph = build_graph(
            model_name=model,
            checkpointer=self._checkpointer,
            store=self._store,
        )

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._owns_cm:
            try:
                self._cm.__exit__(None, None, None)
            except (OSError, RuntimeError, AttributeError):
                pass
            self._owns_cm = False

    def __del__(self):
        self.close()

    def __repr__(self):
        return f"Agent(model={self.model_name})"

    def invoke(self, message: str, thread_id: str = "default") -> dict[str, Any]:
        """Send a message and return the final state dict."""
        from langchain_core.messages import HumanMessage
        return self.graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=_config(thread_id),
        )

    def stream(self, message: str, thread_id: str = "default") -> Iterator[dict]:
        """Stream graph state updates for a message."""
        from langchain_core.messages import HumanMessage
        yield from self.graph.stream(
            {"messages": [HumanMessage(content=message)]},
            config=_config(thread_id),
            stream_mode="updates",
        )

    def get_state(self, thread_id: str) -> Any:
        """Return the current StateSnapshot for a thread."""
        return self.graph.get_state(_config(thread_id))

    def get_history(self, thread_id: str, limit: Optional[int] = None) -> Iterator:
        """Yield checkpoint snapshots for a thread, newest first."""
        yield from self.graph.get_state_history(_config(thread_id), limit=limit)

    def update_state(self, thread_id: str, values: dict[str, Any]) -> RunnableConfig:
        """Write values directly into a thread's checkpoint state."""
        return self.graph.update_state(_config(thread_id), values)

    async def aupdate_state(self, config: RunnableConfig, values: dict[str, Any]) -> RunnableConfig:
        """Async update_state for memory.py stubs."""
        return await self.graph.aupdate_state(config, values)

    async def aget_state(self, config: RunnableConfig) -> Any:
        """Async get_state for memory.py stubs."""
        return await self.graph.aget_state(config)
