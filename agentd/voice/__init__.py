"""AgentD voice: localhost bridge between the Termux audio helper and a live
`D --voice` TUI session.

The Kali proot has no microphone or speaker, so all audio I/O happens on the
Termux side (`termux-speech-to-text` / `termux-tts-speak`). Only text crosses
the boundary, over a localhost TCP socket, to :mod:`agentd.voice.bridge`.
"""
