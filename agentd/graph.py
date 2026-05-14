"""AgentD StateGraph definition with checkpointing and memory store support."""

from __future__ import annotations

from typing import Callable, Optional

from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore


class AgentState(MessagesState):
    """Graph state: LangChain message history + thread-scoped memory facts."""
    _thread_memories: list[str]


def _make_llm_node(model_name: str) -> Callable[[AgentState], dict[str, list]]:
    """Return the single LLM node callable for the graph.

    Uses the proper model factory to instantiate the correct model class
    based on the model name (Kimi, Ollama, Copilot, Claude, etc).
    """
    import json
    import logging
    from agentd.core import Agent
    from agentd.memory import get_memories_prompt
    from langchain_core.messages import SystemMessage

    logger = logging.getLogger("agentd.graph")

    # Use the Agent factory to create the correct model type
    try:
        logger.info(json.dumps({"event": "_make_llm_node.create_model", "model_name": model_name}))
        model = Agent._create_model(model_name)
        logger.info(json.dumps({"event": "_make_llm_node.model_created", "model_name": model_name, "model_type": type(model).__name__}))
    except Exception as e:
        logger.error(json.dumps({"event": "_make_llm_node.create_model_failed", "model_name": model_name, "error": str(e), "error_type": type(e).__name__}))
        raise RuntimeError(
            f"Failed to initialize model '{model_name}': {type(e).__name__}: {e}. "
            f"Check that the model name is valid and required credentials are set."
        )

    def llm_node(state: AgentState) -> dict[str, list]:
        try:
            thread_memories = state.get("_thread_memories", [])
            messages = list(state["messages"])

            logger.info(json.dumps({"event": "llm_node.invoke", "model_name": model_name, "message_count": len(messages)}))

            memories_prompt = get_memories_prompt(thread_memories=thread_memories)
            if memories_prompt:
                if not messages or not isinstance(messages[0], SystemMessage):
                    messages = [SystemMessage(content=memories_prompt)] + messages
                else:
                    messages[0] = SystemMessage(
                        content=f"{memories_prompt}\n\n{messages[0].content}"
                    )

            response = model.invoke(messages)
            logger.info(json.dumps({"event": "llm_node.success", "model_name": model_name}))
            return {"messages": [response]}
        except RuntimeError as e:
            # Re-raise with better context for credential/API errors
            error_msg = str(e)
            logger.error(json.dumps({"event": "llm_node.runtime_error", "model_name": model_name, "error": error_msg}))
            if "API_KEY" in error_msg or "not found" in error_msg:
                raise RuntimeError(
                    f"Authentication error with {model_name}: {error_msg}\n"
                    f"Run '/auth' in TUI to set up credentials."
                )
            elif "Cannot connect" in error_msg or "timed out" in error_msg:
                raise RuntimeError(
                    f"Connection error with {model_name}: {error_msg}\n"
                    f"Check your network connection and that the service is available."
                )
            else:
                raise RuntimeError(
                    f"Error calling {model_name}: {error_msg}"
                )
        except Exception as e:
            logger.error(json.dumps({"event": "llm_node.exception", "model_name": model_name, "error_type": type(e).__name__, "error": str(e)}))
            raise RuntimeError(
                f"Unexpected error with {model_name}: {type(e).__name__}: {e}"
            )

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
