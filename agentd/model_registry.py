"""Model registry for agentD — tracks available models and providers."""

from typing import Dict, Optional, List, Tuple

_registry: Dict[str, Dict[str, str]] = {}


def register_model(
    model_id: str,
    provider: str,
    display: Optional[str] = None,
    description: Optional[str] = None,
    default_model: Optional[str] = None,
) -> None:
    """Register a model with the registry.

    Args:
        model_id: The model identifier (e.g., 'llama2', 'sonnet')
        provider: The provider name (e.g., 'ollama', 'agentd-cli')
        display: Display name for UI menus
        description: Brief description of model capabilities
        default_model: Whether this is the default model for the provider
    """
    _registry[model_id] = {
        "provider": provider,
        "display": display or model_id,
        "description": description or "",
        "is_default": bool(default_model),
    }


def get_model(model_id: str) -> Optional[Dict[str, str]]:
    """Get model info from registry."""
    return _registry.get(model_id)


def get_models_by_provider(provider: str) -> List[Tuple[str, Dict[str, str]]]:
    """Get all models for a provider."""
    return [(mid, info) for mid, info in _registry.items() if info["provider"] == provider]


def list_all_models() -> Dict[str, Dict[str, str]]:
    """List all registered models."""
    return _registry.copy()


def get_providers() -> set:
    """Get all registered providers."""
    return {info["provider"] for info in _registry.values()}


def get_models() -> List[dict]:
    """Get all models as a list of dicts (TUI-compatible format).

    Returns a list of model info dicts with model_id, provider, display name, and description.
    This is the primary API for TUI integration.
    """
    return [
        {
            "model_id": model_id,
            "provider": info["provider"],
            "display": info["display"],
            "description": info.get("description", ""),
            "is_default": info["is_default"],
        }
        for model_id, info in _registry.items()
    ]
