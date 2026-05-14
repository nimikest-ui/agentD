"""Tests for LangGraph persistence infrastructure."""

import pytest


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
        from agentd.graph import build_graph
        graph = build_graph(model_name="sonnet", checkpointer=MemorySaver())
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "get_state")
        assert hasattr(graph, "get_state_history")
        assert hasattr(graph, "update_state")

    def test_build_graph_without_checkpointer(self):
        from agentd.graph import build_graph
        graph = build_graph(model_name="sonnet")
        assert hasattr(graph, "invoke")
