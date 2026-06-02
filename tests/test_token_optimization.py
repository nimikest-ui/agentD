"""Tests for the Claude-path token-reduction work.

Scope guard: these assert the optimizations apply ONLY to the Claude
(``agentd-cli``) path and that the build-command/session-reuse behaviour is
correct. The non-Claude providers must keep the original ``ainvoke(messages)``
path untouched.
"""

import asyncio

from langchain_core.messages import AIMessage, HumanMessage


# --------------------------------------------------------------------------- #
# Model defaults                                                              #
# --------------------------------------------------------------------------- #
class TestDefaults:
    def test_default_model_is_haiku(self):
        from agentd.models import AGENTD_CLI_DEFAULT_MODEL, AgentDModel
        assert AGENTD_CLI_DEFAULT_MODEL == "haiku"
        assert AgentDModel().model == "haiku"


# --------------------------------------------------------------------------- #
# _build_command shape (Change 2 + 3)                                         #
# --------------------------------------------------------------------------- #
class TestBuildCommand:
    def _model(self, **kw):
        from agentd.models import AgentDModel
        return AgentDModel(model="haiku", **kw)

    def test_tools_restricted_to_bash(self):
        cmd = self._model()._build_command("sys", "hello")
        assert "--tools" in cmd
        assert cmd[cmd.index("--tools") + 1] == "Bash"
        # the old, wasteful "--tools default" must be gone
        assert "default" not in cmd

    def test_resume_adds_flag_and_drops_system_prompt(self):
        cmd = self._model()._build_command("sysprompt", "hello", resume_session_id="sess-abc")
        assert "--resume" in cmd
        assert cmd[cmd.index("--resume") + 1] == "sess-abc"
        assert "--append-system-prompt" not in cmd

    def test_no_resume_keeps_system_prompt(self):
        cmd = self._model()._build_command("sysprompt", "hello")
        assert "--append-system-prompt" in cmd
        assert "--resume" not in cmd

    def test_budget_off_by_default(self):
        assert "--max-budget-usd" not in self._model()._build_command("", "hi")

    def test_budget_flag_when_configured(self):
        cmd = self._model(max_budget_usd=0.5)._build_command("", "hi")
        assert "--max-budget-usd" in cmd
        assert cmd[cmd.index("--max-budget-usd") + 1] == "0.5"


# --------------------------------------------------------------------------- #
# Graph node: Claude resume vs. untouched non-Claude path (Change 3)          #
# --------------------------------------------------------------------------- #
class _StubResponse:
    def __init__(self, content, session_id=None):
        self.content = content
        self.response_metadata = {"session_id": session_id} if session_id else {}


class _StubModel:
    """Minimal stand-in for a chat model; records how it was invoked."""

    def __init__(self, llm_type, session_id=None):
        self._llm_type = llm_type
        self._session_id = session_id
        self.calls = []  # list of (messages, kwargs)

    async def ainvoke(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return _StubResponse("ok", self._session_id)


def _node_with_stub(monkeypatch, stub):
    import agentd.core
    import agentd.graph
    monkeypatch.setattr(agentd.core.Agent, "_create_model", staticmethod(lambda *a, **k: stub))
    return agentd.graph._make_llm_node("haiku")


class TestLlmNode:
    def test_non_claude_path_untouched(self, monkeypatch):
        stub = _StubModel("xiomimimo")  # e.g. Xiaomi mimo — NOT the Claude path
        node = _node_with_stub(monkeypatch, stub)
        out = asyncio.run(node({"messages": [HumanMessage("hi")], "_thread_memories": []}))
        msgs, kwargs = stub.calls[0]
        # no resume kwarg, no session id written — original behaviour preserved
        assert "resume_session_id" not in kwargs
        assert "_claude_session_id" not in out

    def test_claude_first_turn_captures_session(self, monkeypatch):
        stub = _StubModel("agentd-cli", session_id="sess-123")
        node = _node_with_stub(monkeypatch, stub)
        out = asyncio.run(node({"messages": [HumanMessage("first")], "_thread_memories": []}))
        _, kwargs = stub.calls[0]
        assert "resume_session_id" not in kwargs  # first turn sends full prompt
        assert out["_claude_session_id"] == "sess-123"

    def test_claude_second_turn_resumes_with_latest_human_only(self, monkeypatch):
        stub = _StubModel("agentd-cli", session_id="sess-123")
        node = _node_with_stub(monkeypatch, stub)
        state = {
            "messages": [HumanMessage("first"), AIMessage("ok"), HumanMessage("second")],
            "_thread_memories": [],
            "_claude_session_id": "sess-123",
        }
        asyncio.run(node(state))
        msgs, kwargs = stub.calls[0]
        assert kwargs.get("resume_session_id") == "sess-123"
        # only the newest human turn is re-sent, not the whole history
        humans = [m for m in msgs if isinstance(m, HumanMessage)]
        assert len(humans) == 1 and humans[0].content == "second"


# --------------------------------------------------------------------------- #
# Pentester skill: 6 calls -> 1 (Change 4)                                    #
# --------------------------------------------------------------------------- #
class TestPentesterConsolidation:
    def test_split_sections_parses_markers(self):
        from agentd.pentester_skill import PentesterSkill
        raw = "===SECTION=== Alpha\nbody a\n===SECTION=== Beta\nbody b"
        out = PentesterSkill._split_sections(raw, ["Alpha", "Beta"], "===SECTION===")
        assert out["Alpha"] == "body a"
        assert out["Beta"] == "body b"

    def test_split_sections_fallback_keeps_text(self):
        from agentd.pentester_skill import PentesterSkill
        out = PentesterSkill._split_sections("no markers", ["Alpha"], "===SECTION===")
        assert out["Alpha"] == "no markers"

    def test_threat_research_makes_single_call(self, monkeypatch):
        from agentd.pentester_skill import PentesterSkill
        skill = PentesterSkill()
        calls = []

        def fake_run_claude(prompt, model="haiku"):
            calls.append((prompt, model))
            return "===SECTION=== Current CVEs & Vulnerabilities\nx\n===SECTION=== Remediation\ny"

        monkeypatch.setattr(skill, "run_claude", fake_run_claude)
        findings = skill.threat_research("test topic")
        assert len(calls) == 1  # was 5 separate CLI sessions
        assert findings["type"] == "threat_intelligence"
        assert findings["topic"] == "test topic"
        assert findings["phases"]  # populated from the single response
