"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_agent():
    """Mock JarvisAgent for testing."""
    with patch('server.agent') as mock:
        mock.get_status.return_value = {"status": "ready"}
        mock.process.return_value.__await__ = lambda: iter([{
            "timestamp": "2026-06-19T12:00:00",
            "reasoning": {"output": "Mock response", "reasoning": "Mock reasoning"}
        }])
        mock.state.session_id = "mock_session"
        mock.call_tool.return_value.__await__ = lambda: iter([{"result": "mock"}])
        yield mock


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter that always allows."""
    with patch('server.rate_limiter') as mock:
        mock.is_allowed.return_value = {"allowed": True, "remaining": 100}
        yield mock


@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing."""
    mock = MagicMock()
    mock.send_json = MagicMock()
    mock.send_text = MagicMock()
    mock.accept = MagicMock()
    mock.close = MagicMock()
    return mock


@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    from fastapi.testclient import TestClient
    from server import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["LOG_LEVEL"] = "WARNING"
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def sample_chat_request():
    """Sample valid chat request."""
    return {
        "message": "Hello, how are you?",
        "modality": "text",
        "session_id": "test_session_123"
    }


@pytest.fixture
def sample_tool_request():
    """Sample valid tool request."""
    return {
        "tool": "weather",
        "args": {"city": "Beijing"}
    }


@pytest.fixture
def sample_llm_config():
    """Sample valid LLM config."""
    return {
        "provider": "openai",
        "api_base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o",
        "api_key": "sk-test_key_1234567890abcdefghijklmnopqrstuvwxyz",
        "temperature": 0.7,
        "max_tokens": 4096,
        "timeout": 60
    }
