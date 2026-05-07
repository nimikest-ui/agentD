# AgentD / DeepAgents - Complete Slash Commands Reference

**All available commands in the TUI (Terminal User Interface)**

---

## Quick Reference Table

| Command | Purpose | Example |
|---------|---------|---------|
| `/help` | Show all commands | `/help` |
| `/quit` | Exit application | `/quit` |
| `/clear` | Clear conversation | `/clear` |
| `/tokens` | Show token usage | `/tokens` |
| `/remember [fact]` | Save memory | `/remember I prefer Python` |
| `/threads` | List conversations | `/threads` |
| `/trace` | Show execution trace | `/trace` |
| `/model [name]` | Switch model | `/model haiku` |
| `/skill:<name>` | Use a skill | `/skill:web-research find X` |
| `/auth` | Manage credentials | `/auth` |
| `/theme` | Change theme | `/theme` |
| `/mcp` | Manage MCP servers | `/mcp` |
| `/editor` | Open file editor | `/editor` |
| `/reload` | Reload skills | `/reload` |
| `/update` | Check updates | `/update` |

---

## Core Commands

### `/help`
**Show all available slash commands and keyboard shortcuts**
```bash
/help
```
Shows a comprehensive list of all available commands in the TUI.

### `/quit`
**Exit the application**
```bash
/quit
```
Closes the TUI gracefully.

### `/clear`
**Clear conversation history in current thread**
```bash
/clear
```
⚠️ **Warning**: This clears the current conversation. Use `/threads` to switch conversations instead of losing history.

### `/version`
**Show application version**
```bash
/version
```
Displays agentd/deepagents version information.

---

## Token & Context Management

### `/tokens`
**Display token usage and context window status**
```bash
/tokens
```
**Shows:**
- Input tokens used
- Output tokens used
- Total tokens / context limit
- Percentage of context window filled
- System prompt + tools overhead
- Conversation message count

**Example output:**
```
2,345 / 200,000 tokens (1%)
├ System prompt + tools: ~500 tokens (fixed)
└ Conversation: ~1,845 tokens
```

### `/offload`
**Offload old messages to save context window**
```bash
/offload
```
Automatically summarizes and compresses older messages when context is running low. Useful for long conversations.

---

## Memory Management

### `/remember [fact]`
**Save a persistent memory fact across sessions**

Save a fact:
```bash
/remember I prefer detailed explanations
/remember Always use Python 3.11+ syntax
/remember Project root is /home/user/workspace
```

List all saved facts:
```bash
/remember
```

**Features:**
- ✅ Persists across app restarts
- ✅ Shared across all threads
- ✅ Auto-injected into all future conversations
- ✅ Global scope (visible everywhere)

**Stored in:** `~/.agentd_memories.json`

---

## Conversation Management

### `/threads`
**View all conversations and switch between them**
```bash
/threads
```

**Opens a modal showing:**
- All saved conversation threads
- Message count per thread
- Last updated time
- Initial prompt

**Use it to:**
- ✅ Resume old conversations
- ✅ Switch between projects
- ✅ Review past interactions
- ✅ Manage multiple parallel discussions

**Stored in:** `~/.agentd/.state/sessions.db`

### `/trace`
**Show execution trace with step-by-step details**
```bash
/trace
```

**Displays:**
- Each step taken by the model
- Tool calls made
- Tool responses received
- Reasoning process
- Time per step
- Token usage per step

Useful for debugging and understanding model behavior.

---

## Model Management

### `/model`
**Switch to a different LLM model**

Open model selector (interactive):
```bash
/model
```

Switch to specific model:
```bash
/model claude-sonnet-4-6
/model gpt-4
/model haiku
/model opus
```

### `/model --default [name]`
**Set the default model for future sessions**
```bash
/model --default claude-sonnet-4-6
```

Clear default and return to auto-detect:
```bash
/model --default --clear
```

### `/model --model-params JSON`
**Set model parameters (temperature, top_p, etc.)**
```bash
/model --model-params '{"temperature": 0.5, "top_p": 0.9}'
```

---

## Skill Management

### `/skill:<name>`
**Invoke a built-in or custom skill**

Basic skill invocation:
```bash
/skill:web-research find information about LLMs
/skill:code-review review main.py
/skill:file-search find all Python files with 'class User'
```

With arguments:
```bash
/skill:bash ls -la /tmp
/skill:python-repl print("hello")
```

**Available skills** (depends on installation):
- `web-research` — Search the web
- `code-review` — Review code
- `file-search` — Search files
- `bash` — Execute shell commands
- `python-repl` — Run Python code
- `remember` — Store facts (alternative to `/remember`)

### `/skill:remember`
**Alternative way to save facts** (same as `/remember`)
```bash
/skill:remember I like concise responses
```

### `/skill-creator`
**Create custom skills**
```bash
/skill-creator
```
Opens a UI to design and build new custom skills.

### `/reload`
**Reload skills and agents**
```bash
/reload
```
Refreshes skill discovery and loads any newly added skills.

---

## Settings & Configuration

### `/auth`
**Manage API credentials**
```bash
/auth
```

