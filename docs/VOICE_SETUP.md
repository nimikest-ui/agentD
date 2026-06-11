# Voice for AgentD

Talk to your live `D` session: speak a prompt, see it appear in the session,
and hear the reply read back. The same button also lets you fire a command at a
backgrounded `D` from your Android home screen.

## Why it is split across two sides

`D` runs inside the **Kali proot**, which has **no microphone or speaker**. The
only thing that can reach Android's audio is **Termux:API**, which lives on the
**Termux** side, outside the proot. So:

| Side | Job |
|------|-----|
| **Termux** | Records speech (`termux-speech-to-text`) and speaks replies (`termux-tts-speak`). |
| **Kali (`D --voice`)** | Receives your transcribed text into the live session and produces the reply. Never touches audio. |

Only **text** crosses the boundary, over a localhost TCP socket (port `8787`
by default). Kali and Termux share the network namespace, so `127.0.0.1` works
between them.

```
 [Termux]                                  [Kali — your live D session]
  🎤 termux-speech-to-text  ──TCP 8787──►  agentd.voice.bridge ──unix sock──►  D TUI (live session)
  🔊 termux-tts-speak       ◄──TCP 8787──  bridge tails sessions.db  ◄───────  reply persisted
```

No fork of the deepagents engine: input uses its supported **event bus**
(`DEEPAGENTS_CLI_EXTERNAL_EVENT_SOCKET`); output is a **read-only tail** of the
session checkpoint store (`~/.deepagents/.state/sessions.db`). The bridge
auto-detects the live session's thread from the newest checkpoint after it
injects, so there's no thread to configure.

## Kali side

Just start the session with voice enabled:

```bash
D --voice
```

This opens the event-bus socket at `~/.deepagents/.state/voice-events.sock` and
starts the bridge (`python -m agentd.voice.bridge`) as a child that exits with
the TUI. The bridge auto-detects which thread the session is using. Override the
port with `AGENTD_VOICE_PORT` if `8787` is taken.

## Termux side (one-time install)

In a **Termux** shell (not inside Kali):

```bash
pkg install python termux-api          # plus the Termux:API + Termux:Widget apps from F-Droid
bash /path/to/agentD/scripts/termux/install-voice-widget.sh
```

The installer copies `agentd-voice-talk` into `~/.shortcuts/` and creates a
**Termux:Widget** button named `🎤 Talk to D`. Add that widget to your home
screen.

For a button that's always available (not just on the home screen), the
installer also prints a `termux-notification` command that puts a persistent
**🎤 Talk** action in your notification shade.

### Alternative trigger: Termux:GUI widget

A Termux:GUI widget gives a styled home-screen button with no terminal popup and
a live status line (Listening… / what it heard / the reply). Unlike the
Termux:Widget button, it needs a small **daemon kept running** to respond.

Place the Termux:GUI widget on your home screen (note the widget id it shows),
then in Termux:

```bash
pip install termuxgui                   # plus the Termux:GUI app from F-Droid
bash ~/kali-fs/root/agentD/scripts/termux/install-voice-gui.sh <widget-id>
python ~/.local/bin/agentd-voice-gui    # start the daemon (id was saved)
```

Passing `<widget-id>` also writes a Termux:Boot autostart so the daemon comes
back after a reboot (needs the Termux:Boot app). Keep the daemon alive for the
widget to work.

### Alternative trigger: a keyboard key

Bind a hardware key with a key-mapper app (e.g. Key Mapper) that fires Termux's
`RUN_COMMAND` intent at `~/.shortcuts/agentd-voice-talk`. One-time: add
`allow-external-apps=true` to `~/.termux/termux.properties` and run
`termux-reload-settings`.

## Using it

1. On the phone running Kali, start `D --voice` (leave it running — it can be
   backgrounded).
2. Tap **🎤 Talk to D** (widget or notification).
3. Speak. Your words appear in the session as a submitted message.
4. The agent's reply is read aloud.

Because the trigger lives on the Termux side, it works whether `D` is in front
of you or running in the background — which is how you fire a quick command
("set an alarm", "start overthewire bandit") at a session you're not looking at.

## Tuning / troubleshooting

- **Port**: set `AGENTD_VOICE_PORT` on both sides if `8787` clashes.
- **"Voice bridge unreachable"**: `D --voice` isn't running, or the port
  differs between sides.
- **No reply spoken**: the bridge waits up to 600s for a finished reply; raise
  it with `AGENTD_VOICE_REPLY_TIMEOUT` (seconds) if a long tool-running turn
  exceeds that.
- **Bridge logs**: the bridge prints to stderr in the `D` terminal, prefixed
  `[voice-bridge]`.
