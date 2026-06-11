#!/data/data/com.termux/files/usr/bin/bash
# Install the AgentD voice Termux:GUI widget daemon.
#
# Run this INSIDE Termux (NOT inside Kali/proot).
#
# Usage:
#   bash install-voice-gui.sh [widget-id]
#
# Passing the widget id (the one Termux:GUI showed when you placed the widget)
# saves it and sets up a Termux:Boot autostart so the daemon survives reboots.
#
# Prerequisites (Termux):
#   pkg install python termux-api
#   pip install termuxgui
#   plus the Termux:GUI and Termux:API apps installed from F-Droid.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
GUI_SRC="$SELF_DIR/agentd-voice-gui"
BIN="$HOME/.local/bin"
DEST="$BIN/agentd-voice-gui"
WID="${1:-}"

if [ ! -f "$GUI_SRC" ]; then
  echo "error: cannot find agentd-voice-gui next to this installer" >&2
  exit 1
fi

mkdir -p "$BIN"
install -m 700 "$GUI_SRC" "$DEST"
echo "Installed daemon: $DEST"

if ! python -c "import termuxgui" 2>/dev/null; then
  echo "Installing termuxgui (python binding)…"
  pip install termuxgui
fi

if [ -n "$WID" ]; then
  mkdir -p "$HOME/.config/agentd-voice"
  printf '%s\n' "$WID" > "$HOME/.config/agentd-voice/widget_id"
  echo "Saved widget id: $WID"

  BOOT="$HOME/.termux/boot"
  mkdir -p "$BOOT"
  cat > "$BOOT/agentd-voice-gui" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
exec python "$DEST"
EOF
  chmod 700 "$BOOT/agentd-voice-gui"
  echo "Created Termux:Boot autostart: $BOOT/agentd-voice-gui (needs the Termux:Boot app)"
fi

echo
echo "Start the daemon now (keep it running so the widget responds):"
if [ -n "$WID" ]; then
  echo "  python $DEST"
else
  echo "  python $DEST <widget-id>"
fi
echo
echo "The widget then shows '🎤 Talk to D' + a status line; tapping it speaks your"
echo "turn into the live 'D --voice' session and reads the reply back. The daemon"
echo "must stay alive for the widget to work."
