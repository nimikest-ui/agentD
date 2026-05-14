"""
Session logging for AgentD.

Provides comprehensive JSON logging of all agent sessions from initialization to completion.
Sessions are saved to timestamped files in the sessions/ directory, similar to ForestGump.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class SessionLogger:
    """Tracks and logs complete agent sessions to JSON files."""

    def __init__(self, model: str, provider: str, task: str = ""):
        """Initialize session logger.

        Args:
            model: Model name being used
            provider: Provider name (e.g., 'kimi', 'xiomimimo', 'agentd-cli')
            task: Optional task/prompt description
        """
        self.model = model
        self.provider = provider
        self.task = task
        self.start_time = datetime.now()
        self.timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        self.turns = 0
        self.messages = []
        self.log_entries = []
        self.memory = {}
        self.cost_data = {}
        self.errors = []

        # Create sessions directory
        self.sessions_dir = Path(__file__).parent.parent / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)

        self.session_file = self.sessions_dir / f"{self.timestamp}.json"

    def log(self, event_type: str, content: str, metadata: Optional[dict] = None) -> None:
        """Add a log entry to the session.

        Args:
            event_type: Type of event (e.g., 'model_init', 'api_call', 'error', 'turn')
            content: Log message
            metadata: Optional additional data
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "content": content,
        }
        if metadata:
            entry["metadata"] = metadata
        self.log_entries.append(entry)

    def log_error(
        self,
        error_type: str,
        message: str,
        provider: str,
        model: str,
        operation: str,
        details: Optional[dict] = None,
    ) -> None:
        """Log an error with full context.

        Args:
            error_type: Type of error (e.g., 'AuthenticationError', 'APIError')
            message: Error message
            provider: Which provider failed
            model: Which model was being used
            operation: What operation was being attempted
            details: Optional additional details
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "provider": provider,
            "model": model,
            "operation": operation,
        }
        if details:
            error_entry["details"] = details
        self.errors.append(error_entry)

        # Also add to general log
        self.log(
            "error",
            f"{error_type} in {operation} ({provider}/{model}): {message}",
            details,
        )

    def record_turn(
        self,
        messages: list,
        response: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Record a conversation turn.

        Args:
            messages: Messages in this turn
            response: Optional response from the model
            metadata: Optional metadata (tokens used, latency, etc.)
        """
        self.turns += 1
        turn_entry = {
            "turn": self.turns,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
        }
        if response:
            turn_entry["response"] = response
        if metadata:
            turn_entry["metadata"] = metadata
        self.messages.append(turn_entry)

    def set_memory(self, memory: dict) -> None:
        """Set session memory data."""
        self.memory = memory

    def set_cost_data(self, cost_data: dict) -> None:
        """Set cost tracking data."""
        self.cost_data = cost_data

    def save(self) -> str:
        """Save session to JSON file.

        Returns:
            Path to saved session file
        """
        end_time = datetime.now()
        duration_seconds = (end_time - self.start_time).total_seconds()

        session_data = {
            "task": self.task,
            "model": self.model,
            "provider": self.provider,
            "timestamp": self.timestamp,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "turns": self.turns,
            "messages": self.messages,
            "log": self.log_entries,
            "memory": self.memory,
            "cost": self.cost_data,
            "errors": self.errors,
        }

        with open(self.session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        return str(self.session_file)

    def list_sessions(self, limit: int = 10) -> list[dict]:
        """List recent sessions.

        Args:
            limit: Number of recent sessions to return

        Returns:
            List of session metadata dicts
        """
        if not self.sessions_dir.exists():
            return []

        files = sorted(self.sessions_dir.glob("*.json"), reverse=True)
        sessions = []

        for f in files[:limit]:
            try:
                with open(f) as fh:
                    data = json.load(fh)
                    sessions.append({
                        "file": str(f),
                        "timestamp": data.get("timestamp", "?"),
                        "model": data.get("model", "?"),
                        "provider": data.get("provider", "?"),
                        "task": data.get("task", "?"),
                        "turns": data.get("turns", 0),
                        "duration_seconds": data.get("duration_seconds", 0),
                        "errors": len(data.get("errors", [])),
                    })
            except Exception:
                pass

        return sessions

    def load_session(self, path: str) -> dict:
        """Load a saved session.

        Args:
            path: Path to session file

        Returns:
            Session data dict
        """
        with open(path) as f:
            return json.load(f)
