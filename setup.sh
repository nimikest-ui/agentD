#!/bin/bash
# agentD setup — run once after cloning
set -e

echo "Setting up agentD..."

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Upgrade pip toolchain (avoids PyYAML cython sdist build on py3.13)
pip install --upgrade --quiet pip setuptools wheel

# Install agentD + all dependencies except browser-use (hard-pins anthropic
# 0.76 which conflicts with langchain-anthropic >=0.96). Install browser-use
# with --no-deps so it shares the agentD-resolved versions.
pip install --quiet \
    "langchain>=1.0.0" "langgraph>=1.1.0" "langchain-anthropic>=1.0.0" \
    "pydantic>=2.0" "httpx>=0.24.0" \
    "deepagents>=0.6.1" "deepagents-cli>=0.0.59,<0.1.0" \
    "anthropic>=0.96.0" "openai>=1.0.0" "ollama>=0.6.0" \
    "playwright>=1.50.0" "firecrawl-py>=0.0.1" "tavily-python>=0.3.0" \
    "aiosqlite>=0.19.0" "sqlalchemy>=2.0.0" "langgraph-checkpoint-sqlite" \
    "langsmith>=0.1.0" "textual>=0.20.0" "requests>=2.32.0" \
    pytest pytest-asyncio black ruff
pip install --quiet --no-deps -e ".[dev]"
pip install --quiet --no-deps --resume-retries 20 "browser-use>=0.12.0"
# browser-use runtime deps (subset, avoids version-pin conflicts)
pip install --quiet --resume-retries 20 \
    psutil bubus cdp-use cloudpickle browser-use-sdk inquirerpy \
    markdownify pillow posthog pyotp pypdf python-docx reportlab \
    screeninfo uuid7 google-api-core google-api-python-client \
    google-auth-oauthlib google-auth google-genai groq

# Install Playwright browsers (required for browser_tools)
playwright install chromium

# Install provider shim into venv site-packages so deepagents-cli subprocess
# sees agentD's custom model classes + auth slots at startup.
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
echo "import agentd._provider_shim" > "$SITE_PACKAGES/_agentd_providers.pth"

# Bump deepagents-cli slash-menu cap so all commands are reachable.
AUTOCOMPLETE="$SITE_PACKAGES/deepagents_cli/widgets/autocomplete.py"
if [ -f "$AUTOCOMPLETE" ]; then
    sed -i 's/^MAX_SUGGESTIONS = 10$/MAX_SUGGESTIONS = 100/' "$AUTOCOMPLETE"
    rm -f "$SITE_PACKAGES/deepagents_cli/widgets/__pycache__/autocomplete."*.pyc
fi

# Seed ~/.deepagents/config.toml provider model lists if not already present.
CONFIG="$HOME/.deepagents/config.toml"
mkdir -p "$(dirname "$CONFIG")"
if [ ! -f "$CONFIG" ] || ! grep -q "models.providers.agentd-cli" "$CONFIG" 2>/dev/null; then
    cat >> "$CONFIG" <<'EOF'

[models]
default = "agentd-cli:haiku"

[warnings]
suppress = ["tavily"]

[models.providers.agentd-cli]
models = ["haiku", "sonnet", "opus"]

[models.providers.copilot-cli]
models = ["copilot"]

[models.providers.kimi]
models = [
    "kimi-k2.6",
    "kimi-k2.5",
    "moonshot-v1-auto",
    "moonshot-v1-8k",
    "moonshot-v1-32k",
    "moonshot-v1-128k",
    "moonshot-v1-8k-vision-preview",
    "moonshot-v1-32k-vision-preview",
    "moonshot-v1-128k-vision-preview",
]

[models.providers.xiomimimo]
models = [
    "mimo-v2-flash",
    "mimo-7b",
    "mimo-v2.5",
    "mimo-v2-pro",
    "mimo-v2-omni",
    "mimo-v2-tts",
    "mimo-v2.5-pro",
]
EOF
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start agentD:"
echo "  source venv/bin/activate"
echo "  D                  # Interactive TUI"
echo "  D -n 'your task'   # Non-interactive task"
