#!/usr/bin/env python3
"""
AgentD Command-Line Interface.

Provides the 'D' shortcut command and 'agentd' full command.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def get_tui_engine_path():
    """Locate the TUI engine (agentd) used by agentD."""
    # Try to find agentd in the current environment
    try:
        result = subprocess.run(
            ["which", "agentd"],
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
        Path.home() / ".venv" / "bin" / "agentd",
        Path("/opt/agentd/bin/agentd"),
        Path("/usr/local/bin/agentd"),
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


def main():
    """Main entry point for AgentD CLI."""
    parser = argparse.ArgumentParser(
        description="AgentD - LLM Agent Framework",
        prog="D" if sys.argv[0].endswith("D") else "agentd",
    )

    parser.add_argument(
        "-M", "--model",
        default="claude-cli",
        help="Model to use (default: claude-cli)"
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

    # Add model
    if args.model != "claude-cli":
        cmd.extend(["-M", args.model])
    else:
        cmd.extend(["-M", "claude-cli"])

    # Add flags (TUI mode with all yes)
    cmd.extend(["-S", "all"])

    # Auto-approve if requested
    if args.auto_approve:
        cmd.append("-y")

    # Resume
    if args.resume:
        cmd.append("-r")
    elif args.thread_id:
        cmd.extend(["--thread-id", args.thread_id])

    # Non-interactive task
    if args.non_interactive:
        cmd.extend(["-n", args.non_interactive])

    # Add unknown args
    cmd.extend(unknown)

    # Execute
    try:
        sys.exit(subprocess.run(cmd).returncode)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except FileNotFoundError:
        print(f"Error: AgentD TUI engine not found at {tui_engine_path}", file=sys.stderr)
        sys.exit(1)

def main_d():
    """Entry point for 'D' shortcut with auto-approval defaults."""
    # Insert auto-approval by default for 'D' command
    if "--auto-approve" not in sys.argv and "-y" not in sys.argv:
        sys.argv.insert(1, "--auto-approve")
    main()

if __name__ == "__main__":
    main()
