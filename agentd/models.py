"""
AgentDModel - Custom LangChain BaseChatModel for Claude CLI integration.

Bridges LangChain with the Claude binary for API-key-free operation.
"""

from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import threading
import time
from typing import Any, Iterator, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field

AGENTD_CLI_PROVIDER = "agentd-cli"
AGENTD_CLI_DEFAULT_MODEL = "sonnet"


class AgentDModel(BaseChatModel):
    """LangChain BaseChatModel that shells out to the claude CLI binary."""

    model: str = AGENTD_CLI_DEFAULT_MODEL
    cli_binary: str = ""
    permission_mode: str = "bypassPermissions"
    call_timeout: int = 300
    profile: dict[str, Any] = Field(
        default_factory=lambda: {
            "tool_calling": True,
            "max_input_tokens": 200000,
        }
    )
    last_usage: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        if "cli_binary" not in data or not data["cli_binary"]:
            binary = shutil.which("claude") or "/root/.local/bin/claude"
            data["cli_binary"] = binary
        super().__init__(**data)

    @property
    def _llm_type(self) -> str:
        return "agentd-cli"

    def _get_ls_params(self, **kwargs: Any) -> dict[str, str]:
        return {"ls_provider": "agentd-cli", "ls_model_name": self.model}

    def bind_tools(
        self, tools: Any, *, tool_choice: Any = None, **kwargs: Any
    ) -> AgentDModel:
        """No-op: Claude CLI manages its own tools internally.

        Tool definitions are not sent to the subprocess. Claude CLI's
        --tools default provides bash and other tools server-side.
        This skips all tool serialization overhead, optimizing cache usage.
        """
        return self

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Extract plain text from various content formats."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text", "")
                    if t:
                        parts.append(t)
            return " ".join(parts)
        return str(content) if content else ""

    def _messages_to_prompt(
        self, messages: list[BaseMessage], thread_memories: Optional[list[str]] = None
    ) -> tuple[str, str]:
        """Convert LangChain message list to (system_prompt, user_prompt).

        Automatically injects persistent memories into system prompt.
        """
        system_parts: list[str] = []
        conv_parts: list[str] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                text = self._extract_text(msg.content)
                if text:
                    system_parts.append(text)
            elif isinstance(msg, HumanMessage):
                text = self._extract_text(msg.content)
                if text:
                    conv_parts.append(f"Human: {text}")
            elif isinstance(msg, AIMessage):
                text = self._extract_text(msg.content)
                if text:
                    conv_parts.append(f"Assistant: {text}")
            elif isinstance(msg, ToolMessage):
                text = self._extract_text(msg.content)
                conv_parts.append(f"Tool Result: {text}")

        # Inject memories (both file-based and thread-scoped) into system prompt
        from agentd.memory import get_memories_prompt
        memories_section = get_memories_prompt(thread_memories=thread_memories)
        if memories_section:
            system_parts.insert(0, memories_section)

        system_prompt = "\n\n".join(system_parts)

        if (
            len(conv_parts) == 1
            and conv_parts[0].startswith("Human: ")
        ):
            user_prompt = conv_parts[0][len("Human: ") :]
        else:
            user_prompt = "\n".join(conv_parts)

        return system_prompt, user_prompt

    def _build_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        """Build the claude CLI subprocess command."""
        permission_mode = self.permission_mode
        if permission_mode == "bypassPermissions" and os.geteuid() == 0:
            permission_mode = "dontAsk"

        cmd = [
            self.cli_binary,
            "--model",
            self.model,
            "--tools",
            "default",
            "--allowedTools",
            "Bash",
            "--permission-mode",
            permission_mode,
            "--print",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if permission_mode == "bypassPermissions":
            cmd.append("--dangerously-skip-permissions")
        if system_prompt:
            cmd.extend(["--append-system-prompt", system_prompt])
        cmd.append(user_prompt)
        return cmd

    def _run_cli(
        self,
        cmd: list[str],
        on_chunk: Optional[callable] = None,
    ) -> tuple[str, Optional[str]]:
        """Run Claude CLI and stream responses.

        Returns: (full_response_text, session_id)
        """
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        sel = selectors.DefaultSelector()
        assert process.stdout is not None
        assert process.stderr is not None
        sel.register(process.stdout, selectors.EVENT_READ)
        sel.register(process.stderr, selectors.EVENT_READ)

        start = time.monotonic()
        text_chunks: list[str] = []
        session_id: Optional[str] = None
        stderr_buf: list[str] = []
        usage: dict[str, Any] = {}

        while sel.get_map():
            remaining = self.call_timeout - (time.monotonic() - start)
            if remaining <= 0:
                process.kill()
                raise TimeoutError(
                    f"Claude CLI timed out after {self.call_timeout}s"
                )

            for key, _ in sel.select(timeout=remaining):
                line = key.fileobj.readline()
                if not line:
                    sel.unregister(key.fileobj)
                    continue

                if key.fileobj is process.stderr:
                    stderr_buf.append(line)
                    continue

                raw = line.strip()
                if not raw:
                    continue

                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                if payload.get("type") == "stream_event":
                    event = payload.get("event", {})
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        chunk = delta.get("text", "")
                        if chunk:
                            text_chunks.append(chunk)
                            if on_chunk:
                                on_chunk(chunk)
                elif payload.get("type") == "result":
                    session_id = payload.get("session_id")
                    if "usage" in payload:
                        usage = payload["usage"]

        rc = process.wait()
        if rc != 0:
            stderr_text = "".join(stderr_buf).strip()
            raise RuntimeError(
                f"Claude CLI exited with code {rc}: {stderr_text or '(no stderr)'}"
            )

        self.last_usage = usage
        return "".join(text_chunks), session_id

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response (sync)."""
        system_prompt, user_prompt = self._messages_to_prompt(messages)
        cmd = self._build_command(system_prompt, user_prompt)
        full_text, _ = self._run_cli(cmd)
        ai_message = AIMessage(
            content=full_text,
            usage_metadata=self.last_usage if self.last_usage else None
        )
        return ChatResult(generations=[ChatGeneration(message=ai_message)])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream response tokens (sync streaming)."""
        system_prompt, user_prompt = self._messages_to_prompt(messages)
        cmd = self._build_command(system_prompt, user_prompt)

        queue: list[str] = []
        done = threading.Event()
        error_holder: list[BaseException] = []

        def on_chunk(text: str) -> None:
            queue.append(text)

        def run() -> None:
            try:
                self._run_cli(cmd, on_chunk=on_chunk)
            except BaseException as exc:
                error_holder.append(exc)
            finally:
                done.set()

        t = threading.Thread(target=run, daemon=True)
        t.start()

        emitted = 0
        while not done.is_set() or emitted < len(queue):
            while emitted < len(queue):
                text = queue[emitted]
                emitted += 1
                is_last = done.is_set() and emitted >= len(queue)
                usage = self.last_usage if is_last else None
                chunk = ChatGenerationChunk(
                    message=AIMessageChunk(
                        content=text,
                        usage_metadata=usage if usage else None
                    )
                )
                if run_manager:
                    run_manager.on_llm_new_token(text, chunk=chunk)
                yield chunk
            time.sleep(0.01)

        t.join()
        if error_holder:
            raise error_holder[0]
