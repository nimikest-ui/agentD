# LangSmith Integration Setup Guide

AgentD now includes full LangSmith tracing support for automatic observability of your AI agent workflows.

## Quick Start

### 1. Get Your API Key

1. Sign up or log in at [LangSmith](https://smith.langchain.com)
2. Go to Settings → API Keys
3. Create a new API key and copy it

### 2. Install Dependencies

```bash
pip install -e .
```

This installs AgentD with LangSmith and Anthropic SDK support.

### 3. Configure Environment Variables

Create a `.env` file in your project root:

```bash
cp .env.example .env
```

Then edit `.env` and add your API key:

```env
LANGSMITH_API_KEY=lsv2_pt_YOUR_KEY_HERE
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agentd
```

### 4. Run Your Agent

```python
from agentd.tracing import configure_langsmith
from agentd.core import Agent

# Initialize tracing
configure_langsmith(project_name="agentd")

# Use your agent normally
agent = Agent(model="sonnet")
# All calls are automatically traced!
```

## Features

### 1. Automatic Model Tracing

Your `Agent` and `AgentDModel` calls are automatically traced:

```python
from agentd.core import Agent

agent = Agent(model="sonnet")
# All model calls to Claude are traced in LangSmith
```

### 2. Custom Function Tracing

Decorate functions with `@trace_run` to trace custom workflows:

```python
from agentd.tracing import trace_run

@trace_run(name="My Workflow", run_type="chain")
def my_workflow(query: str):
    # This function is traced
    return process(query)

@trace_run(name="Search Tool", run_type="tool")
def search(query: str):
    # This tool usage is traced
    return search_docs(query)
```

### 3. Anthropic SDK Client Tracing

Use the wrapped Anthropic client for direct API calls:

```python
from agentd.tracing import create_anthropic_client
import os

client = create_anthropic_client(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    enable_tracing=True,
)

# All calls to this client are traced
message = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

### 4. Run Types

Use appropriate `run_type` for different operations:

- `"llm"` - LLM model calls
- `"chain"` - Multi-step workflows
- `"tool"` - Tool or function calls
- `"agent"` - Agent execution
- `"retriever"` - Document retrieval

## Tracing API Reference

### `configure_langsmith(api_key, project_name, workspace_id)`

Configure LangSmith environment variables.

**Parameters:**
- `api_key` (str, optional): LangSmith API key
- `project_name` (str): Project name for organizing traces (default: "default")
- `workspace_id` (str, optional): Workspace ID for multi-workspace accounts

**Example:**
```python
from agentd.tracing import configure_langsmith

configure_langsmith(
    api_key="your-api-key",
    project_name="my-project",
    workspace_id="your-workspace-id"
)
```

### `@trace_run(name, run_type, **kwargs)`

Decorator to trace function execution.

**Parameters:**
- `name` (str): Display name in LangSmith UI
- `run_type` (str): Type of run ("chain", "tool", "agent", "llm", "retriever")
- `**kwargs`: Additional keyword arguments for `@traceable`

**Example:**
```python
from agentd.tracing import trace_run

@trace_run(name="Search Pipeline", run_type="chain")
def search_and_rank(query: str):
    results = search(query)
    return rank_results(results)
```

### `create_anthropic_client(api_key, enable_tracing)`

Create Anthropic client with optional LangSmith tracing.

**Parameters:**
- `api_key` (str, optional): Anthropic API key
- `enable_tracing` (bool): Enable LangSmith tracing (default: True)

**Returns:** Wrapped or unwrapped Anthropic client

**Example:**
```python
from agentd.tracing import create_anthropic_client

client = create_anthropic_client(
    api_key="your-anthropic-key",
    enable_tracing=True
)
```

### `get_langsmith_client()`

Get LangSmith client instance for advanced operations.

**Example:**
```python
from agentd.tracing import get_langsmith_client

ls_client = get_langsmith_client()
# Use for advanced tracing operations
```

## Environment Variables

Configure tracing with these environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `LANGSMITH_API_KEY` | Your LangSmith API key | Yes |
| `LANGSMITH_TRACING` | Enable tracing ("true"/"false") | No (default: false) |
| `LANGSMITH_PROJECT` | Project name for organizing traces | No (default: "default") |
| `LANGSMITH_WORKSPACE_ID` | Workspace ID for multi-workspace accounts | No |
| `ANTHROPIC_API_KEY` | Anthropic API key for SDK client | Only for Anthropic SDK usage |

## Viewing Traces

1. After running your code, go to [LangSmith](https://smith.langchain.com)
2. Navigate to your project
3. View traces, latencies, token usage, and errors
4. Click into traces to see detailed information about each step

## Troubleshooting

### Traces not appearing

1. Check `LANGSMITH_TRACING=true` in your environment
2. Verify `LANGSMITH_API_KEY` is set correctly
3. Check that your code is using Agent or @trace_run decorators
4. Look for errors in your application logs

### No module named 'langsmith'

Install dependencies:
```bash
pip install -e .
```

### Tracing is slow

- LangSmith overhead is minimal (~1-2% latency)
- For high-throughput applications, consider batching traces
- You can disable tracing by setting `LANGSMITH_TRACING=false`

## Advanced Usage

### Custom Run Metadata

Pass additional metadata to traces:

```python
from langsmith import traceable

@traceable(
    name="My Function",
    run_type="chain",
    tags=["production", "important"],
    metadata={"version": "1.0", "experiment": "test_a"}
)
def my_function():
    pass
```

### Conditional Tracing

Enable/disable tracing based on conditions:

```python
from agentd.tracing import trace_run, traceable
import os

if os.environ.get("LANGSMITH_TRACING") == "true":
    @trace_run(name="My Workflow", run_type="chain")
    def my_workflow():
        pass
else:
    def my_workflow():
        pass
```

### Batch Tracing

For high-throughput scenarios:

```python
from langsmith import Client

client = Client()
with client.batch_contexts(project_name="agentd") as batch:
    # All runs within this context are batched
    for item in items:
        process(item)
```

## Examples

See `examples/tracing_example.py` for comprehensive examples including:

1. Basic agent tracing
2. Decorator-based function tracing
3. Wrapped Anthropic client usage
4. Agent workflows with tool tracing

Run examples:

```bash
python examples/tracing_example.py
```

## Next Steps

- Explore [LangSmith Documentation](https://docs.langchain.com/langsmith)
- Set up debugging with [LangSmith Studio](https://smith.langchain.com)
- Configure [alerts and monitors](https://docs.langchain.com/langsmith/monitoring)
- Integrate with [CI/CD pipelines](https://docs.langchain.com/langsmith/testing)
