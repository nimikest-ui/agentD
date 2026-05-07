#!/bin/bash
# AgentD Startup Script
# Usage: ./start.sh [command]

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate venv
source "$SCRIPT_DIR/venv/bin/activate"

# Show logo if interactive
if [ "$#" -eq 0 ]; then
    clear
    cat "$SCRIPT_DIR/logo.txt"
    echo ""
    sleep 1
fi

# Run command or start TUI
if [ "$#" -eq 0 ]; then
    # No arguments - start interactive TUI
    D --bare
else
    # With arguments - run command
    "$@"
fi
