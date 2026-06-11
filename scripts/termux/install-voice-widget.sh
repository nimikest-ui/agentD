#!/data/data/com.termux/files/usr/bin/bash
# Install the AgentD voice push-to-talk button for Termux:Widget.
#
# Run this INSIDE Termux (NOT inside Kali/proot). It copies the talk script
# into ~/.shortcuts and creates a widget button you can place on your home
# screen. It also prints the command for an optional always-available
# notification button.
#
# Prerequisites (Termux):
#   pkg install python termux-api
#   plus the Termux:API and Termux:Widget apps installed from F-Droid.
set -euo pipefail

SHORTCUTS="$HOME/.shortcuts"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
TALK_SRC="$SELF_DIR/agentd-voice-talk"
BUTTON="$SHORTCUTS/🎤 Talk to D"

if [ ! -f "$TALK_SRC" ]; then
  echo "error: cannot find agentd-voice-talk next to this installer" >&2
  exit 1
fi

mkdir -p "$SHORTCUTS/tasks"
install -m 700 "$TALK_SRC" "$SHORTCUTS/agentd-voice-talk"

cat > "$BUTTON" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
exec python "$SHORTCUTS/agentd-voice-talk"
EOF
chmod 700 "$BUTTON"

echo "Installed:"
echo "  $SHORTCUTS/agentd-voice-talk   (the push-to-talk script)"
echo "  $BUTTON   (Termux:Widget button)"
echo
echo "Next: long-press your home screen → Widgets → Termux:Widget → pick"
echo "'🎤 Talk to D'. Tap it, speak, and your words appear in the live D"
echo "session; the reply is read back to you."
echo
echo "Optional — a persistent notification button (tap from anywhere):"
echo
cat <<EOF
  termux-notification --id agentd-voice --ongoing \\
    --title "AgentD voice" --content "Tap to talk to D" \\
    --button1 "🎤 Talk" \\
    --button1-action "python $SHORTCUTS/agentd-voice-talk"
EOF
