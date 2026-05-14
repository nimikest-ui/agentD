#!/usr/bin/env python3
"""Test if API keys work by making actual API calls."""

import httpx
import json
import sys
from agentd.auth_store import get_credential

def test_kimi():
    """Test Kimi/Moonshot API."""
    print("=" * 60)
    print("Testing Kimi/Moonshot API")
    print("=" * 60)

    api_key = get_credential("MOONSHOT_API_KEY")
    if not api_key:
        print("✗ MOONSHOT_API_KEY not found in credentials")
        return False

    print(f"✓ API Key found: {api_key[:20]}...")

    url = "https://api.moonshot.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "kimi-k2.5",
        "messages": [{"role": "user", "content": "test"}],
        "stream": False,
    }

    print(f"POST {url}")
    print(f"Headers: Authorization: Bearer {api_key[:20]}...")

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            print("✓ Kimi API works!")
            return True
        else:
            print(f"✗ Kimi API error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def test_xiaomi():
    """Test Xiaomi MiMo API."""
    print("\n" + "=" * 60)
    print("Testing Xiaomi MiMo API")
    print("=" * 60)

    api_key = get_credential("XIOMIMIMO_API_KEY")
    if not api_key:
        print("✗ XIOMIMIMO_API_KEY not found in credentials")
        return False

    print(f"✓ API Key found: {api_key[:20]}...")

    url = "https://api.xiaomimimo.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mimo-v2.5-pro",
        "messages": [{"role": "user", "content": "test"}],
        "stream": False,
    }

    print(f"POST {url}")
    print(f"Headers: Authorization: Bearer {api_key[:20]}...")

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            print("✓ Xiaomi API works!")
            return True
        else:
            print(f"✗ Xiaomi API error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

if __name__ == "__main__":
    kimi_ok = test_kimi()
    xiaomi_ok = test_xiaomi()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Kimi: {'✓ OK' if kimi_ok else '✗ FAILED'}")
    print(f"Xiaomi: {'✓ OK' if xiaomi_ok else '✗ FAILED'}")

    sys.exit(0 if (kimi_ok or xiaomi_ok) else 1)
