"""AgentD Core — Agent class with LangGraph persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, Optional

from langchain_core.runnables import RunnableConfig

from agentd.models import AgentDModel, AGENTD_CLI_PROVIDER
from agentd.graph import build_graph
from agentd.persistence import make_store

__all__ = ["Agent", "AgentDModel", "AGENTD_CLI_PROVIDER"]


def _config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


class Agent:
    """AgentD Agent — LangGraph graph with SqliteSaver checkpointing."""

    def __init__(
        self,
        model: str = "sonnet",
        db_path: str | Path | None = None,
        checkpointer=None,
        store=None,
        **kwargs,
    ):
        self.model_name = model
        self.agent_model = AgentDModel(model=model)
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
            except Exception:
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

    def get_state(self, thread_id: str):
        """Return the current StateSnapshot for a thread."""
        return self.graph.get_state(_config(thread_id))

    def get_history(self, thread_id: str, limit: Optional[int] = None) -> Iterator:
        """Yield checkpoint snapshots for a thread, newest first."""
        yield from self.graph.get_state_history(_config(thread_id), limit=limit)

    def update_state(self, thread_id: str, values: dict[str, Any]) -> RunnableConfig:
        """Write values directly into a thread's checkpoint state."""
        return self.graph.update_state(_config(thread_id), values)

    async def aupdate_state(self, config: RunnableConfig, values: dict) -> RunnableConfig:
        """Async update_state for memory.py stubs."""
        return await self.graph.aupdate_state(config, values)

    async def aget_state(self, config: RunnableConfig):
        """Async get_state for memory.py stubs."""
        return await self.graph.aget_state(config)
