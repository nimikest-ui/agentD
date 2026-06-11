#!/usr/bin/env python3
"""AgentD voice bridge (Kali side).

Connects the Termux audio helper to a live ``D --voice`` TUI session. It never
touches audio — the proot has no mic/speaker — only text crosses localhost.

One spoken turn (single-flight):

1. The Termux helper records speech, frames the transcript, sends it over TCP.
2. The bridge injects it as a prompt into the running TUI through the
   deepagents event-bus Unix socket (the TUI runs with
   ``DEEPAGENTS_CLI_EXTERNAL_EVENT_SOCKET=1``).
3. The bridge tails the session checkpoint store (``sessions.db``), on the
   auto-detected live thread, until the new finished assistant reply lands.
4. The bridge frames the reply back over the same TCP connection; the Termux
   helper speaks it with ``termux-tts-speak``.

Wire framing (both directions): a 4-byte big-endian length prefix followed by
the UTF-8 body — matching the user's voice-chat prototype.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import sqlite3
import struct
import sys
import time
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
# How long to wait for a turn to finish before giving up. Long tool-running
# turns (e.g. a CTF) can exceed the default; raise via AGENTD_VOICE_REPLY_TIMEOUT.
REPLY_TIMEOUT_S = float(os.environ.get("AGENTD_VOICE_REPLY_TIMEOUT", "600"))
POLL_INTERVAL_S = 0.4
REQUEST_READ_TIMEOUT_S = 30.0
ACK_TIMEOUT_S = 10.0


def _log(message: str) -> None:
    print(f"[voice-bridge] {message}", file=sys.stderr, flush=True)


def _state_dir() -> Path:
    return Path.home() / ".deepagents" / ".state"


def default_event_socket_path() -> Path:
    return _state_dir() / "voice-events.sock"


def default_db_path() -> Path:
    return _state_dir() / "sessions.db"


# --- framing -----------------------------------------------------------------


async def _read_frame(reader: asyncio.StreamReader) -> str:
    header = await reader.readexactly(4)
    (length,) = struct.unpack(">I", header)
    if length == 0:
        return ""
    body = await reader.readexactly(length)
    return body.decode("utf-8", "replace")


async def _write_frame(writer: asyncio.StreamWriter, text: str) -> None:
    body = text.encode("utf-8")
    writer.write(struct.pack(">I", len(body)) + body)
    await writer.drain()


# --- input: inject prompt into the live TUI ---------------------------------


async def _inject_prompt(socket_path: Path, text: str) -> None:
    """Send a ``prompt`` event to the TUI's event-bus Unix socket."""
    reader, writer = await asyncio.open_unix_connection(str(socket_path))
    try:
        payload = json.dumps({"kind": "prompt", "payload": text}) + "\n"
        writer.write(payload.encode("utf-8"))
        await writer.drain()
        ack_line = await asyncio.wait_for(reader.readline(), timeout=ACK_TIMEOUT_S)
        ack = json.loads(ack_line.decode("utf-8") or "{}")
        if not ack.get("ok"):
            raise RuntimeError(ack.get("error") or "event bus rejected prompt")
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


# --- output: tail the session checkpoint for the reply ----------------------


def _message_text(msg: object) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    parts: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
            else:
                text = getattr(block, "text", None)
                if text:
                    parts.append(str(text))
    return "".join(parts)


def _is_final_ai(msg: object) -> bool:
    """A finished assistant answer: an AI message with visible text and no
    pending tool calls (those are intermediate steps, not the reply)."""
    if getattr(msg, "type", None) != "ai":
        return False
    if getattr(msg, "tool_calls", None):
        return False
    return bool(_message_text(msg).strip())


