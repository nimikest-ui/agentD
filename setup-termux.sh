#!/data/data/com.termux/files/usr/bin/bash
# agentD — Termux (Android, bionic libc, no-root) setup.
#
# Installs the LEAN HEADLESS CORE: the agent + HTTP providers (Xiaomi/mimo, Kimi)
# and the Claude CLI provider. Browser automation (Playwright/Chromium) is NOT
# installed — its bundled Chromium is a glibc ELF and cannot run on Termux.
#
# Usage:  bash setup-termux.sh
set -euo pipefail

echo ">> agentD Termux setup"

if [ -z "${PREFIX:-}" ] || ! command -v pkg >/dev/null 2>&1; then
    echo "!! This script targets Termux (no 'pkg'/\$PREFIX found)."
    echo "   On a normal Linux host use ./setup.sh instead."
    exit 1
fi

# Defensive: if a transitive dep pulls grpcio, build it against system libs
# rather than failing on Termux.
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1

echo ">> Installing Termux system packages + build toolchain"
pkg update -y && pkg upgrade -y
pkg install -y \
    python nodejs-lts rust binutils clang make \
    openssl libxml2 libxslt libjpeg-turbo zlib pkg-config git

# Prefer Termux-prebuilt wheels for heavy native deps (best-effort; names vary
# across Termux versions, so don't fail the whole install if absent).
pkg install -y python-cryptography python-lxml python-pillow 2>/dev/null || \
    echo "   (prebuilt python-cryptography/lxml/pillow not available — pip will build them)"

echo ">> Creating virtualenv"
python -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip wheel setuptools

echo ">> Installing agentD (lean core — no browser extra)"
pip install -e .

# Optional: the Claude CLI provider (agentd-cli) shells out to the Node-based
# `claude` binary. Install it if Node is present; harmless to skip.
if command -v npm >/dev/null 2>&1; then
    echo ">> Installing Claude CLI (for the agentd-cli provider)"
    npm install -g @anthropic-ai/claude-code || \
        echo "   (claude CLI install failed — the mimo/kimi HTTP providers still work)"
    echo "   Run 'claude' once to log in if you plan to use the agentd-cli provider."
fi

echo ">> Verifying install"
python - <<'PY'
import agentd
from agentd.browser_tools import BrowserToolkit
status = BrowserToolkit().get_status()
assert status["browser_use"] is False, "browser_use unexpectedly present on Termux"
print("   import agentd: OK   browser_use:", status["browser_use"])
PY
D --version || true

cat <<'EOF'

Setup complete!

Next steps:
  source venv/bin/activate
  export XIOMIMIMO_API_KEY=...     # for the mimo provider (recommended primary)
  export MOONSHOT_API_KEY=...      # for the kimi provider (optional)

  D -n 'hello'                     # non-interactive task (default provider)
  D -M mimo-v2.5-pro -n 'task'     # explicit mimo provider
  D                                # interactive Textual TUI

Browser automation is disabled on Termux by design. See docs/TERMUX.md.
EOF