**Opens credential manager for:**
- Anthropic API key
- OpenAI API key
- Google credentials
- Other provider tokens

**Stored securely** in agentd credential store.

### `/theme`
**Change UI theme**
```bash
/theme
```

**Available themes:**
- Light (default)
- Dark
- Custom

### `/notifications`
**Configure notification settings**
```bash
/notifications
```

Control:
- Desktop notifications
- Sound alerts
- Long-running task notifications

### `/mcp`
**Manage MCP (Model Context Protocol) servers**
```bash
/mcp
```

**Manage:**
- Connected MCP servers
- Server status
- Server tools and resources

### `/editor`
**Open integrated file editor**
```bash
/editor
```
For editing files directly in the TUI.

---

## Updates & Documentation

### `/update`
**Check for and install updates**
```bash
/update
```
Checks if a newer version is available and prompts to install.

### `/auto-update`
**Configure automatic updates**
```bash
/auto-update
```
Enable/disable automatic update checks and installation.

### `/changelog`
**View recent changes and new features**
```bash
/changelog
```
Shows what's new in recent releases.

### `/docs`
**Open documentation**
```bash
/docs
```
Opens official documentation (agentd/deepagents docs).

### `/feedback`
**Send feedback to developers**
```bash
/feedback
```
Opens a form to report issues or suggest improvements.

---

## Agent Management

### `/agents`
**Manage agents**
```bash
/agents
```

**Manage:**
- Agent configurations
- Agent versions
- Agent switching
- Custom agent setup

### `/reload`
**Reload agents**
```bash
/reload
```
Refreshes agent discovery.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift+A` | Toggle auto-approve (was Shift+Tab) |
| `Ctrl+C` | Interrupt current operation |
| `Ctrl+D` | Exit application |
| `Ctrl+L` | Clear screen |
| `Tab` | Autocomplete command |
| `↑/↓` | Command history |

**Note:** In AgentD, the auto-approve toggle was changed from `Shift+Tab` to `Shift+A` for accessibility.

---

## Usage Examples

### Example 1: Quick Research Task
```bash
/model claude-opus-4-7          # Use powerful model for complex task
# Ask your question...
/skill:web-research find X      # Use web research skill
/tokens                          # Check token usage
```

### Example 2: Code Review
```bash
/remember Project uses FastAPI
/skill:code-review review app.py
/tokens
```

### Example 3: Multi-Session Work
```bash
/threads                         # See all conversations
# (select a thread to resume)
/remember What we decided last time  # Add context
# Continue working...
```

### Example 4: Model Switching
```bash
/model haiku                     # Fast responses
# Ask simple questions...
/model opus                      # Complex reasoning
# Ask complex questions...
/model --default sonnet          # Set default for next time
```

### Example 5: Memory Management
```bash
/remember I prefer detailed explanations
/remember Always verify output before proceeding
/remember Use Python 3.11+
/remember                        # List all facts
# Exit and restart...
/remember                        # Facts still there!
```

---

## Tips & Tricks

### Autocomplete
Press `Tab` while typing a command to autocomplete:
```bash
/mo[Tab]  → /model
/rem[Tab] → /remember
/ski[Tab] → /skill:
```

### Command History
Use `↑` and `↓` arrow keys to navigate previous commands.

### Save Context Before Clearing
Before using `/clear`, use `/threads` to verify you won't lose important work.

### Use `/tokens` Regularly
Monitor your context window to avoid hitting limits mid-task.

### Set Smart Defaults
```bash
/model --default sonnet          # Good for most tasks
/model --default opus            # If you do complex reasoning
```

### Create Memory for Preferences
```bash
/remember I prefer concise, technical responses
/remember Always explain my assumptions
/remember Use modern Python features
```

---

## Quick Command Reference by Category

**Start here:**
- `/help` — See all commands
- `/tokens` — Check usage
- `/threads` — See conversations
- `/remember` — Save facts

**Task execution:**
- `/model <name>` — Pick model
- `/skill:<name>` — Use tools
- `/trace` — Debug

**Configuration:**
- `/auth` — Add credentials
- `/theme` — Change theme
- `/model --default` — Set default

**Cleanup:**
- `/clear` — Start fresh
- `/offload` — Save context
- `/reload` — Refresh

---

## Default Behaviors

| Command | Without Args | With Args |
|---------|--------------|-----------|
| `/remember` | List all facts | Save new fact |
| `/model` | Open selector | Switch to model |
| `/threads` | Show modal | (no arg version) |
| `/skill:X` | Show help | Run skill X |
| `/tokens` | Show usage | (no arg version) |

---

## Related Commands

### In AgentD
- `D` — Quick shortcut (auto-approve + full TUI)
- `agentd` — Full command

### Within TUI
All `/` commands listed above plus:
- Type normally to chat with Claude
- Use `/` to access special commands
- Use `Shift+A` to toggle auto-approval

---

## Command Help

Get help for specific commands:
```bash
/help                    # All commands
/skill:name --help       # Help for specific skill
/model --help            # Model info
```

---

**Reference**: Full command list available via `/help` in any AgentD/Deepagents session.

Version: agentd 0.1.0
Last updated: 2026-05-07
