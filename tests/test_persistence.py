"""Tests for LangGraph persistence infrastructure."""

import pytest
from typing import Callable


class TestPersistenceFactories:
    def test_make_checkpointer_with_memory_path(self, tmp_path):
        from agentd.persistence import make_checkpointer
        from langgraph.checkpoint.sqlite import SqliteSaver
        db_path = tmp_path / "test.db"
        with make_checkpointer(str(db_path)) as saver:
            assert isinstance(saver, SqliteSaver)

    def test_make_checkpointer_creates_parent_dir(self, tmp_path):
        from agentd.persistence import make_checkpointer
        db_path = tmp_path / "subdir" / "nested" / "test.db"
        with make_checkpointer(str(db_path)) as saver:
            assert db_path.parent.exists()

    def test_make_store_returns_in_memory_store(self):
        from agentd.persistence import make_store
        from langgraph.store.memory import InMemoryStore
        store = make_store()
        assert isinstance(store, InMemoryStore)


class TestGraphStructure:
    def test_agent_state_has_thread_memories_field(self):
        from agentd.graph import AgentState
        assert "_thread_memories" in AgentState.__annotations__

    def test_build_graph_returns_compiled_graph(self):
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph.state import CompiledStateGraph
        from agentd.graph import build_graph
        graph = build_graph(model_name="sonnet", checkpointer=MemorySaver())
        assert isinstance(graph, CompiledStateGraph)
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "get_state")
        assert hasattr(graph, "get_state_history")
        assert hasattr(graph, "update_state")

    def test_build_graph_without_checkpointer(self):
        from agentd.graph import build_graph
        graph = build_graph(model_name="sonnet")
        assert hasattr(graph, "invoke")


class TestAgentAPI:
    def _agent(self):
        from langgraph.checkpoint.memory import MemorySaver
        from agentd.core import Agent
        return Agent(model="sonnet", checkpointer=MemorySaver())

    def test_repr(self):
        assert "sonnet" in repr(self._agent())

    def test_get_state_empty_thread(self):
        state = self._agent().get_state("new-thread")
        assert isinstance(state.values, dict)

    def test_get_history_empty_thread(self):
        history = list(self._agent().get_history("new-thread"))
        assert history == []

    def test_update_then_get_state(self):
        a = self._agent()
        a.update_state("t1", {"_thread_memories": ["user likes Python"]})
        state = a.get_state("t1")
        assert state.values.get("_thread_memories") == ["user likes Python"]

    def test_thread_isolation(self):
        a = self._agent()
        a.update_state("t-alpha", {"_thread_memories": ["alpha fact"]})
        a.update_state("t-beta", {"_thread_memories": ["beta fact"]})
        assert a.get_state("t-alpha").values["_thread_memories"] == ["alpha fact"]
        assert a.get_state("t-beta").values["_thread_memories"] == ["beta fact"]

    def test_get_history_after_updates(self):
        a = self._agent()
        a.update_state("hist-thread", {"_thread_memories": ["v1"]})
        a.update_state("hist-thread", {"_thread_memories": ["v2"]})
        history = list(a.get_history("hist-thread"))
        assert len(history) >= 1
