# agentD

**agentD** is a TUI-first AI agent built by merging two projects:

- **[deepagents](https://docs.langchain.com/oss/python/deepagents/overview)** — the terminal UI, threading, session management, and skill system
- **ForestGump** — a bare-metal shell agent with PTY execution, persistent memory, and learned techniques

The result is a production-grade pentesting and research agent that runs in your terminal, requires no API key, and remembers everything across sessions.

```
┌─────────────────────────────────────────────────────┐
│              deepagents TUI (terminal UI)             │
│         threads · sessions · skills · models          │
├─────────────────────────────────────────────────────┤
│           agentD library (this repo)                  │
│   LangGraph graph · memory · browser · MCP server     │
├─────────────────────────────────────────────────────┤
│          ForestGump execution engine                  │
│     PTY shell · safety guards · technique memory      │
├─────────────────────────────────────────────────────┤
│    Claude CLI / Ollama / Kimi / Anthropic API         │
└─────────────────────────────────────────────────────┘
```

- **No API key required** — defaults to Claude CLI (OAuth)
- **Persistent memory** — facts, credentials, techniques survive restarts
- **Browser automation** — Playwright + browser-use built in
- **Security skills** — pentest-workflow, bug-bounty-toolkit, deep-research
- **Multi-model** — Claude, Ollama (local), Kimi, XiaoMi MiMo, Copilot

---

## Quick Start

```bash
git clone https://github.com/yourusername/agentD.git
cd agentD
bash setup.sh                   # creates venv, installs everything, downloads Chromium
source venv/bin/activate
D                               # launch TUI
```

### Usage

```bash
D                               # Full interactive TUI
D --bare                        # Bare-metal shell agent (ForestGump mode)
D -n "your task"                # Non-interactive single task
D -M haiku "quick question"     # Use a specific model
D -r                            # Resume last conversation
D --thread-id <id>              # Resume specific thread
```

---

## Ollama (local models)

```bash
ollama serve
D -M llama2 "solve this"
D -M mistral -n "write code"
```

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for details.

## Features

### 1. Token Counting
```
/tokens      # Show input/output tokens and context window usage
```

### 2. Persistent Memory
```
/remember I prefer detailed explanations      # Save global memory
/remember                                      # List all memories
```

### 3. Session Management
```
/threads                                       # View all conversations
--thread-id <id>                              # Resume specific thread
```

### 4. Execution Tracing
```
/trace                                         # See step-by-step execution
```

---

## Architecture

agentD is the library layer between deepagents (TUI) and your LLM:

```
deepagents TUI  →  agentd/cli.py  →  agentd/core.py (Agent)
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                   ▼
                  agentd/graph.py   agentd/models.py   agentd/browser_tools.py
                  (LangGraph)       (LLM providers)    (Playwright)
                        │
                  agentd/memory.py + agentd/session_logger.py
                  (persistent state across sessions)
```

### Data Storage

```
~/.deepagents/.state/sessions.db   Session checkpoints & message history
~/.deepagents/.state/auth.json     API credentials
```

---

## Command Reference

### TUI Commands

| Command | Purpose |
|---------|---------|
| `/tokens` | Show token usage |
| `/remember <fact>` | Save memory |
| `/remember` | List memories |
| `/threads` | View all conversations |
| `--thread-id <id>` | Resume thread |
| `/trace` | Execution details |
| `/model <name>` | Switch model |

### CLI Shortcuts

```bash
D                                # Full TUI (auto-approve)
D "task"                         # Run task
D -n "task"                      # Non-interactive
D --thread-id <id>              # Resume
D --auto-approve                # Enable all approvals
D -M haiku "task"               # Use haiku model
D -M opus "task"                # Use opus model
```

---

## Session Logging

AgentD logs everything automatically to SQLite:

- **245+ Checkpoints** — State snapshots after each turn
- **312+ Messages** — Complete conversation history
- **12+ Threads** — Separate conversations stored
- **3.5 MB** — All data persisted to disk

Resume any conversation without losing context.

---

## Memory System (LangGraph-Backed)

### Two Layers

**Global** (`~/.agentd_memories.json`)
- Shared across all threads
- Survives app restarts
- Use for: preferences, defaults

**Thread-Scoped** (LangGraph state)
- Unique per conversation
- Survives within thread
- Use for: conversation decisions

Both automatically injected into system prompts.

---

## No API Key Required

AgentD uses the Claude CLI binary exclusively. No Anthropic API key needed.

```bash
# This works with just the CLI
D "solve this problem"
```

---

## File Structure

```
agentD/
├── agentd/
│   ├── __init__.py           # Package init
│   ├── cli.py                # CLI entry point (D command)
│   ├── core.py               # Agent class
│   ├── models.py             # AgentDModel (Claude CLI wrapper)
│   └── memory.py             # Memory system
├── setup.py                  # Package config
└── README.md                 # This file
```

---

## Development

```bash
git clone https://github.com/yourusername/agentD.git
cd agentD
bash setup.sh          # handles venv + pip install -e .[dev] + playwright
```

### Run Tests

```bash
pytest tests/
```

---

## Documentation

See documentation files for detailed information:

- `SESSION_LOGGING_ARCHITECTURE.md` — Full session logging details
- `LANGGRAPH_MEMORY_INTEGRATION.md` — Memory system architecture
- `OPTIMIZATION_SUMMARY.md` — 4 core optimizations
- `QUICK_REFERENCE.md` — Quick usage guide

---

---

## License

MIT

---

## Contributing

Pull requests welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

---

## Support

Issues and questions: [GitHub Issues](https://github.com/yourusername/agentD/issues)

---

**AgentD** — Production-grade LLM agents with full session logging.

Ready for deployment. No API key required. ✅
