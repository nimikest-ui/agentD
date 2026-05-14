#!/usr/bin/env python3
"""Test Agent with Kimi model"""

from agentd.core import Agent

print("Creating Agent with kimi:kimi-k2.6...")
try:
    agent = Agent(model="kimi:kimi-k2.6")
    print(f"✓ Agent created: {agent}")
    print(f"  model_name: {agent.model_name}")
    print(f"  agent_model: {agent.agent_model}")
    print(f"  agent_model._llm_type: {agent.agent_model._llm_type}")
except Exception as e:
    print(f"✗ Failed to create agent: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\nInvoking agent with test message...")
try:
    result = agent.invoke("hi")
    print(f"✓ Success")
    print(f"  Result keys: {result.keys()}")
    if "messages" in result:
        print(f"  Last message: {result['messages'][-1]}")
except Exception as e:
    print(f"✗ Failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    agent.close()
