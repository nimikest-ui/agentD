#!/usr/bin/env python3
"""Direct test of KimiModel.invoke()"""

from agentd.models import KimiModel
from langchain_core.messages import HumanMessage

print("Creating KimiModel instance...")
try:
    model = KimiModel(model="kimi-k2.6")
    print(f"✓ Model created: {model._llm_type}")
    print(f"  API key present: {bool(model.api_key)}")
    print(f"  Base URL: {model.base_url}")
except Exception as e:
    print(f"✗ Failed to create model: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\nCalling model.invoke() with test message...")
try:
    response = model.invoke([HumanMessage(content="hi")])
    print(f"✓ Success: {response}")
except Exception as e:
    print(f"✗ Failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
