# LangSmith Quick Start (5 minutes)

Get LangSmith tracing running with AgentD in 5 minutes.

## Step 1: Get API Key (1 minute)

1. Go to https://smith.langchain.com
2. Sign up or log in
3. Go to Settings → API Keys → Create New
4. Copy your API key

## Step 2: Configure Environment (1 minute)

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your key
LANGSMITH_API_KEY=lsv2_pt_YOUR_KEY
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agentd
```

## Step 3: Install & Import (1 minute)

```bash
pip install -e .
```

In your Python code:

```python
from agentd.tracing import configure_langsmith
from agentd.core import Agent

# Configure once at startup
configure_langsmith(project_name="agentd")

# Your agent calls are automatically traced!
agent = Agent()
```

## Step 4: Run & View (2 minutes)

```bash
python your_script.py
```

Then open https://smith.langchain.com and view your traces!

## That's It! 🎉

Every Agent call is now automatically traced with:
- Model calls
- Token usage
- Latency
- Errors
- Full request/response

## Add Custom Tracing (Optional)

Trace your own functions:

```python
from agentd.tracing import trace_run

@trace_run(name="My Pipeline", run_type="chain")
def my_pipeline(query):
    # This is traced
    return process(query)
```

## Troubleshooting

- **No traces showing?** Check `LANGSMITH_TRACING=true`
- **Import error?** Run `pip install -e .`
- **API key error?** Verify key in .env is correct

See `LANGSMITH_SETUP.md` for complete documentation.
