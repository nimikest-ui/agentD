"""AgentD StateGraph definition with checkpointing and memory store support."""

from __future__ import annotations

from typing import Optional

from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore


class AgentState(MessagesState):
    """Graph state: LangChain message history + thread-scoped memory facts."""
    _thread_memories: list[str]


def _make_llm_node(model_name: str):
    """Return the single LLM node callable for the graph."""
    from agentd.models import AgentDModel
    from agentd.memory import get_memories_prompt
    from langchain_core.messages import SystemMessage

    model = AgentDModel(model=model_name)

    def llm_node(state: AgentState) -> dict:
        thread_memories = state.get("_thread_memories", [])
        messages = list(state["messages"])

        memories_prompt = get_memories_prompt(thread_memories=thread_memories)
        if memories_prompt:
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=memories_prompt)] + messages
            else:
                messages[0] = SystemMessage(
                    content=f"{memories_prompt}\n\n{messages[0].content}"
                )

        response = model.invoke(messages)
        return {"messages": [response]}

    return llm_node


def build_graph(
    model_name: str = "sonnet",
    checkpointer: Optional[BaseCheckpointSaver] = None,
    store: Optional[BaseStore] = None,
):
    """Build and compile the AgentD StateGraph.

    Args:
        model_name: Model identifier passed to AgentDModel.
        checkpointer: Checkpoint saver (SqliteSaver in prod, MemorySaver in tests).
        store: Cross-thread InMemoryStore.

    Returns:
        CompiledStateGraph ready for invoke/stream/get_state/update_state.
    """
    graph = StateGraph(AgentState)
    graph.add_node("llm", _make_llm_node(model_name))
    graph.set_entry_point("llm")
    graph.set_finish_point("llm")
    return graph.compile(checkpointer=checkpointer, store=store)
