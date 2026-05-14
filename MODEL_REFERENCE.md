# AgentD Model Reference

Quick reference for all available models in agentD.

## Claude Models (Claude CLI)

Use via Claude Code's Claude CLI binary.

```bash
D -M haiku "task"      # Claude Haiku (fastest, cheapest)
D -M sonnet "task"     # Claude Sonnet (balanced)
D -M opus "task"       # Claude Opus (most capable)
```

## Ollama Models

Local models running on `http://localhost:11434` (default).

**Fast & Lightweight:**
```bash
D -M ministral-3:3b "task"          # Mistral 3B
D -M gemma3:4b-cloud "task"         # Gemma 3 4B
```

**Balanced:**
```bash
D -M ministral-3:3b-cloud "task"    # Mistral 3B Cloud
D -M gemma3:27b-cloud "task"        # Gemma 3 27B
```

**Powerful:**
```bash
D -M deepseek-v3.1:671b-cloud "task"      # DeepSeek V3.1
D -M nemotron-3-super:cloud "task"        # Nemotron 3 Super
```

For local models, make sure Ollama is running:
```bash
ollama serve
```

## Kimi Models (OpenAI-compatible via Kimi)

```bash
D -M moonshot-v1-8k "task"       # 8K context
D -M moonshot-v1-32k "task"      # 32K context
D -M moonshot-v1-128k "task"     # 128K context
```

## Xiaomi MiMo Models

```bash
D -M mimo-v2.5-pro "task"        # v2.5 Pro
D -M mimo-7b-rl "task"           # 7B RL
D -M mimo-7b-sft "task"          # 7B SFT
```

## Copilot CLI

```bash
D -M copilot "task"              # Copilot CLI
```

## Usage Examples

**Non-interactive:**
```bash
D -M haiku "write a python function"
D -M ministral-3:3b "explain this code"
```

**Interactive TUI:**
```bash
D -M sonnet        # Start TUI with Claude Sonnet
D -M llama2        # Start TUI with Ollama
```

**Resume conversation:**
```bash
D -M opus --thread-id my-chat
```

## Configuration

**Set default provider:**
```bash
export AGENTD_PROVIDER=ollama
D "task"  # Uses Ollama by default
```

**Set Ollama server URL:**
```bash
export OLLAMA_BASE_URL=http://192.168.1.100:11434
D -M ministral-3:3b "task"
```

**Set Ollama API key (if required):**
```bash
export OLLAMA_API_KEY=your-api-key
```

## Model Selection in TUI

When running `D` interactively, use `/model` to see and switch between models:

```
/model
1. Claude Sonnet
2. Claude Opus
3. Claude Haiku
4. Ollama: ministral-3:3b
5. Ollama: gemma3:4b-cloud
...
```

Type the number to select.

## Performance Comparison

| Model | Speed | Quality | Context | Best For |
|-------|-------|---------|---------|----------|
| Haiku | ⚡⚡⚡ | ⭐⭐⭐ | 200K | Quick tasks |
| Sonnet | ⚡⚡ | ⭐⭐⭐⭐ | 200K | Balanced |
| Opus | ⚡ | ⭐⭐⭐⭐⭐ | 200K | Complex tasks |
| Ministral 3B | ⚡⚡⚡ | ⭐⭐⭐ | 32K | Local, fast |
| Gemma 4B | ⚡⚡ | ⭐⭐⭐⭐ | 8K | Local, balanced |
| DeepSeek V3 | ⚡ | ⭐⭐⭐⭐⭐ | 128K | Local, powerful |

## See Also

- [OLLAMA_SETUP.md](OLLAMA_SETUP.md) — Detailed Ollama integration guide
- [README.md](README.md) — Main documentation
