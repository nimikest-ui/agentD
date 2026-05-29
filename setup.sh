#!/bin/bash
# agentD setup — run once after cloning
set -e

echo "Setting up agentD..."

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install agentD + all dependencies (including deepagents TUI engine)
pip install -e ".[dev]" --quiet

# Install Playwright browsers (required for browser_tools)
playwright install chromium

echo ""
echo "Setup complete!"
echo ""
echo "To start agentD:"
echo "  source venv/bin/activate"
echo "  D                  # Interactive TUI"
echo "  D --bare           # Bare-metal shell agent (ForestGump mode)"
echo "  D -n 'your task'   # Non-interactive task"
