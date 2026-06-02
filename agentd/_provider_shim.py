"""agentD provider bridge into langchain + deepagents-cli runtime.

Imported at interpreter startup via a `.pth` bootstrapper installed by
`setup.sh` into the active venv's site-packages. Patches three registries
so deepagents-cli (launched as a subprocess by `D`) sees agentD's custom
chat-model classes and credential slots:

1. `langchain.chat_models.base._BUILTIN_PROVIDERS` — lets `init_chat_model`
   resolve `agentd-cli:*`, `copilot-cli:*`, `kimi:*`, `xiomimimo:*` specs.
2. `deepagents_cli.model_config.PROVIDER_API_KEY_ENV` — surfaces kimi /
   xiomimimo / firecrawl / langsmith slots in the `/auth` UI.
3. `deepagents_cli.model_config.NO_AUTH_REQUIRED_PROVIDERS` — marks
   agentd-cli and copilot-cli as ambient-auth (subprocess to local CLI).

Model lists for the `/model` picker live in `~/.deepagents/config.toml`
under `[models.providers.<name>]`; setup.sh seeds them on first install.
"""


def _register_langchain_providers() -> None:
    try:
        from langchain.chat_models import base as _b
    except Exception:
        return

    def _call(cls, model, **kwargs):
        return cls(model=model, **kwargs)

    # Register both hyphen and underscore forms — langchain checks raw
    # prefix at base.py:603 and normalized form at base.py:624.
    spec = {
        "agentd_cli":  ("agentd.models", "AgentDModel"),
        "agentd-cli":  ("agentd.models", "AgentDModel"),
        "copilot_cli": ("agentd.models", "CopilotModel"),
        "copilot-cli": ("agentd.models", "CopilotModel"),
        "kimi":        ("agentd.models", "KimiModel"),
        "xiomimimo":   ("agentd.models", "XiaomiModel"),
        "xiaomi":      ("agentd.models", "XiaomiModel"),
        "mimo":        ("agentd.models", "XiaomiModel"),
    }
    for prov, (mod, cls_name) in spec.items():
        _b._BUILTIN_PROVIDERS[prov] = (mod, cls_name, _call)

    try:
        _b._get_chat_model_creator.cache_clear()
    except Exception:
        pass


def _register_deepagents_auth() -> None:
    try:
        from deepagents_cli import model_config as _mc
    except Exception:
        return

    extra_keys = {
        "kimi":      "MOONSHOT_API_KEY",
        "xiomimimo": "XIOMIMIMO_API_KEY",
        "firecrawl": "FIRECRAWL_API_KEY",
        "langsmith": "LANGSMITH_API_KEY",
    }
    for prov, env in extra_keys.items():
        _mc.PROVIDER_API_KEY_ENV.setdefault(prov, env)

    try:
        _mc.NO_AUTH_REQUIRED_PROVIDERS = frozenset(
            set(_mc.NO_AUTH_REQUIRED_PROVIDERS) | {"agentd-cli", "copilot-cli"}
        )
    except Exception:
        pass


_register_langchain_providers()
_register_deepagents_auth()
