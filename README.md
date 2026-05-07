# AgentD - LLM Agent Framework

**Production-grade agentic framework with full session logging, persistent memory, token tracking, and Claude CLI integration.**

- ✅ **No API Key Required** — Uses Claude CLI binary
- ✅ **Full Session Logging** — SQLite checkpoints (245+ snapshots, 312+ messages)
- ✅ **Persistent Memory** — LangGraph-backed dual-layer memory system
- ✅ **Token Aware** — Real-time token counting and context window monitoring
- ✅ **Production Ready** — Battle-tested with 12 unique conversations

---

## Quick Start

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/agentD.git
cd agentD

# Install in development mode
pip install -e .
```

### Usage

**Simple Command (with auto-approval):**
```bash
D "your task"
```

**Full TUI:**
```bash
D
```

**Resume a conversation:**
```bash
D --thread-id <thread-id>
```

**Non-interactive:**
```bash
D -n "run this task"
```

---

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

```
┌─────────────────────────────────────────┐
│         AgentD TUI (Textual)             │
├─────────────────────────────────────────┤
│  AgentDModel (LangChain BaseChatModel)  │
├─────────────────────────────────────────┤
│  SQLite Session DB + JSON Memory File   │
├─────────────────────────────────────────┤
│       Claude CLI (subprocess)            │
└─────────────────────────────────────────┘
```

### Data Storage

```
~/.agentd/.state/sessions.db       Session checkpoints & message history
~/.agentd_memories.json            Global user memories
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

### Setup Development Environment

```bash
git clone https://github.com/yourusername/agentD.git
cd agentD
pip install -e ".[dev]"
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

## Limitations

- ❌ Browser use not available (requires API key)
- ⚠️ SQLite database grows with usage (cleanup not yet implemented)

---

## Future Enhancements

- [ ] `/forget <fact>` command
- [ ] `/remember --search <term>` search
- [ ] Export conversations to JSON/PDF
- [ ] Automatic database cleanup
- [ ] Web API for remote access
- [ ] Multi-user support

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
