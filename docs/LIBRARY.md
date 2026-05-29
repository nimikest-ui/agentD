# AgentD - Library Installation & Usage

## Installation

### From Source (Development)

```bash
git clone https://github.com/yourusername/agentD.git
cd agentD
pip install -e .
```

This installs two commands:
- `D` — Quick shortcut (auto-approve all, full TUI)
- `agentd` — Full command with options

### PyPI (When Published)

```bash
pip install agentD
```

---

## Quick Commands

### The `D` Shortcut (Recommended)

**Simplest way to use AgentD** — auto-approves all, full TUI with everything enabled.

```bash
# Open TUI
D

# Run a task
D "fix the bug in main.py"

# Resume a conversation
D --thread-id 019dff9a-8e29-72c1-9abc
```

### Full `agentd` Command

For more control:

```bash
agentd -M claude-cli -S all                    # Full TUI
agentd -n "your task" -M claude-cli -S all     # Non-interactive
agentd --thread-id <id> -M claude-cli -S all   # Resume specific
```

---

## Usage Examples

### Example 1: Quick Task
```bash
D "write a python function to reverse a list"
```
→ Runs task, auto-approves all tool calls, returns result

### Example 2: Interactive Session
```bash
D
```
→ Opens TUI, type prompts, use `/tokens`, `/remember`, `/threads`, etc.

### Example 3: Resume Previous Conversation
```bash
D --thread-id 019dff9a-8e29-72c1-9
```
→ Restores full conversation history, memories, and context

### Example 4: With Different Model
```bash
D -M haiku "quick summary"
D -M opus "complex reasoning task"
```

---

## In-TUI Commands

Once you open `D` or `agentd`, you can use:

```
/tokens              Show token usage (input/output/context window)
/remember <fact>     Save a global memory fact
/remember            List all stored memories
/threads             View all conversations
--thread-id <id>     Resume that thread
/trace               See step-by-step execution details
/model <name>        Switch models
/help                Show available commands
```

---

## What AgentD Does

### 1. **Session Logging**
Every conversation is automatically logged to `~/.agentd/.state/sessions.db`:
- Full message history
- State snapshots after each turn
- Token counts
- Complete transcript

Resume any conversation: `D --thread-id <id>`

### 2. **Persistent Memory**
Save facts that persist across conversations:
```bash
D
# /remember I prefer Python 3.11+ syntax
# /remember Always verify output
# Exit and restart...
D
# /remember   ← Shows saved facts
```

### 3. **Token Counting**
Monitor your context window:
```bash
D
# (In TUI) /tokens
# Shows: 2,345 / 200,000 tokens (1%)
```

### 4. **No API Key Required**
AgentD uses only the Claude CLI binary. No Anthropic API key needed:
```bash
export ANTHROPIC_API_KEY=""
D "this still works!"
```

---

## File Locations

```
~/.agentd/.state/sessions.db      All session checkpoints and messages
~/.agentd_memories.json           Global persistent memories
```

---

## For Developers

### Extend AgentD

Add custom models or tools:

```python
from agentd.models import AgentDModel

class CustomModel(AgentDModel):
    def _run_cli(self, cmd, on_chunk=None):
        # Your custom logic
        return super()._run_cli(cmd, on_chunk)
```

### Use in Your Code

```python
from agentd import Agent

agent = Agent(model="sonnet")
# Now use via subprocess or extend further
```

---

## Troubleshooting

### `D` command not found
Make sure you're in the venv:
```bash
source venv/bin/activate
D
```

### Sessions not resuming
Check thread ID matches:
```bash
D --thread-id 019dff9a-8e29-72c1-9
```
Use exact ID from `/threads`

### Token counts not showing
Run a task first, then check:
```bash
D "hello"
# /tokens   ← Now shows data
```

---

## Architecture

```
User Command (D)
    ↓
agentd.cli.main_d()
    ↓
TUI Engine (deepagents backend)
    ↓
AgentDModel (LangChain wrapper)
    ↓
Claude CLI subprocess
    ↓
LangGraph checkpoints & JSON memory
```

---

## Configuration

AgentD is zero-config. Everything works out of the box.

Optional: Set a custom default model:
```bash
export AGENTD_DEFAULT_MODEL=haiku
D "quick task"
```

---

## Next Steps

1. **Install**: `pip install -e .`
2. **Run**: `D "your task"`
3. **Explore**: `D` then `/threads` and `/tokens`
4. **Save memories**: `/remember important facts`
5. **Resume**: `D --thread-id <id>`

---

## Documentation

See the [project README](../README.md) for the full documentation index.

---

**AgentD** — Production-grade LLM agents. No API key. Full session logging.
