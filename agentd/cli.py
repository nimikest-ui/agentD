#!/usr/bin/env python3
"""
AgentD Command-Line Interface.

Provides the 'D' shortcut command and 'agentd' full command.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def get_tui_engine_path():
    """Locate the TUI engine (deepagents) used by agentD."""
    # First: check same bin/ dir as the running Python — works without venv activation
    same_bin = Path(sys.executable).parent / "deepagents"
    if same_bin.exists():
        return str(same_bin)

    # Second: which deepagents (works when venv is activated in PATH)
    try:
        result = subprocess.run(
            ["which", "deepagents"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Fallback paths
    fallback_paths = [
        Path.home() / ".venv" / "bin" / "deepagents",
        Path("/opt/deepagents/bin/deepagents"),
        Path("/usr/local/bin/deepagents"),
    ]

    for path in fallback_paths:
        if path.exists():
            return str(path)

    raise FileNotFoundError(
        "AgentD TUI engine not found. Install with: pip install -e ."
    )

def run_non_interactive(task: str, thread_id: str = "default", model: str = "sonnet") -> int:
    """Run a task through Agent.invoke() with thread persistence.

    Args:
        task: The task text to run.
        thread_id: Thread ID for checkpoint isolation.
        model: Model name.

    Returns:
        Exit code (0 = success).
    """
    from agentd.core import Agent
    try:
        agent = Agent(model=model)
        result = agent.invoke(task, thread_id=thread_id)
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            print(getattr(last, "content", str(last)))
        agent.close()
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _get_startup_model() -> str:
    """Read startup model from ~/.deepagents/config.toml.

    Priority: [models].default > [models].recent > fallback haiku.
    """
    from agentd.config import load_deepagents_config
    models = load_deepagents_config().get("models", {})
    return models.get("default") or models.get("recent") or "agentd-cli:haiku"


def main():
    """Main entry point for AgentD CLI."""
    parser = argparse.ArgumentParser(
        description="AgentD - LLM Agent Framework",
        prog="D" if sys.argv[0].endswith("D") else "agentd",
    )

    parser.add_argument(
        "-M", "--model",
        default=None,
        help="Model to use (default: agentd-cli:haiku, or last /model selection)"
    )

    parser.add_argument(
        "-n", "--non-interactive",
        help="Run non-interactive task"
    )

    parser.add_argument(
        "-t", "--thread-id",
        help="Resume specific thread/conversation"
    )


    parser.add_argument(
        "-r", "--resume",
        action="store_true",
        help="Resume last conversation"
    )

    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve all tool calls (dangerous!)"
    )

    parser.add_argument(
        "--voice",
        action="store_true",
        help="Enable voice: open the event-bus socket and run the localhost "
             "bridge for Termux speech I/O (the bridge auto-detects the live "
             "session's thread)."
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    # Parse known args, pass rest to TUI engine
    args, unknown = parser.parse_known_args()

    # Handle non-interactive mode
    if args.non_interactive:
        thread_id = args.thread_id or "default"
        model = args.model or "sonnet"
        sys.exit(run_non_interactive(
            args.non_interactive,
            thread_id=thread_id,
            model=model,
        ))
    try:
        tui_engine_path = get_tui_engine_path()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    cmd = [tui_engine_path]

    # Add model — use explicit flag or read persisted preference
    model = args.model if args.model is not None else _get_startup_model()
    cmd.extend(["-M", model])

    # Add flags (TUI mode with all yes)
    cmd.extend(["-S", "all"])

    # Auto-approve if requested
    if args.auto_approve:
        cmd.append("-y")

    # Resume. (Voice does not pin a thread: deepagents has no --thread-id and
    # -r <name> for a missing thread silently forks a new UUID, so the bridge
    # auto-detects the live session's thread from the newest checkpoint.)
    if args.resume:
        cmd.append("-r")
    elif args.thread_id:
        cmd.extend(["--thread-id", args.thread_id])

    # Non-interactive task
    if args.non_interactive:
        cmd.extend(["-n", args.non_interactive])

    # Add unknown args
    cmd.extend(unknown)

    # Build the child environment and, for voice, start the localhost bridge.
    env = os.environ.copy()
    bridge_proc = None
    if args.voice:
        socket_path = Path.home() / ".deepagents" / ".state" / "voice-events.sock"
        socket_path.parent.mkdir(parents=True, exist_ok=True)
        env["DEEPAGENTS_CLI_EXTERNAL_EVENT_SOCKET"] = "1"
        env["DEEPAGENTS_CLI_EXTERNAL_EVENT_SOCKET_PATH"] = str(socket_path)
        port = env.get("AGENTD_VOICE_PORT", "8787")
        try:
            bridge_proc = subprocess.Popen(
                [sys.executable, "-m", "agentd.voice.bridge",
                 "--socket", str(socket_path), "--port", str(port)],
                env=env,
            )
            print(f"[voice] bridge started (pid {bridge_proc.pid}) on "
                  f"127.0.0.1:{port}", file=sys.stderr)
        except Exception as e:
            print(f"[voice] failed to start bridge: {e}", file=sys.stderr)

    # Execute
    try:
        sys.exit(subprocess.run(cmd, env=env).returncode)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except FileNotFoundError:
        print(f"Error: AgentD TUI engine not found at {tui_engine_path}", file=sys.stderr)
        sys.exit(1)
    finally:
        if bridge_proc is not None:
            bridge_proc.terminate()
            try:
                bridge_proc.wait(timeout=5)
            except Exception:
                bridge_proc.kill()

def main_d():
    """Entry point for 'D' shortcut with auto-approval defaults."""
    # Insert auto-approval by default for 'D' command
    if "--auto-approve" not in sys.argv and "-y" not in sys.argv:
        sys.argv.insert(1, "--auto-approve")
    main()

if __name__ == "__main__":
    main()
