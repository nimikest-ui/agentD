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
