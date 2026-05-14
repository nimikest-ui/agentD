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


@pytest.fixture
def agent_instance():
    """Create an Agent with MemorySaver for testing."""
    from langgraph.checkpoint.memory import MemorySaver
    from agentd.core import Agent
    agent = Agent(model="sonnet", checkpointer=MemorySaver())
    yield agent
    agent.close()


class TestAgentAPI:
    def test_repr(self, agent_instance):
        """Verify Agent __repr__ includes model name."""
        assert "sonnet" in repr(agent_instance)

    def test_get_state_empty_thread(self, agent_instance):
        """Verify get_state returns empty dict for new thread."""
        state = agent_instance.get_state("new-thread")
        assert isinstance(state.values, dict)

    def test_get_history_empty_thread(self, agent_instance):
        """Verify get_history returns empty list for new thread."""
        history = list(agent_instance.get_history("new-thread"))
        assert history == []

    def test_update_then_get_state(self, agent_instance):
        """Verify update_state persists values and get_state retrieves them."""
        agent_instance.update_state("t1", {"_thread_memories": ["user likes Python"]})
        state = agent_instance.get_state("t1")
        assert state.values.get("_thread_memories") == ["user likes Python"]

    def test_thread_isolation(self, agent_instance):
        """Verify different threads maintain isolated state."""
        agent_instance.update_state("t-alpha", {"_thread_memories": ["alpha fact"]})
        agent_instance.update_state("t-beta", {"_thread_memories": ["beta fact"]})
        assert agent_instance.get_state("t-alpha").values["_thread_memories"] == ["alpha fact"]
        assert agent_instance.get_state("t-beta").values["_thread_memories"] == ["beta fact"]

    def test_get_history_after_updates(self, agent_instance):
        """Verify get_history returns checkpoints after state updates."""
        agent_instance.update_state("hist-thread", {"_thread_memories": ["v1"]})
        agent_instance.update_state("hist-thread", {"_thread_memories": ["v2"]})
        history = list(agent_instance.get_history("hist-thread"))
        assert len(history) >= 1


class TestMemoryIntegration:
    """Test async memory integration with Agent."""

    @pytest.mark.asyncio
    async def test_persist_and_load_thread_memories(self):
        """Verify persist_memory_to_state and load_state_memories work end-to-end."""
        from langgraph.checkpoint.memory import MemorySaver
        from agentd.core import Agent
        from agentd.memory import persist_memory_to_state, load_state_memories

        agent = Agent(model="sonnet", checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "mem-thread"}}

        await persist_memory_to_state(agent, config, ["fact A", "fact B"])
        facts = await load_state_memories(agent, config)

        assert "fact A" in facts
        assert "fact B" in facts
        agent.close()

    @pytest.mark.asyncio
    async def test_load_from_empty_thread_returns_empty_list(self):
        """Verify load_state_memories returns empty list for new thread."""
        from langgraph.checkpoint.memory import MemorySaver
        from agentd.core import Agent
        from agentd.memory import load_state_memories

        agent = Agent(model="sonnet", checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "ghost-thread"}}
        facts = await load_state_memories(agent, config)
        assert facts == []
        agent.close()

    @pytest.mark.asyncio
    async def test_memories_are_thread_scoped(self):
        """Verify memories are isolated per thread."""
        from langgraph.checkpoint.memory import MemorySaver
        from agentd.core import Agent
        from agentd.memory import persist_memory_to_state, load_state_memories

        agent = Agent(model="sonnet", checkpointer=MemorySaver())
        config_a = {"configurable": {"thread_id": "scope-a"}}
        config_b = {"configurable": {"thread_id": "scope-b"}}

        await persist_memory_to_state(agent, config_a, ["thread A fact"])
        await persist_memory_to_state(agent, config_b, ["thread B fact"])

        facts_a = await load_state_memories(agent, config_a)
        facts_b = await load_state_memories(agent, config_b)

        assert "thread A fact" in facts_a
        assert "thread A fact" not in facts_b
        assert "thread B fact" in facts_b
        agent.close()
