"""
AgentDModel - Custom LangChain BaseChatModel for Claude CLI integration.

Bridges LangChain with the Claude binary for API-key-free operation.
Integrated with LangSmith for automatic tracing and observability.
"""

from __future__ import annotations

import asyncio
import json
import os
import selectors
import shutil
import subprocess
import threading
import time
from typing import Any, Iterator, Optional

import httpx
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

try:
    from langsmith import traceable
except ImportError:
    traceable = None

AGENTD_CLI_PROVIDER = "agentd-cli"
AGENTD_CLI_DEFAULT_MODEL = "sonnet"

COPILOT_CLI_PROVIDER = "copilot-cli"
COPILOT_CLI_DEFAULT_MODEL = "copilot"

KIMI_PROVIDER = "kimi"
KIMI_DEFAULT_MODEL = "kimi-k2.6"
KIMI_MODELS = [
    # Latest K2 models
    "kimi-k2.6",
    "kimi-k2.5",
    # Moonshot V1 auto-routing
    "moonshot-v1-auto",
    # Moonshot V1 text models
    "moonshot-v1-8k",
    "moonshot-v1-32k",
    "moonshot-v1-128k",
    # Moonshot V1 vision models
    "moonshot-v1-8k-vision-preview",
    "moonshot-v1-32k-vision-preview",
    "moonshot-v1-128k-vision-preview",
]

XIOMIMIMO_PROVIDER = "xiomimimo"
XIOMIMIMO_DEFAULT_MODEL = "mimo-v2.5-pro"
XIOMIMIMO_MODELS = [
    # Latest V2.5 series (April 2026)
    "mimo-v2.5-pro",
    "mimo-v2.5",
    # V2 series (March 2026)
    "mimo-v2-pro",
    "mimo-v2-omni",
    "mimo-v2-tts",
    # Open-weight models
    "mimo-v2-flash",
    "mimo-7b",
]

OLLAMA_PROVIDER = "ollama"
OLLAMA_DEFAULT_MODEL = "llama2"
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"
OLLAMA_COMMON_MODELS = [
    "llama2",
    "llama2:13b",
    "mistral",
    "neural-chat",
    "starling-lm",
    "dolphin-mixtral",
    "phi",
    "neural-chat:7b",
    "openhermes",
    "zephyr",
]


