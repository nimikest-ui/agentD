"""Persistence infrastructure: checkpointer and store factories."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore

DEFAULT_DB_PATH = Path.home() / ".agentd" / "checkpoints.db"


@contextmanager
def make_checkpointer(db_path: str | Path | None = None) -> Iterator[SqliteSaver]:
    """Yield a SqliteSaver for the given path.

    Args:
        db_path: SQLite path. Defaults to ~/.agentd/checkpoints.db.
    """
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(path)) as saver:
        yield saver


def make_store() -> InMemoryStore:
    """Create a cross-thread InMemoryStore instance."""
    return InMemoryStore()
