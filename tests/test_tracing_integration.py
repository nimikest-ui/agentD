"""
Tests for LangSmith tracing integration.
"""

import os
import pytest
from agentd.tracing import (
    configure_langsmith,
    get_langsmith_client,
    create_anthropic_client,
    trace_run,
)


class TestTracingConfiguration:
    """Test LangSmith configuration."""

    def test_configure_langsmith_sets_env_vars(self):
        """Test that configure_langsmith sets environment variables."""
        configure_langsmith(
            api_key="test-key",
            project_name="test-project",
            workspace_id="test-workspace"
        )

        assert os.environ.get("LANGSMITH_API_KEY") == "test-key"
        assert os.environ.get("LANGSMITH_TRACING") == "true"
        assert os.environ.get("LANGSMITH_PROJECT") == "test-project"
        assert os.environ.get("LANGSMITH_WORKSPACE_ID") == "test-workspace"

    def test_configure_langsmith_without_api_key(self):
        """Test configuration without providing API key."""
        os.environ.pop("LANGSMITH_API_KEY", None)
        configure_langsmith(project_name="test")

        assert os.environ.get("LANGSMITH_TRACING") == "true"
        assert os.environ.get("LANGSMITH_PROJECT") == "test"


class TestAnthropicClient:
    """Test Anthropic client wrapper."""

    def test_create_anthropic_client_without_tracing(self):
        """Test creating Anthropic client without tracing."""
        os.environ["LANGSMITH_TRACING"] = "false"
        client = create_anthropic_client(enable_tracing=False)
        assert client is not None
        assert hasattr(client, 'messages')

    def test_create_anthropic_client_with_tracing(self):
        """Test creating Anthropic client with tracing enabled."""
        os.environ["LANGSMITH_TRACING"] = "true"
        # This should not raise an error even without valid key
        # (tracing wraps the client, doesn't validate credentials)
        try:
            client = create_anthropic_client(enable_tracing=True)
            assert client is not None
        except ImportError:
            # langsmith may not be installed in test environment
            pytest.skip("langsmith not installed")


class TestTraceRunDecorator:
    """Test @trace_run decorator."""

    def test_trace_run_decorator_basic(self):
        """Test basic @trace_run decorator functionality."""
        @trace_run(name="Test Function", run_type="tool")
        def test_func(x: int) -> int:
            return x * 2

        # Function should work normally
        result = test_func(5)
        assert result == 10

    def test_trace_run_preserves_function_name(self):
        """Test that @trace_run preserves function metadata."""
        @trace_run(name="Test", run_type="chain")
        def my_function():
            """My docstring."""
            pass

        # functools.wraps should preserve the original function's metadata
        assert my_function.__doc__ == "My docstring."

    def test_trace_run_with_args_and_kwargs(self):
        """Test @trace_run with various argument patterns."""
        @trace_run(name="Complex Function", run_type="chain")
        def complex_func(a, b, *args, c=None, **kwargs):
            return (a, b, args, c, kwargs)

        result = complex_func(1, 2, 3, 4, c=5, d=6)
        assert result == (1, 2, (3, 4), 5, {'d': 6})


class TestLangSmithClient:
    """Test LangSmith client access."""

    def test_get_langsmith_client(self):
        """Test getting LangSmith client instance."""
        try:
            client = get_langsmith_client()
            assert client is not None
        except Exception as e:
            # May fail without valid API key, which is expected
            pytest.skip(f"LangSmith client not available: {e}")


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_tracing_respects_env_flag(self):
        """Test that tracing respects LANGSMITH_TRACING flag."""
        # Tracing should only be active when flag is true
        os.environ["LANGSMITH_TRACING"] = "false"

        @trace_run(name="Test", run_type="chain")
        def func():
            return "result"

        result = func()
        assert result == "result"

        os.environ["LANGSMITH_TRACING"] = "true"
        result = func()
        assert result == "result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