def add_context_to_error(
    error: Exception,
    provider: str,
    model: str,
    operation: str,
) -> Exception:
    """Wrap exception with explicit context about which provider/model/operation failed.

    Args:
        error: Original exception
        provider: Provider name
        model: Model name
        operation: What operation was being attempted

    Returns:
        RuntimeError with explicit context
    """
    base_msg = str(error) if str(error) else type(error).__name__
    context_msg = (
        f"[{provider}/{model}] {operation} failed: {base_msg}"
    )
    new_error = RuntimeError(context_msg)
    new_error.__cause__ = error
    return new_error


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

        try:
            super().__init__(**data)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize AgentDModel with model '{data.get('model', 'unknown')}': "
                f"{type(e).__name__}: {str(e)}"
            ) from e

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

    def _run_cli_traced(
        self,
        cmd: list[str],
        on_chunk: Optional[callable] = None,
    ) -> tuple[str, Optional[str]]:
        """Run Claude CLI with LangSmith tracing if enabled."""
        if traceable and os.environ.get("LANGSMITH_TRACING") == "true":
            traced = traceable(
                name=f"Claude {self.model}",
                run_type="llm",
            )(self._run_cli)
            return traced(cmd, on_chunk=on_chunk)
        return self._run_cli(cmd, on_chunk=on_chunk)

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
        full_text, _ = self._run_cli_traced(cmd)
        ai_message = AIMessage(
            content=full_text,
            usage_metadata=self.last_usage if self.last_usage else None
        )
        return ChatResult(generations=[ChatGeneration(message=ai_message)])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response (async).

        Uses asyncio.to_thread to run blocking CLI operations in a separate thread,
        completely isolating from the async event loop and blockbuster detection.
        """
        system_prompt, user_prompt = self._messages_to_prompt(messages)
        cmd = self._build_command(system_prompt, user_prompt)

        # asyncio.to_thread is cleaner than run_in_executor and avoids blockbuster issues
        full_text, _ = await asyncio.to_thread(self._run_cli_traced, cmd)

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
                self._run_cli_traced(cmd, on_chunk=on_chunk)
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
            # Use event.wait() instead of sleep to avoid blocking
            if not done.is_set():
                done.wait(timeout=0.01)

        # Don't join - let daemon thread clean up on its own
        if error_holder:
            raise error_holder[0]


class CopilotModel(AgentDModel):
    """Copilot CLI-backed model reusing AgentDModel behavior but using the 'copilot' binary."""

    model: str = COPILOT_CLI_DEFAULT_MODEL

    def __init__(self, **data):
        if "cli_binary" not in data or not data["cli_binary"]:
            # Prefer system-installed copilot, then common install locations
            candidates = [
                shutil.which("copilot"),
                shutil.which("copilot-cli"),
                "/usr/local/bin/copilot",
                "/root/.local/bin/copilot",
                "/root/.local/share/pipx/venvs/deepagents/bin/copilot",
                "/usr/bin/copilot",
            ]
            binary = next((p for p in candidates if p), "/usr/bin/copilot")
            data["cli_binary"] = binary

        try:
            super().__init__(**data)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize CopilotModel with model '{data.get('model', 'unknown')}': "
                f"{type(e).__name__}: {str(e)}"
            ) from e

    @property
    def _llm_type(self) -> str:
        return "copilot-cli"

    def _get_ls_params(self, **kwargs: Any) -> dict[str, str]:
        return {"ls_provider": COPILOT_CLI_PROVIDER, "ls_model_name": self.model}

    def _build_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        """Build the copilot CLI subprocess command (different flags than claude CLI)."""
        # Copilot CLI uses --prompt for non-interactive mode and --output-format json
        cmd = [
            self.cli_binary,
            "--output-format",
            "json",
            "--allow-all",  # Enable all permissions for non-interactive use
        ]
        if system_prompt:
            # Copilot CLI doesn't have --append-system-prompt, so we prepend to the prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
        else:
            full_prompt = user_prompt
        cmd.extend(["--prompt", full_prompt])
        return cmd

    def _run_cli(
        self,
        cmd: list[str],
        on_chunk: Optional[callable] = None,
    ) -> tuple[str, Optional[str]]:
        """Run copilot CLI and parse JSONL output format."""
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
                    f"Copilot CLI timed out after {self.call_timeout}s"
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

                # Parse copilot JSONL format
                event_type = payload.get("type", "")
                if event_type == "assistant.message_delta":
                    delta = payload.get("data", {}).get("deltaContent", "")
                    if delta:
                        text_chunks.append(delta)
                        if on_chunk:
                            on_chunk(delta)
                elif event_type == "assistant.message":
                    # Final message event with full content
                    content = payload.get("data", {}).get("content", "")
                    if content and not text_chunks:
                        text_chunks.append(content)
                elif event_type == "result":
                    # Result event with usage data
                    usage = payload.get("data", {}).get("usage", {})

        rc = process.wait()
        if rc != 0:
            stderr_text = "".join(stderr_buf).strip()
            raise RuntimeError(
                f"Copilot CLI exited with code {rc}: {stderr_text or '(no stderr)'}"
            )

        self.last_usage = usage
        return "".join(text_chunks), session_id


class OllamaModel(BaseChatModel):
    """Ollama-backed chat model for local or cloud LLMs via Ollama.

    Supports both:
    - Local Ollama: http://localhost:11434/api (set OLLAMA_BASE_URL env var)
    - Ollama Cloud: https://ollama.com/api (set OLLAMA_API_KEY env var)
    """

    model: str = OLLAMA_DEFAULT_MODEL
    base_url: str = ""  # Will be set based on api_key
    api_key: str = ""
    call_timeout: int = 300

    def __init__(self, **data):
        from agentd.auth_store import get_credential
        # Prioritize cloud API if API key is available, otherwise use local
        api_key = data.get("api_key") or get_credential("OLLAMA_API_KEY")
        if api_key:
            # Use Ollama Cloud
            data["api_key"] = api_key
            if "base_url" not in data or not data["base_url"]:
                data["base_url"] = "https://ollama.com/api"
        else:
            # Use local Ollama
            if "api_key" not in data:
                data["api_key"] = ""
            if "base_url" not in data or not data["base_url"]:
                data["base_url"] = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL)
        super().__init__(**data)

    @property
    def _llm_type(self) -> str:
        return "ollama"

    def _get_ls_params(self, **kwargs: Any) -> dict[str, str]:
        return {"ls_provider": OLLAMA_PROVIDER, "ls_model_name": self.model}

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for Ollama API (cloud or local)."""
        headers = {"Content-Type": "application/json"}
        # Cloud API requires Bearer token; local doesn't
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using Ollama API (sync).

        Uses asyncio.to_thread to avoid blocking errors in async contexts.
        """
        import asyncio
        import threading

        # Check if we're in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, use to_thread
            return asyncio.run_coroutine_threadsafe(
                self._agenerate(messages, stop, run_manager, **kwargs),
                loop,
            ).result()
        except RuntimeError:
            # No event loop, use blocking call
            return self._generate_sync(messages, stop, run_manager, **kwargs)

    def _generate_sync(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Internal sync implementation of _generate."""
        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": False,
        }

        url = f"{self.base_url.rstrip('/')}/api/chat"
        headers = self._build_headers()

        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.call_timeout,
            )
            response.raise_for_status()
            data = response.json()

            # Check for Ollama error response
            if "error" in data:
                raise RuntimeError(f"Ollama error: {data['error']}")

            content = data.get("message", {}).get("content", "")
            if not content:
                raise RuntimeError("Empty response from Ollama API")

            ai_message = AIMessage(content=content)
            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Ollama API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 404:
                raise RuntimeError(
                    f"Ollama model not found (HTTP {status}). "
                    f"Make sure the model '{self.model}' is available. "
                    f"Check your Ollama instance or cloud settings."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Ollama API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Ollama API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                raise RuntimeError(
                    f"Cannot connect to local Ollama at {self.base_url}. "
                    f"Make sure Ollama is running. Start it with: ollama serve"
                )
            else:
                raise RuntimeError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    f"Check your network connection and API key. "
                    f"Error: {str(e)[:100]}"
                )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Ollama request timed out after {self.call_timeout}s. "
                f"The model might be processing a large request or the service is slow. "
                f"Try again in a moment."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Ollama API returned invalid JSON. "
                f"The service may be experiencing issues. Error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Ollama API error: {type(e).__name__}: {str(e)[:200]}"
            )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using Ollama API (async)."""
        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": False,
        }

        url = f"{self.base_url.rstrip('/')}/api/chat"
        headers = self._build_headers()

        try:
            async with httpx.AsyncClient(timeout=self.call_timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                # Check for Ollama error response
                if "error" in data:
                    raise RuntimeError(f"Ollama error: {data['error']}")

                content = data.get("message", {}).get("content", "")
                if not content:
                    raise RuntimeError("Empty response from Ollama API")

                ai_message = AIMessage(content=content)
                return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Ollama API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 404:
                raise RuntimeError(
                    f"Ollama model not found (HTTP {status}). "
                    f"Make sure the model '{self.model}' is available. "
                    f"Check your Ollama instance or cloud settings."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Ollama API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Ollama API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                raise RuntimeError(
                    f"Cannot connect to local Ollama at {self.base_url}. "
                    f"Make sure Ollama is running. Start it with: ollama serve"
                )
            else:
                raise RuntimeError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    f"Check your network connection and API key. "
                    f"Error: {str(e)[:100]}"
                )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Ollama request timed out after {self.call_timeout}s. "
                f"The model might be processing a large request or the service is slow. "
                f"Try again in a moment."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Ollama API returned invalid JSON. "
                f"The service may be experiencing issues. Error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Ollama API error: {type(e).__name__}: {str(e)[:200]}"
            )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream response tokens from Ollama API."""
        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": True,
        }

        url = f"{self.base_url.rstrip('/')}/api/chat"
        headers = self._build_headers()

        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=self.call_timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)

                            # Check for error in stream
                            if "error" in data:
                                raise RuntimeError(f"Ollama error: {data['error']}")

                            content = data.get("message", {}).get("content", "")
                            if content:
                                chunk = ChatGenerationChunk(
                                    message=AIMessageChunk(content=content)
                                )
                                if run_manager:
                                    run_manager.on_llm_new_token(content, chunk=chunk)
                                yield chunk
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Ollama API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 404:
                raise RuntimeError(
                    f"Ollama model not found (HTTP {status}). "
                    f"Make sure the model '{self.model}' is available."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Ollama API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Ollama API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                raise RuntimeError(
                    f"Cannot connect to local Ollama at {self.base_url}. "
                    f"Make sure Ollama is running. Start it with: ollama serve"
                )
            else:
                raise RuntimeError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    f"Check your network connection. Error: {str(e)[:100]}"
                )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Ollama request timed out after {self.call_timeout}s. "
                f"The service may be slow or overloaded. Try again in a moment."
            )
        except Exception as e:
            raise RuntimeError(
                f"Ollama streaming error: {type(e).__name__}: {str(e)[:200]}"
            )

    @staticmethod
    def _convert_messages_to_dict(messages: list[BaseMessage]) -> list[dict]:
        """Convert LangChain messages to Ollama API format."""
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": str(msg.content)})
            elif isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": str(msg.content)})
        return result