def _max_rowid(db_path: Path) -> int:
    """Newest checkpoint insert id across all threads (cheap raw read)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    try:
        row = con.execute("SELECT MAX(rowid) FROM checkpoints").fetchone()
        return (row[0] or 0) if row else 0
    finally:
        con.close()


def _newest_thread(db_path: Path) -> str | None:
    """Thread id of the most recently written checkpoint — i.e. the session
    that is currently active (the live TUI is the only checkpoint writer)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    try:
        row = con.execute(
            "SELECT thread_id FROM checkpoints ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None
    finally:
        con.close()


_serde: object | None = None


def _get_serde() -> object:
    global _serde  # noqa: PLW0603 — module-level cache
    if _serde is None:
        from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

        _serde = JsonPlusSerializer()
    return _serde


def _latest_final_ai(db_path: Path, thread_id: str) -> tuple[object, str]:
    """``(write_key, text)`` of the newest finished assistant answer for the
    thread, or ``(None, "")`` if none yet.

    This agent stores conversation turns in the checkpointer's ``writes`` table
    (channel ``messages``) rather than snapshotting them into checkpoint
    ``channel_values``, so the reply is read from there. ``write_key`` is the
    globally-unique ``(checkpoint_id, idx)`` of the write, used to tell a fresh
    reply from a prior one. Only the main graph (``checkpoint_ns = ''``) is
    read, so intermediate tool-subgraph writes are ignored.
    """
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    try:
        rows = con.execute(
            "SELECT checkpoint_id, idx, type, value FROM writes "
            "WHERE thread_id = ? AND checkpoint_ns = '' AND channel = 'messages' "
            "ORDER BY checkpoint_id DESC, idx DESC",
            (thread_id,),
        ).fetchall()
    finally:
        con.close()

    serde = _get_serde()
    for checkpoint_id, idx, type_str, value in rows:
        if not type_str or value is None:
            continue
        try:
            decoded = serde.loads_typed((type_str, value))
        except Exception:  # noqa: BLE001 — skip anything we can't decode
            continue
        items = decoded if isinstance(decoded, list) else [decoded]
        for msg in reversed(items):
            if _is_final_ai(msg):
                return (checkpoint_id, idx), _message_text(msg)
    return None, ""


async def _handle_turn(text: str, socket_path: Path, db_path: Path) -> str:
    # Baseline before injecting so we can tell this turn's reply apart from any
    # earlier one (dedupe by the reply's unique write key, not just row growth).
    base_rowid = _max_rowid(db_path)
    base_thread = _newest_thread(db_path)
    base_key = _latest_final_ai(db_path, base_thread)[0] if base_thread else None

    await _inject_prompt(socket_path, text)

    deadline = time.monotonic() + REPLY_TIMEOUT_S
    while time.monotonic() < deadline:
        await asyncio.sleep(POLL_INTERVAL_S)
        if _max_rowid(db_path) <= base_rowid:
            continue  # the TUI hasn't recorded anything for this turn yet
        thread = _newest_thread(db_path)
        if not thread:
            continue
        key, reply = _latest_final_ai(db_path, thread)
        if reply.strip() and key is not None and key != base_key:
            return reply
    raise TimeoutError(f"no reply within {REPLY_TIMEOUT_S:.0f}s")


# --- TCP server --------------------------------------------------------------


async def _on_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    socket_path: Path,
    db_path: Path,
) -> None:
    peer = writer.get_extra_info("peername")
    try:
        text = await asyncio.wait_for(_read_frame(reader), timeout=REQUEST_READ_TIMEOUT_S)
        if not text.strip():
            await _write_frame(writer, "")
            return
        _log(f"heard: {text!r}")
        try:
            reply = await _handle_turn(text.strip(), socket_path, db_path)
            _log(f"reply: {reply[:80]!r}{'…' if len(reply) > 80 else ''}")
        except Exception as exc:  # noqa: BLE001 — surface every failure to the speaker
            reply = f"Voice bridge error: {exc}"
            _log(reply)
        await _write_frame(writer, reply)
    except (asyncio.IncompleteReadError, asyncio.TimeoutError, ConnectionError) as exc:
        _log(f"client {peer} dropped: {exc}")
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


async def serve(host: str, port: int, socket_path: Path, db_path: Path) -> None:
    server = await asyncio.start_server(
        lambda r, w: _on_client(r, w, socket_path, db_path), host, port
    )
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets or [])
    _log(f"listening on {addrs} (auto-detect active thread)")
    _log(f"event socket: {socket_path}")
    _log(f"session db:   {db_path}")
    async with server:
        await server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agentd-voice-bridge",
        description="Bridge Termux speech I/O to a live `D --voice` session.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AGENTD_VOICE_PORT", DEFAULT_PORT)),
    )
    parser.add_argument(
        "--socket",
        default=os.environ.get("DEEPAGENTS_CLI_EXTERNAL_EVENT_SOCKET_PATH")
        or str(default_event_socket_path()),
        help="TUI event-bus Unix socket path.",
    )
    parser.add_argument("--db", default=str(default_db_path()))
    args = parser.parse_args(argv)

    try:
        asyncio.run(
            serve(
                args.host,
                args.port,
                Path(args.socket).expanduser(),
                Path(args.db).expanduser(),
            )
        )
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
