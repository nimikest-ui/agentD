# Agent Instructions

All agent guidance for this repository — including the GitNexus code-intelligence
workflow (impact analysis before edits, `detect_changes` before commits, etc.) — lives
in **[CLAUDE.md](CLAUDE.md)**, the single source of truth.

Please read [CLAUDE.md](CLAUDE.md).

## Setup

```bash
pip install -e ".[dev]"        # Dev install (editable, with dev deps)
playwright install chromium     # Browser automation
```

## Dev Commands

```bash
pytest tests/                   # Run tests
ruff check .                    # Lint (default config)
black .                         # Format (default config)
python -m build                 # Build distribution
```

- `ruff` and `black` have no config files — they run with defaults
- `asyncio_mode = "auto"` is set in `pyproject.toml`; async tests auto-detected
- Tests must run from package root, not inside `tests/`

## Architecture

**Entrypoints:**
- `D` → `agentd.cli:main_d` — TUI shortcut, auto-inserts `--auto-approve`
- `agentd` → `agentd.cli:main` — standard CLI

**Core flow:**
```
cli.py → core.py (Agent) → graph.py (StateGraph) → models.py (provider detection)
```

**Key files:**
| File | Purpose |
|------|---------|
| `agentd/cli.py` | CLI entrypoints, TUI engine discovery, voice bridge launch |
| `agentd/core.py` | `Agent` class — LangGraph graph wrapper with invoke/stream |
| `agentd/graph.py` | `StateGraph` definition with single LLM node, memory injection |
| `agentd/models.py` | 5 model classes: AgentDModel (Claude CLI), CopilotModel, OllamaModel, KimiModel, XiaomiModel |
| `agentd/memory.py` | Two-layer memory: global JSON file + thread-scoped LangGraph state |
| `agentd/persistence.py` | SQLite checkpointer + InMemoryStore factories |
| `agentd/browser_tools.py` | Browser-use + Firecrawl web research integration |
| `agentd/mcp_server.py` | MCP server exposing browser/scrape/search tools |
| `agentd/tracing.py` | LangSmith tracing configuration |

## Conventions & Quirks

- **Circular imports**: `graph.py` imports from `core.py` inside function bodies. Never move these to module level.
- **Lazy credential loading**: Model objects construct without API keys; keys load at call time. Don't add eager validation.
- **No `conftest.py`**: Fixtures are defined locally in test files. New test files need their own fixtures.
- **`D` command auto-inserts `--auto-approve`**: This is by design for the shortcut command.
- **No lint config files**: `ruff` and `black` run with defaults. No `[tool.ruff]` or `[tool.black]` in pyproject.toml.

## Environment Variables

**Core:**
- `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT` — LangSmith tracing
- `ANTHROPIC_API_KEY` — optional, for Anthropic SDK wrapper

**Provider-specific:**
- `MOONSHOT_API_KEY` — Kimi/Moonshot
- `XIOMIMIMO_API_KEY` — Xiaomi MiMo
- `OLLAMA_BASE_URL`, `OLLAMA_API_KEY` — Ollama
- `FIRECRAWL_API_KEY` — Firecrawl web scraping

**Override:**
- `AGENTD_PROVIDER` — forces provider selection (bypasses auto-detection)

**Credential resolution order:** env var first, then `~/.deepagents/.state/auth.json`

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **agentD** (1138 symbols, 1832 relationships, 52 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/agentD/context` | Codebase overview, check index freshness |
| `gitnexus://repo/agentD/clusters` | All functional areas |
| `gitnexus://repo/agentD/processes` | All execution flows |
| `gitnexus://repo/agentD/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