class KimiModel(BaseChatModel):
    """Kimi/Moonshot API-backed chat model.

    Uses the OpenAI-compatible API at https://api.moonshot.ai/v1.
    Requires MOONSHOT_API_KEY (set via env var or ~/.deepagents/.state/auth.json).
    """

    model: str = KIMI_DEFAULT_MODEL
    base_url: str = "https://api.moonshot.ai/v1"
    api_key: str = ""
    call_timeout: int = 300

    def __init__(self, **data):
        from agentd.auth_store import get_credential
        if not data.get("api_key"):
            data["api_key"] = get_credential("MOONSHOT_API_KEY") or ""
        super().__init__(**data)

    @property
    def _llm_type(self) -> str:
        return "kimi"

    def _get_ls_params(self, **kwargs: Any) -> dict[str, str]:
        return {"ls_provider": KIMI_PROVIDER, "ls_model_name": self.model}

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for Moonshot API."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using Moonshot API (sync).

        Always uses sync implementation to avoid blocking issues in async contexts.
        """
        return self._generate_sync(messages, stop, run_manager, **kwargs)

    def _generate_sync(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Internal sync implementation of _generate."""
        if not self.api_key:
            raise RuntimeError(
                f"[kimi/{self.model}] Authentication failed: MOONSHOT_API_KEY not found. "
                f"Set it via environment variable MOONSHOT_API_KEY or use /auth command in TUI."
            )

        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": False,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers()

        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.call_timeout,
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(f"Moonshot error: {data['error']}")

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError("Empty response from Moonshot API")

            ai_message = AIMessage(content=content)
            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text[:500]
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Moonshot API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Response: {text}. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Moonshot API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Moonshot API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Moonshot API at {self.base_url}. "
                f"Check your network connection. "
                f"Error: {str(e)[:100]}"
            )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Moonshot API request timed out after {self.call_timeout}s. "
                f"The service may be slow or overloaded. Try again in a moment."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Moonshot API returned invalid JSON. "
                f"The service may be experiencing issues. Error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Moonshot API error: {type(e).__name__}: {str(e)[:200]}"
            )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using Moonshot API (async)."""
        if not self.api_key:
            raise RuntimeError(
                f"[kimi/{self.model}] Authentication failed: MOONSHOT_API_KEY not found. "
                f"Set it via environment variable MOONSHOT_API_KEY or use /auth command in TUI."
            )

        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": False,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers()

        try:
            async with httpx.AsyncClient(timeout=self.call_timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    raise RuntimeError(f"Moonshot error: {data['error']}")

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    raise RuntimeError("Empty response from Moonshot API")

                ai_message = AIMessage(content=content)
                return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text[:500]  # Limit to first 500 chars for debugging
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Moonshot API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Response: {text}. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Moonshot API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Moonshot API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Moonshot API. "
                f"Check your network connection. "
                f"Error: {str(e)[:100]}"
            )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Moonshot API request timed out after {self.call_timeout}s. "
                f"The service may be slow or overloaded. Try again in a moment."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Moonshot API returned invalid JSON. "
                f"The service may be experiencing issues. Error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Moonshot API error: {type(e).__name__}: {str(e)[:200]}"
            )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream response tokens from Moonshot API."""
        if not self.api_key:
            raise RuntimeError(
                f"[kimi/{self.model}] Authentication failed: MOONSHOT_API_KEY not found. "
                f"Set it via environment variable MOONSHOT_API_KEY or use /auth command in TUI."
            )

        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": True,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers()

        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=self.call_timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip():
                        try:
                            if line.startswith("data: "):
                                line = line[6:]
                            if line.strip() == "[DONE]":
                                break
                            data = json.loads(line)

                            if "error" in data:
                                raise RuntimeError(f"Moonshot error: {data['error']}")

                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                chunk = ChatGenerationChunk(
                                    message=AIMessageChunk(content=content)
                                )
                                if run_manager:
                                    run_manager.on_llm_new_token(content, chunk=chunk)
                                yield chunk
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text[:500]  # Limit to first 500 chars for debugging
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Moonshot API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Response: {text}. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Moonshot API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Moonshot API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Moonshot API. "
                f"Check your network connection. "
                f"Error: {str(e)[:100]}"
            )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Moonshot API request timed out after {self.call_timeout}s. "
                f"The service may be slow or overloaded. Try again in a moment."
            )
        except Exception as e:
            raise RuntimeError(
                f"Moonshot streaming error: {type(e).__name__}: {str(e)[:200]}"
            )

    @staticmethod
    def _convert_messages_to_dict(messages: list[BaseMessage]) -> list[dict]:
        """Convert LangChain messages to OpenAI-compatible format."""
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": str(msg.content)})
            elif isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": str(msg.content)})
        return result


