#!/usr/bin/env python3
"""
AgentD - LLM Agent Framework
A production-grade agentic framework with full session logging, memory,
token tracking, and Claude CLI integration.
"""

from setuptools import setup, find_packages
from pathlib import Path

root_dir = Path(__file__).parent
readme_path = root_dir / "README.md"

long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="agentD",
    version="0.1.0",
    description="LLM Agent Framework with full session logging and memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AgentD Contributors",
    url="https://github.com/yourusername/agentD",
    license="MIT",
    packages=find_packages(include=["agentd", "agentd.*"]),
    python_requires=">=3.10",
    install_requires=[
        "langchain>=0.1.0",
        "langgraph>=0.0.1",
        "langsmith>=0.0.1",
        "textual>=0.20.0",
        "pydantic>=2.0",
        "anthropic>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "D=agentd.cli:main",
            "agentd=agentd.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
