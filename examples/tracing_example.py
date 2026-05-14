"""
Example: Using LangSmith Tracing with AgentD

Demonstrates how to:
1. Configure LangSmith
2. Use the traced AgentDModel
3. Use @traceable decorators for custom functions
4. Use the wrapped Anthropic client
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agentd.tracing import (
    configure_langsmith,
    trace_run,
    create_anthropic_client,
)
from agentd.core import Agent
from langchain_core.messages import HumanMessage


def setup_tracing():
    """Initialize LangSmith tracing."""
    configure_langsmith(
        api_key=os.getenv("LANGSMITH_API_KEY"),
        project_name="agentd",
    )
    print("✓ LangSmith tracing configured")


@trace_run(name="Query Processor", run_type="chain")
def process_query(query: str) -> str:
    """Process a user query with tracing."""
    print(f"Processing query: {query}")
    return f"Processed: {query}"


@trace_run(name="RAG Pipeline", run_type="chain")
def retrieval_augmented_generation(user_query: str) -> str:
    """Example RAG pipeline with tracing."""
    # This would normally retrieve documents
    context = "Retrieved context about the topic"

    # Process with the agent
    return f"Query: {user_query}\nContext: {context}"


def example_basic_tracing():
    """Example 1: Basic tracing with AgentDModel."""
    print("\n--- Example 1: Basic Tracing ---")
    setup_tracing()

    # Create an agent (uses AgentDModel with tracing)
    agent = Agent(model="sonnet")

    # When you call the agent, it's automatically traced
    print("Agent created:", agent)
    # Chat calls are traced in LangSmith


def example_decorator_tracing():
    """Example 2: Decorator-based tracing."""
    print("\n--- Example 2: Decorator Tracing ---")
    setup_tracing()

    # These function calls are traced
    result1 = process_query("What is LangSmith?")
    print("Result:", result1)

    result2 = retrieval_augmented_generation("How to use AgentD?")
    print("Result:", result2)


def example_anthropic_client():
    """Example 3: Using wrapped Anthropic client with tracing."""
    print("\n--- Example 3: Wrapped Anthropic Client ---")
    setup_tracing()

    # Create wrapped Anthropic client
    client = create_anthropic_client(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        enable_tracing=True,
    )

    # Calls to this client are automatically traced
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "What is LangSmith?"
            }
        ]
    )
    print("Response:", message.content[0].text)


def example_agent_with_tools():
    """Example 4: Agent with tool usage tracing."""
    print("\n--- Example 4: Agent with Tools ---")
    setup_tracing()

    @trace_run(name="Tool Call", run_type="tool")
    def search_docs(query: str) -> str:
        """Simulated document search tool."""
        return f"Found documents about: {query}"

    @trace_run(name="Agent Workflow", run_type="agent")
    def agent_workflow(user_input: str) -> str:
        """Complete agent workflow."""
        docs = search_docs(user_input)
        # Agent processes docs and generates response
        return f"Based on search: {docs}"

    result = agent_workflow("Tell me about LangSmith")
    print("Workflow result:", result)


if __name__ == "__main__":
    print("AgentD LangSmith Tracing Examples")
    print("=" * 50)

    # Run examples (uncomment to run specific examples)
    # example_basic_tracing()
    # example_decorator_tracing()
    # example_anthropic_client()
    # example_agent_with_tools()

    print("\nNote: Ensure LANGSMITH_API_KEY is set in .env")
    print("View traces at: https://smith.langchain.com")