class XiaomiModel(BaseChatModel):
    """Xiaomi MiMo API-backed chat model.

    Uses the OpenAI-compatible API at https://api.xiaomimimo.com/v1.
    Requires XIOMIMIMO_API_KEY (set via env var or ~/.deepagents/.state/auth.json).
    """

    model: str = XIOMIMIMO_DEFAULT_MODEL
    base_url: str = "https://api.xiaomimimo.com/v1"
    api_key: str = ""
    call_timeout: int = 300

    def __init__(self, **data):
        from agentd.auth_store import get_credential
        if not data.get("api_key"):
            data["api_key"] = get_credential("XIOMIMIMO_API_KEY") or ""
        super().__init__(**data)

    @property
    def _llm_type(self) -> str:
        return "xiaomi"

    def _get_ls_params(self, **kwargs: Any) -> dict[str, str]:
        return {"ls_provider": XIOMIMIMO_PROVIDER, "ls_model_name": self.model}

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for Xiaomi API."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using Xiaomi API (sync).

        Always uses sync implementation to avoid blocking issues in async contexts.
        """
        return self._generate_sync(messages, stop, run_manager, **kwargs)

    def _generate_sync(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Internal sync implementation of _generate."""
        if not self.api_key:
            raise RuntimeError(
                f"[xiomimimo/{self.model}] Authentication failed: XIOMIMIMO_API_KEY not found. "
                f"Set it via environment variable XIOMIMIMO_API_KEY or use /auth command in TUI."
            )

        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": False,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers()

        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.call_timeout,
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(f"Xiaomi error: {data['error']}")

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError("Empty response from Xiaomi API")

            ai_message = AIMessage(content=content)
            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Xiaomi API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Xiaomi API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Xiaomi API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Xiaomi API at {self.base_url}. "
                f"Check your network connection. "
                f"Error: {str(e)[:100]}"
            )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Xiaomi API request timed out after {self.call_timeout}s. "
                f"The service may be slow or overloaded. Try again in a moment."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Xiaomi API returned invalid JSON. "
                f"The service may be experiencing issues. Error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Xiaomi API error: {type(e).__name__}: {str(e)[:200]}"
            )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using Xiaomi API (async)."""
        if not self.api_key:
            raise RuntimeError(
                f"[xiomimimo/{self.model}] Authentication failed: XIOMIMIMO_API_KEY not found. "
                f"Set it via environment variable XIOMIMIMO_API_KEY or use /auth command in TUI."
            )

        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": False,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers()

        try:
            async with httpx.AsyncClient(timeout=self.call_timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    raise RuntimeError(f"Xiaomi error: {data['error']}")

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    raise RuntimeError("Empty response from Xiaomi API")

                ai_message = AIMessage(content=content)
                return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Xiaomi API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Xiaomi API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Xiaomi API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Xiaomi API. "
                f"Check your network connection. "
                f"Error: {str(e)[:100]}"
            )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Xiaomi API request timed out after {self.call_timeout}s. "
                f"The service may be slow or overloaded. Try again in a moment."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Xiaomi API returned invalid JSON. "
                f"The service may be experiencing issues. Error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Xiaomi API error: {type(e).__name__}: {str(e)[:200]}"
            )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream response tokens from Xiaomi API."""
        if not self.api_key:
            raise RuntimeError(
                f"[xiomimimo/{self.model}] Authentication failed: XIOMIMIMO_API_KEY not found. "
                f"Set it via environment variable XIOMIMIMO_API_KEY or use /auth command in TUI."
            )

        messages_dicts = self._convert_messages_to_dict(messages)

        payload = {
            "model": self.model,
            "messages": messages_dicts,
            "stream": True,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers()

        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=self.call_timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip():
                        try:
                            if line.startswith("data: "):
                                line = line[6:]
                            if line.strip() == "[DONE]":
                                break
                            data = json.loads(line)

                            if "error" in data:
                                raise RuntimeError(f"Xiaomi error: {data['error']}")

                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                chunk = ChatGenerationChunk(
                                    message=AIMessageChunk(content=content)
                                )
                                if run_manager:
                                    run_manager.on_llm_new_token(content, chunk=chunk)
                                yield chunk
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text
            if status == 401 or status == 403:
                raise RuntimeError(
                    f"Xiaomi API authentication failed (HTTP {status}). "
                    f"Your API key may be invalid or expired. "
                    f"Run '/auth' in TUI to update your credentials."
                )
            elif status == 429:
                raise RuntimeError(
                    f"Xiaomi API rate limit exceeded (HTTP {status}). "
                    f"Please wait a moment and try again."
                )
            else:
                raise RuntimeError(
                    f"Xiaomi API error (HTTP {status}): {text}"
                )
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Xiaomi API. "
                f"Check your network connection. "
                f"Error: {str(e)[:100]}"
            )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                f"Xiaomi API request timed out after {self.call_timeout}s. "
                f"The service may be slow or overloaded. Try again in a moment."
            )
        except Exception as e:
            raise RuntimeError(
                f"Xiaomi streaming error: {type(e).__name__}: {str(e)[:200]}"
            )

    @staticmethod
    def _convert_messages_to_dict(messages: list[BaseMessage]) -> list[dict]:
        """Convert LangChain messages to OpenAI-compatible format."""
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": str(msg.content)})
            elif isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": str(msg.content)})
        return result


