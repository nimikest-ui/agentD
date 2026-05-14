"""Auth store for API keys and credentials — delegates to deepagents_cli.

Handles credential storage for:
- OLLAMA_API_KEY (for Ollama Cloud models at ollama.com)
- MOONSHOT_API_KEY (for Kimi models)
- XIOMIMIMO_API_KEY (for Xiaomi MiMo models)
- LANGSMITH_API_KEY (for LangSmith tracing and observability)
- Other provider keys

Delegates to deepagents_cli.auth_store for actual file I/O and schema validation.
Maps environment variable names (MOONSHOT_API_KEY) to provider names (kimi).
"""

import os
from typing import Optional, Dict

try:
    from deepagents_cli.auth_store import (
        get_stored_key as _get_stored_key,
        set_stored_key as _set_stored_key,
        delete_stored_key as _delete_stored_key,
        load_credentials as _da_load_credentials,
    )
    _DEEPAGENTS_AVAILABLE = True
except ImportError:
    _DEEPAGENTS_AVAILABLE = False


# Map environment variable names to deepagents provider names
_PROVIDER_MAP = {
    "MOONSHOT_API_KEY": "kimi",
    "XIOMIMIMO_API_KEY": "xiomimimo",
    "OLLAMA_API_KEY": "ollama",
    "LANGSMITH_API_KEY": "langsmith",
}


def get_credential(key: str) -> Optional[str]:
    """Get a single credential (checks env var first, then auth store).

    Args:
        key: Credential key (e.g., "MOONSHOT_API_KEY", "LANGSMITH_API_KEY")

    Returns:
        Credential value, or None if not found
    """
    # Environment variable takes priority
    env_value = os.environ.get(key)
    if env_value:
        return env_value

    if not _DEEPAGENTS_AVAILABLE:
        return None

    # Map env var name to provider name
    provider = _PROVIDER_MAP.get(key, key.lower())

    try:
        return _get_stored_key(provider)
    except Exception:
        return None


def set_credential(key: str, value: str) -> None:
    """Store a credential in auth store.

    Args:
        key: Credential key (e.g., "MOONSHOT_API_KEY")
        value: Credential value to store
    """
    if not _DEEPAGENTS_AVAILABLE:
        raise RuntimeError("deepagents_cli not installed; cannot store credentials")

    provider = _PROVIDER_MAP.get(key, key.lower())

    try:
        _set_stored_key(provider, value)
    except Exception as e:
        raise RuntimeError(f"Failed to store credential for {key}: {e}")

    # Also set in environment so it takes effect immediately
    os.environ[key] = value


def delete_credential(key: str) -> None:
    """Remove a credential from auth store.

    Args:
        key: Credential key (e.g., "MOONSHOT_API_KEY")
    """
    if not _DEEPAGENTS_AVAILABLE:
        raise RuntimeError("deepagents_cli not installed; cannot delete credentials")

    provider = _PROVIDER_MAP.get(key, key.lower())

    try:
        _delete_stored_key(provider)
    except Exception:
        pass

    # Also remove from environment
    os.environ.pop(key, None)


def load_credentials() -> Dict[str, str]:
    """Load all stored credentials from auth store.

    Returns:
        Dictionary of provider names to credentials
    """
    if not _DEEPAGENTS_AVAILABLE:
        return {}

    try:
        return _da_load_credentials()
    except Exception:
        return {}


def save_credentials(creds: Dict[str, str]) -> None:
    """Save credentials to auth store.

    Note: This is a legacy interface. Use set_credential() for new code.

    Args:
        creds: Dictionary of credentials to save
    """
    if not _DEEPAGENTS_AVAILABLE:
        raise RuntimeError("deepagents_cli not installed; cannot save credentials")

    for key, value in creds.items():
        try:
            set_credential(key, value)
        except Exception:
            pass


# Provider credential keys
OLLAMA_API_KEY = "OLLAMA_API_KEY"
MOONSHOT_API_KEY = "MOONSHOT_API_KEY"
XIOMIMIMO_API_KEY = "XIOMIMIMO_API_KEY"
LANGSMITH_API_KEY = "LANGSMITH_API_KEY"

# Supported credential keys for /auth command
SUPPORTED_CREDENTIALS = {
    OLLAMA_API_KEY: "Ollama Cloud API Key (from ollama.com/settings/keys)",
    MOONSHOT_API_KEY: "Kimi/Moonshot API Key (for Chinese LLM support)",
    XIOMIMIMO_API_KEY: "Xiaomi MiMo API Key (from xiaomimimo.com/settings/keys)",
    LANGSMITH_API_KEY: "LangSmith API Key (for tracing & observability at smith.langchain.com)",
}


def get_supported_keys() -> Dict[str, str]:
    """Get all supported credential keys and their descriptions."""
    return SUPPORTED_CREDENTIALS.copy()
