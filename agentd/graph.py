"""AgentD StateGraph definition with checkpointing and memory store support."""

from __future__ import annotations

from typing import Callable, Optional

from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore


class AgentState(MessagesState):
    """Graph state: LangChain message history + thread-scoped memory facts."""
    _thread_memories: list[str]
    # Claude Code session id for this thread. Set only on the Claude (agentd-cli)
    # path so subsequent turns `--resume` instead of re-sending the full history.
    _claude_session_id: str


def _make_llm_node(model_name: str) -> Callable[[AgentState], dict]:
    """Return the single LLM node callable for the graph.

    Uses the proper model factory to instantiate the correct model class
    based on the model name (Kimi, Ollama, Copilot, Claude, etc).
    """
    from agentd.core import Agent
    from agentd.memory import get_memories_prompt
    from langchain_core.messages import HumanMessage, SystemMessage

    # Use the Agent factory to create the correct model type
    try:
        model = Agent._create_model(model_name)
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize model '{model_name}': {type(e).__name__}: {e}. "
            f"Check that the model name is valid and required credentials are set."
        )

    # Claude (agentd-cli) is the only provider that supports `--resume` session
    # reuse. Every other provider (Kimi/Xiaomi/Ollama/Copilot) keeps the original
    # ainvoke(messages) path untouched.
    is_claude = getattr(model, "_llm_type", "") == "agentd-cli"

    async def llm_node(state: AgentState) -> dict:
        try:
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

            session_id = state.get("_claude_session_id") if is_claude else None

            if is_claude and session_id:
                # Resume the existing Claude Code session: send only the latest
                # human turn — prior context is retained server-side, so we avoid
                # re-sending (and re-paying for) the whole conversation.
                last_human = next(
                    (m for m in reversed(messages) if isinstance(m, HumanMessage)),
                    None,
                )
                turn = [last_human] if last_human is not None else messages
                response = await model.ainvoke(turn, resume_session_id=session_id)
            else:
                response = await model.ainvoke(messages)

            out: dict = {"messages": [response]}
            if is_claude:
                new_sid = (getattr(response, "response_metadata", None) or {}).get("session_id")
                if new_sid:
                    out["_claude_session_id"] = new_sid
            return out
        except RuntimeError as e:
            # Re-raise with better context for credential/API errors
            error_msg = str(e)
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
            raise RuntimeError(
                f"Unexpected error with {model_name}: {type(e).__name__}: {e}"
            )

    return llm_node


def build_graph(
    model_name: str = "haiku",
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
