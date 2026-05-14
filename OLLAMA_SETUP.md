# AgentD + Ollama Integration

Run agentD with local Ollama models. No API keys required for local models.

## Setup

### 1. Install Ollama

Download and install Ollama from https://ollama.ai

### 2. Pull a model

```bash
ollama pull llama2
ollama pull neural-chat
ollama pull mistral
```

Check available models:
```bash
ollama list
```

### 3. Start Ollama server

```bash
ollama serve
```

The server runs on `http://localhost:11434` by default.

## Usage

### Run with Ollama model

```bash
# Using non-interactive mode
D -M llama2 "solve this problem"
D -M mistral "write a python script"
D -M neural-chat "explain this code"

# Or in TUI mode
D -M llama2

# With custom Ollama server URL
OLLAMA_BASE_URL=http://192.168.1.100:11434 D -M llama2
```

### Configuration

**Environment Variables:**

```bash
# Ollama server URL (default: http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434

# Ollama API key (if your Ollama server requires auth)
export OLLAMA_API_KEY=your-api-key-here

# Force Ollama provider
export AGENTD_PROVIDER=ollama
```

**Add to .env file:**

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=optional-key
AGENTD_PROVIDER=ollama
```

### Available Ollama Models

Popular models to pull:

- **llama2** — General purpose (7B, 13B, 70B variants)
- **mistral** — Fast and efficient (7B)
- **neural-chat** — Chat optimized
- **phi** — Lightweight (2.7B)
- **orca-mini** — Instruction following (3B, 7B)
- **dolphin-mixtral** — Mixture of experts
- **openchat** — Chat model

Pull with size specifier:
```bash
ollama pull llama2:13b
ollama pull mistral:7b
```

### Model Selection in TUI

When running `D`, the `/model` menu will show available Ollama models:

```
1. Sonnet (Claude)
2. Copilot CLI
3. Ollama: llama2
4. Ollama: mistral
5. Ollama: neural-chat
...
```

Select an Ollama model by number.

### API Key (Optional)

If your Ollama server requires authentication:

```bash
# Set in environment
export OLLAMA_API_KEY=your-api-key

# Or in .env
echo "OLLAMA_API_KEY=your-api-key" >> .env

# Then in TUI, use /auth to configure
```

## Examples

**Non-interactive task with Ollama:**
```bash
D -M llama2 "write a python function to sort a list"
```

**Resume conversation with Ollama:**
```bash
D -M mistral --thread-id my-chat
```

**Use a specific model size:**
```bash
D -M llama2:13b "explain quantum computing"
```

**Stream from Ollama:**
```bash
D -M mistral  # Starts TUI with streaming response
```

## Troubleshooting

**Connection refused:**
```bash
# Make sure Ollama is running
ollama serve

# Or check if it's on a different host
OLLAMA_BASE_URL=http://your-server:11434 D -M llama2
```

**Model not found:**
```bash
# Pull the model first
ollama pull llama2

# Check available models
ollama list
```

**Slow responses:**
- Use a smaller model (phi, orca-mini, mistral)
- Use GPU acceleration: `ollama serve --gpu` (if available)
- Check Ollama resource usage

**Out of memory:**
- Reduce model size: `llama2:7b` instead of `llama2:70b`
- Close other applications
- Use smaller batch size in Ollama settings

## Model Registry

AgentD automatically discovers available Ollama models and registers them in the `/model` menu. To refresh the list:

```bash
# Models are cached, restart agentD to refresh:
D
```

## Performance Notes

- **Local Ollama models** are ideal for privacy-sensitive work
- **CPU inference** is slower than GPU; GPU support varies by system
- **Model selection** impacts speed:
  - `phi` / `orca-mini` (3-7B) — Fast, lower quality
  - `mistral` / `neural-chat` (7B) — Balanced
  - `llama2:13b` / `mixtral` (13B+) — Slower, higher quality
  - `llama2:70b` — Very slow on CPU, excellent on GPU

## See Also

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Available Models](https://ollama.ai/library)
- [AgentD Main Documentation](README.md)