def get_ollama_models() -> list[tuple[str, str]]:
    """Fetch available models from Ollama cloud or local instance.

    Priority:
    1. Ollama Cloud (https://ollama.com/api) with OLLAMA_API_KEY
    2. Local Ollama (http://localhost:11434/api)
    3. Default fallback model

    OLLAMA_API_KEY can be set via:
    - Environment variable: export OLLAMA_API_KEY=...
    - TUI /auth command: stores in ~/.deepagents/.state/auth.json
    """
    from agentd.auth_store import get_credential
    models = []
    api_key = get_credential("OLLAMA_API_KEY")

    # Try Ollama Cloud first (default)
    if api_key:
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = httpx.get(
                "https://ollama.com/api/tags",
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            for model in data.get("models", []):
                model_id = model.get("name", "")
                if model_id:
                    models.append((model_id, f"Ollama Cloud: {model_id}"))
            if models:
                return models
        except Exception:
            pass

    # Fallback to local Ollama instance
    base_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL)
    try:
        response = httpx.get(
            f"{base_url.rstrip('/')}/api/tags",
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        for model in data.get("models", []):
            model_id = model.get("name", "")
            if model_id:
                models.append((model_id, f"Ollama: {model_id}"))
        if models:
            return models
    except Exception:
        pass

    # Fallback to default model
    return [(OLLAMA_DEFAULT_MODEL, f"Ollama: {OLLAMA_DEFAULT_MODEL}")]


# Register models with the runtime registry so TUI/clients can discover them
try:
    from agentd.model_registry import register_model

    # Claude models via AgentD CLI (expensive)
    register_model("sonnet", AGENTD_CLI_PROVIDER, display="Claude Sonnet",
                   description="Balanced speed & intelligence. Best for most tasks.", cost_tier=4, default_model=AGENTD_CLI_DEFAULT_MODEL)
    register_model("opus", AGENTD_CLI_PROVIDER, display="Claude Opus",
                   description="Most capable. Best for complex reasoning & analysis.", cost_tier=5)
    register_model("haiku", AGENTD_CLI_PROVIDER, display="Claude Haiku",
                   description="Fastest & most compact. Best for real-time interactions.", cost_tier=3)

    # Copilot CLI (moderate cost)
    register_model("copilot", COPILOT_CLI_PROVIDER, display="Copilot CLI",
                   description="GitHub Copilot integration. Code-focused assistance.", cost_tier=3, default_model=COPILOT_CLI_DEFAULT_MODEL)

    # Kimi/Moonshot models (latest first)
    register_model("kimi-k2.6", KIMI_PROVIDER, display="Kimi K2.6 (Latest)",
                   description="Latest multimodal model. 256k context. Best reasoning & vision.", cost_tier=4, default_model=KIMI_DEFAULT_MODEL)
    register_model("kimi-k2.5", KIMI_PROVIDER, display="Kimi K2.5",
                   description="Multimodal model. 256k context. Strong across coding & vision.", cost_tier=4)
    register_model("moonshot-v1-auto", KIMI_PROVIDER, display="Moonshot V1 Auto",
                   description="Auto-routing. Moonshot selects best model for your task.", cost_tier=3)
    register_model("moonshot-v1-8k", KIMI_PROVIDER, display="Moonshot V1 8k",
                   description="8k context window. Balanced performance and cost.", cost_tier=3)
    register_model("moonshot-v1-32k", KIMI_PROVIDER, display="Moonshot V1 32k",
                   description="32k context window. Better for longer documents.", cost_tier=3)
    register_model("moonshot-v1-128k", KIMI_PROVIDER, display="Moonshot V1 128k",
                   description="128k context window. Best for very long conversations.", cost_tier=3)
    register_model("moonshot-v1-8k-vision-preview", KIMI_PROVIDER, display="Moonshot V1 8k Vision",
                   description="Vision-capable. Analyzes images and text. 8k context.", cost_tier=3)
    register_model("moonshot-v1-32k-vision-preview", KIMI_PROVIDER, display="Moonshot V1 32k Vision",
                   description="Vision-capable. Analyzes images and text. 32k context.", cost_tier=3)
    register_model("moonshot-v1-128k-vision-preview", KIMI_PROVIDER, display="Moonshot V1 128k Vision",
                   description="Vision-capable. Analyzes images and text. 128k context.", cost_tier=3)

    # Xiaomi MiMo models (sorted: cheapest to most expensive)
    # Open-weight models - cheapest
    register_model("mimo-v2-flash", XIOMIMIMO_PROVIDER, display="Xiaomi MiMo V2 Flash (Open)",
                   description="Open-weight model. MIT license. Fast inference.", cost_tier=1)
    register_model("mimo-7b", XIOMIMIMO_PROVIDER, display="Xiaomi MiMo 7B (Open)",
                   description="Compact 7B parameter model. Open-source & lightweight.", cost_tier=1)
    # V2 series (March 2026) - cheaper
    register_model("mimo-v2.5", XIOMIMIMO_PROVIDER, display="Xiaomi MiMo V2.5",
                   description="General-purpose V2.5. Strong performance & cost-effective.", cost_tier=2)
    register_model("mimo-v2-pro", XIOMIMIMO_PROVIDER, display="Xiaomi MiMo V2 Pro (Reasoning)",
                   description="Specialized for reasoning tasks & agent workflows. High quality outputs.", cost_tier=2)
    register_model("mimo-v2-omni", XIOMIMIMO_PROVIDER, display="Xiaomi MiMo V2 Omni (Multimodal)",
                   description="Full multimodal support. Text & image understanding.", cost_tier=2)
    register_model("mimo-v2-tts", XIOMIMIMO_PROVIDER, display="Xiaomi MiMo V2 TTS (Speech)",
                   description="Text-to-speech synthesis. Audio generation from text.", cost_tier=2)
    # V2.5 series (April 2026) - moderate cost
    register_model("mimo-v2.5-pro", XIOMIMIMO_PROVIDER, display="Xiaomi MiMo V2.5 Pro",
                   description="Latest professional model. Matches frontier benchmarks at lower cost.", cost_tier=3, default_model=XIOMIMIMO_DEFAULT_MODEL)

    # Register Ollama models (always register common models, add dynamic ones if available)
    registered_ollama = set()

    # Always register common Ollama models with descriptions
    ollama_descriptions = {
        "llama2": "Meta's flagship open model. Balanced & reliable.",
        "llama2:13b": "13B version of Llama2. Smaller footprint.",
        "mistral": "Mistral 7B. Fast & efficient. Great for real-time.",
        "neural-chat": "Intel's optimized chat model. Good for conversations.",
        "starling-lm": "Chat-optimized model. High quality responses.",
        "dolphin-mixtral": "Uncensored MoE model. Mixture of Experts.",
        "phi": "Microsoft's 2.7B model. Small & capable.",
        "neural-chat:7b": "7B variant. Optimized for chat tasks.",
        "openhermes": "Open Hermes 2.5. Strong reasoning & coding.",
        "zephyr": "Aligned chat model. Well-behaved & helpful.",
    }

    for model_id in OLLAMA_COMMON_MODELS:
        register_model(
            model_id,
            OLLAMA_PROVIDER,
            display=f"Ollama: {model_id}",
            description=ollama_descriptions.get(model_id, "Local open-source model."),
            cost_tier=1,  # Ollama local models are free
            default_model=model_id == OLLAMA_DEFAULT_MODEL
        )
        registered_ollama.add(model_id)

    # Try to fetch and register any additional models available on the running Ollama instance
    try:
        ollama_models = get_ollama_models()
        for model_id, display_name in ollama_models:
            if model_id not in registered_ollama:
                # Cloud models are cheaper than dedicated APIs
                cost_tier = 2 if "cloud" in display_name.lower() else 1
                register_model(
                    model_id,
                    OLLAMA_PROVIDER,
                    display=display_name,
                    description="Available from Ollama Cloud or local instance.",
                    cost_tier=cost_tier,
                )
    except Exception:
        # Ollama might not be available, that's OK - we already registered the common models
        pass

except Exception:
    # If registry is not available (older installs), silently skip registration
    pass
