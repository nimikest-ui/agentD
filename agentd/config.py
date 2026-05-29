"""Shared access to the deepagents TUI config (~/.deepagents/config.toml).

Centralizes the read so callers (cli, browser_tools) don't each re-implement the
tomllib parse + missing-file fallback. Stdlib-only on purpose — keep this import light.
"""

import os
import tomllib

DEEPAGENTS_CONFIG_PATH = os.path.expanduser("~/.deepagents/config.toml")


def load_deepagents_config() -> dict:
    """Load the deepagents TUI config as a dict, or ``{}`` if missing/unreadable."""
    try:
        with open(DEEPAGENTS_CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    except (FileNotFoundError, OSError, ValueError):
        return {}
