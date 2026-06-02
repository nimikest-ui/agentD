"""Persistence infrastructure: checkpointer and store factories."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# langgraph-checkpoint-sqlite is kept out of the lean Termux core: its only
# Termux-incompatible piece is the *vector store* (which pulls `sqlite-vec`,
# a wheels-only extension with no Android/bionic build). The SqliteSaver
# checkpointer itself never imports sqlite-vec, so Termux installs it with
# `pip install --no-deps langgraph-checkpoint-sqlite` (see setup-termux.sh).
# When it's absent entirely we degrade to an in-process checkpointer so the
# agent still runs — sessions just won't persist across restarts.
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    _SQLITE_SAVER_AVAILABLE = True
except ImportError:
    SqliteSaver = None  # type: ignore[assignment,misc]
    _SQLITE_SAVER_AVAILABLE = False

DEFAULT_DB_PATH = Path.home() / ".agentd" / "checkpoints.db"


@contextmanager
def make_checkpointer(
    db_path: str | Path | None = None,
) -> Iterator[BaseCheckpointSaver]:
    """Yield a checkpointer for the given path.

    Uses a persistent SqliteSaver when langgraph-checkpoint-sqlite is installed,
    and falls back to an in-process InMemorySaver when it isn't (e.g. a minimal
    install that omitted it). The in-memory fallback keeps the agent runnable but
    does not persist sessions across process restarts.

    Args:
        db_path: SQLite path. Defaults to ~/.agentd/checkpoints.db.
    """
    if not _SQLITE_SAVER_AVAILABLE:
        yield InMemorySaver()
        return
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(path)) as saver:
        yield saver


def make_store() -> InMemoryStore:
    """Create a cross-thread InMemoryStore instance."""
    return InMemoryStore()
