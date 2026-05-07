"""Persistent memory system backed by LangGraph checkpoint and local JSON fallback.

Stores conversation facts in both:
1. LangGraph graph state (per-thread, thread-scoped memories)
2. Local JSON file (user-scoped, shared across all threads)

Memories are auto-loaded into system prompts for context continuity.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

MEMORY_FILE = Path.home() / ".agentd_memories.json"
"""Global user memories file (shared across all threads)."""


def load_memories() -> list[dict[str, Any]]:
    """Load all stored memory facts from disk."""
    if not MEMORY_FILE.exists():
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_memories(memories: list[dict[str, Any]]) -> None:
    """Write memory facts to disk."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memories, f, indent=2)
    except IOError as e:
        print(f"Warning: Failed to save memories: {e}")


def add_memory(fact: str) -> None:
    """Add a new memory fact."""
    memories = load_memories()
    memories.append({
        "fact": fact,
        "created": datetime.now().isoformat(),
    })
    save_memories(memories)


def clear_memories() -> None:
    """Delete all stored memories."""
    if MEMORY_FILE.exists():
        try:
            os.remove(MEMORY_FILE)
        except OSError:
            pass


def get_memories_prompt(thread_memories: Optional[list[str]] = None) -> str:
    """Format stored memories as a system prompt injection.

    Combines global user memories (file-based) and thread-scoped memories
    (from LangGraph state). Thread memories take precedence and appear first.

    Args:
        thread_memories: Optional list of memory facts from the current thread's
                        LangGraph state. If provided, these appear first in output.

    Returns:
        Formatted system prompt section, or empty string if no memories exist.
    """
    all_facts = []

    if thread_memories:
        all_facts.extend(thread_memories)

    user_memories = load_memories()
    for m in user_memories:
        fact = m.get("fact", "")
        if fact and fact not in all_facts:
            all_facts.append(fact)

    if not all_facts:
        return ""

    facts_text = "\n".join(f"- {fact}" for fact in all_facts)
    return (
        "## Stored Facts\n\n"
        "You remember the following facts from earlier conversations:\n\n"
        f"{facts_text}\n\n"
        "Use this context to provide consistent, personalized responses."
    )


async def persist_memory_to_state(
    agent: Any,
    config: Any,
    memory_facts: list[str],
) -> None:
    """Persist thread-scoped memories to LangGraph state.

    This stores memories in the agent's checkpoint state, keyed to the
    current thread. They survive across turns but not across threads.

    Args:
        agent: The LangGraph Agent instance.
        config: Runnable config with thread_id in configurable dict.
        memory_facts: List of memory facts to store in this thread.
    """
    try:
        await agent.aupdate_state(config, {"_thread_memories": memory_facts})
    except Exception as e:
        logger.warning("Failed to persist thread memories to state: %s", e)


async def load_state_memories(
    agent: Any,
    config: Any,
) -> list[str]:
    """Load thread-scoped memories from LangGraph state.

    Args:
        agent: The LangGraph Agent instance.
        config: Runnable config with thread_id in configurable dict.

    Returns:
        List of memory facts stored in this thread, or empty list if none.
    """
    try:
        state = await agent.aget_state(config)
        if state and hasattr(state, "values"):
            return state.values.get("_thread_memories", [])
    except Exception as e:
        logger.warning("Failed to load thread memories from state: %s", e)
    return []
