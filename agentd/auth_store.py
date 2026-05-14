"""Auth store for API keys and credentials (integrates with deepagents TUI).

Handles credential storage for:
- OLLAMA_API_KEY (for Ollama Cloud models at ollama.com)
- MOONSHOT_API_KEY (for Kimi models)
- Other provider keys
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict

# Use deepagents auth store location if available, otherwise fallback
AUTH_STORE_PATH = Path.home() / ".deepagents" / ".state" / "auth.json"
AUTH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_credentials() -> Dict[str, str]:
    """Load all stored credentials from auth store."""
    if not AUTH_STORE_PATH.exists():
        return {}
    try:
        with open(AUTH_STORE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_credentials(creds: Dict[str, str]) -> None:
    """Save credentials to auth store (mode 0600 for security)."""
    AUTH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_STORE_PATH, "w") as f:
        json.dump(creds, f, indent=2)
    # Set restrictive permissions
    os.chmod(AUTH_STORE_PATH, 0o600)


def get_credential(key: str) -> Optional[str]:
    """Get a single credential (checks env var first, then auth store)."""
    # Environment variable takes priority
    env_value = os.environ.get(key)
    if env_value:
        return env_value

    # Fall back to auth store
    creds = load_credentials()
    return creds.get(key)


def set_credential(key: str, value: str) -> None:
    """Store a credential in auth store."""
    creds = load_credentials()
    creds[key] = value
    save_credentials(creds)
    # Also set in environment so it takes effect immediately
    os.environ[key] = value


def delete_credential(key: str) -> None:
    """Remove a credential from auth store."""
    creds = load_credentials()
    if key in creds:
        del creds[key]
        save_credentials(creds)
    # Also remove from environment
    os.environ.pop(key, None)


# Provider credential keys
OLLAMA_API_KEY = "OLLAMA_API_KEY"
MOONSHOT_API_KEY = "MOONSHOT_API_KEY"

# Supported credential keys for /auth command
SUPPORTED_CREDENTIALS = {
    OLLAMA_API_KEY: "Ollama Cloud API Key (from ollama.com/settings/keys)",
    MOONSHOT_API_KEY: "Kimi/Moonshot API Key (for Chinese LLM support)",
}


def get_supported_keys() -> Dict[str, str]:
    """Get all supported credential keys and their descriptions."""
    return SUPPORTED_CREDENTIALS.copy()
