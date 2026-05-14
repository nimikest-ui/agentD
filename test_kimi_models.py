#!/usr/bin/env python3
"""Test each registered Kimi model."""

from agentd.models import KIMI_MODELS
from agentd.core import Agent
from langchain_core.messages import HumanMessage

print(f"Testing {len(KIMI_MODELS)} registered Kimi models:\n")

for model_name in KIMI_MODELS:
    try:
        print(f"Testing {model_name}...", end=" ", flush=True)

        # Create Agent with this model
        agent = Agent(model=model_name)

        # Try to invoke
        response = agent.invoke("hi", thread_id=f"test-{model_name}")

        # Check if we got a response
        if response and "messages" in response and len(response["messages"]) > 0:
            msg = response["messages"][-1]
            content = getattr(msg, "content", str(msg))[:50]
            print(f"✓ {content}...")
        else:
            print(f"✗ No response")

        agent.close()
    except Exception as e:
        error_msg = str(e)[:80]
        print(f"✗ {error_msg}")
