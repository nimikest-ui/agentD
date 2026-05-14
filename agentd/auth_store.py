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
    """Get a single credential (checks env var first, then auth store).

    Supports both flat format (for legacy) and nested format from deepagents TUI.
    Maps credential keys to TUI provider names:
    - MOONSHOT_API_KEY → credentials.kimi
    - OLLAMA_API_KEY → credentials.ollama
    """
    # Environment variable takes priority
    env_value = os.environ.get(key)
    if env_value:
        return env_value

    # Fall back to auth store (handles both nested TUI format and flat legacy format)
    creds = load_credentials()

    # Try flat format first (legacy)
    if key in creds:
        val = creds[key]
        # Handle nested credential object from TUI {type: api_key, key: ...}
        if isinstance(val, dict) and "key" in val:
            return val["key"]
        return val

    # Try nested format from deepagents TUI
    if "credentials" in creds and isinstance(creds["credentials"], dict):
        # Map credential env var names to TUI provider names
        provider_map = {
            "MOONSHOT_API_KEY": "kimi",
            "OLLAMA_API_KEY": "ollama",
        }
        provider_name = provider_map.get(key)
        if provider_name and provider_name in creds["credentials"]:
            cred_obj = creds["credentials"][provider_name]
            if isinstance(cred_obj, dict) and "key" in cred_obj:
                return cred_obj["key"]
            return cred_obj

    return None


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
