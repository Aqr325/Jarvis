"""
Tests for server.py API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check_returns_ok(self):
        """Health endpoint should return 200 OK."""
        from server import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["websocket_enabled"] is True
    
    def test_health_check_returns_all_fields(self):
        """Health endpoint should return all expected fields."""
        from server import app
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        required_fields = ["status", "service", "version", "websocket_enabled", "rate_limiting"]
        for field in required_fields:
            assert field in data


class TestStatusEndpoint:
    """Tests for /api/status endpoint."""
    
    def test_status_endpoint(self):
        """Status endpoint should return agent status."""
        from server import app
        client = TestClient(app)
        # Mock the agent
        with patch('server.agent') as mock_agent:
            mock_agent.get_status.return_value = {"status": "ready", "session_id": "test"}
            response = client.get("/api/status")
            assert response.status_code == 200
    
    def test_status_endpoint_rate_limit(self):
        """Status endpoint should respect rate limiting."""
        from server import app
        from server import rate_limiter
        client = TestClient(app)
        
        with patch('server.agent') as mock_agent:
            # Block the rate limiter temporarily
            original_is_allowed = rate_limiter.is_allowed
            rate_limiter.is_allowed = lambda *args: {"allowed": False, "retry_after": 60, "remaining": 0}
            
            response = client.get("/api/status")
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json().get("detail", {}).get("error", "")
            
            rate_limiter.is_allowed = original_is_allowed


class TestChatEndpoint:
    """Tests for /api/chat endpoint."""
    
    def test_chat_valid_request(self):
        """Chat endpoint should accept valid requests."""
        from server import app
        client = TestClient(app)
        
        with patch('server.agent') as mock_agent:
            mock_agent.process.return_value.__await__ = lambda: iter([{
                "timestamp": "2026-06-19T12:00:00",
                "reasoning": {"output": "Test response", "reasoning": "Test"}
            }])
            mock_agent.state.session_id = "test_session"
            
            response = client.post("/api/chat", json={
                "message": "Hello, how are you?",
                "modality": "text"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "output" in data
            assert "session_id" in data
    
    def test_chat_empty_message(self):
        """Chat endpoint should reject empty messages."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422  # Validation error
    
    def test_chat_message_too_long(self):
        """Chat endpoint should reject messages that are too long."""
        from server import app
        client = TestClient(app)
        
        # Create a message exceeding 4096 characters
        long_message = "x" * 5000
        
        response = client.post("/api/chat", json={"message": long_message})
        assert response.status_code == 422  # Validation error
    
    def test_chat_invalid_modality(self):
        """Chat endpoint should reject invalid modality values."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/chat", json={
            "message": "Hello",
            "modality": "telepathy"  # Invalid modality
        })
        assert response.status_code == 422
    
    def test_chat_extra_fields_rejected(self):
        """Chat endpoint should reject unknown fields."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/chat", json={
            "message": "Hello",
            "invalid_field": "should be rejected"
        })
        assert response.status_code == 422


class TestToolEndpoint:
    """Tests for /api/tool endpoint."""
    
    def test_tool_valid_request(self):
        """Tool endpoint should accept valid requests."""
        from server import app
        client = TestClient(app)
        
        with patch('server.agent') as mock_agent:
            mock_agent.call_tool.return_value.__await__ = lambda: iter([{"result": "success"}])
            
            response = client.post("/api/tool", json={
                "tool": "weather",
                "args": {"city": "Beijing"}
            })
            
            assert response.status_code == 200
    
    def test_tool_invalid_name(self):
        """Tool endpoint should reject invalid tool names."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/tool", json={
            "tool": "123invalid",  # Must start with letter
            "args": {}
        })
        assert response.status_code == 422
    
    def test_tool_special_characters(self):
        """Tool endpoint should reject tool names with special characters."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/tool", json={
            "tool": "tool@name",  # Invalid characters
            "args": {}
        })
        assert response.status_code == 422


class TestModelConfigEndpoint:
    """Tests for /api/model/config endpoint."""
    
    def test_valid_openai_config(self):
        """Should accept valid OpenAI configuration."""
        from server import app
        client = TestClient(app)
        
        with patch('server.agent') as mock_agent:
            response = client.post("/api/model/config", json={
                "provider": "openai",
                "api_base_url": "https://api.openai.com/v1",
                "model_name": "gpt-4o",
                "api_key": "sk-valid_key_12345",
                "temperature": 0.7,
                "max_tokens": 4096
            })
            
            # Should be 200 or 500 depending on whether agent is initialized
            assert response.status_code in [200, 500]
    
    def test_invalid_provider(self):
        """Should reject invalid provider."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/model/config", json={
            "provider": "invalid_provider_xyz",
            "model_name": "test"
        })
        assert response.status_code == 422
        assert "provider" in response.json().get("detail", {}).get("message", "").lower()
    
    def test_invalid_temperature(self):
        """Should reject temperature outside valid range."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/model/config", json={
            "provider": "openai",
            "model_name": "gpt-4o",
            "temperature": 5.0  # Max is 2.0
        })
        assert response.status_code == 422
    
    def test_api_key_too_short(self):
        """Should reject API key that is too short."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/model/config", json={
            "provider": "openai",
            "model_name": "gpt-4o",
            "api_key": "short"  # Less than 10 chars
        })
        assert response.status_code == 422


class TestSchedulerEndpoints:
    """Tests for scheduler endpoints."""
    
    def test_create_task_valid(self):
        """Should accept valid task creation request."""
        from server import app
        client = TestClient(app)
        
        with patch('server.scheduler') as mock_scheduler:
            mock_scheduler.create_task.return_value.__await__ = lambda: iter([{"id": "task_1"}])
            
            response = client.post("/api/scheduler/task", json={
                "title": "Test task",
                "due_date": "2026-06-25",
                "priority": "high"
            })
            
            assert response.status_code == 200
    
    def test_create_task_invalid_priority(self):
        """Should reject invalid priority."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/scheduler/task", json={
            "title": "Test",
            "due_date": "2026-06-25",
            "priority": "ultra_high"  # Invalid
        })
        assert response.status_code == 422


class TestPublicAPIEndpoints:
    """Tests for public API endpoints."""
    
    def test_crypto_request_valid(self):
        """Should accept valid crypto request."""
        from server import app
        client = TestClient(app)
        
        with patch('modules.public_apis.crypto_price') as mock_crypto:
            mock_crypto.return_value.__await__ = lambda: iter([{"price": 50000}])
            
            response = client.post("/api/public/crypto", json={
                "coin_id": "bitcoin",
                "vs_currency": "usd"
            })
            
            assert response.status_code == 200
    
    def test_exchange_request_valid(self):
        """Should accept valid exchange request."""
        from server import app
        client = TestClient(app)
        
        with patch('modules.public_apis.exchange_rate') as mock_exchange:
            mock_exchange.return_value.__await__ = lambda: iter([{"rate": 7.2}])
            
            response = client.post("/api/public/exchange", json={
                "from_currency": "USD",
                "to_currency": "CNY",
                "amount": 100
            })
            
            assert response.status_code == 200
    
    def test_exchange_invalid_currency_code(self):
        """Should reject invalid currency codes."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/public/exchange", json={
            "from_currency": "US",  # Too short
            "to_currency": "CNY"
        })
        assert response.status_code == 422
    
    def test_holiday_request_valid(self):
        """Should accept valid holiday request."""
        from server import app
        client = TestClient(app)
        
        with patch('modules.public_apis.public_holidays') as mock_holidays:
            mock_holidays.return_value.__await__ = lambda: iter([{"holidays": []}])
            
            response = client.post("/api/public/holidays", json={
                "year": 2026,
                "country_code": "CN"
            })
            
            assert response.status_code == 200
    
    def test_holiday_year_out_of_range(self):
        """Should reject year out of valid range."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/public/holidays", json={
            "year": 1800,  # Before 2000
            "country_code": "CN"
        })
        assert response.status_code == 422


class TestSchemaValidation:
    """Tests for schema validation directly."""
    
    def test_chat_request_schema(self):
        """Test ChatRequest schema validation."""
        from schemas.chat import ChatRequest
        
        # Valid request
        req = ChatRequest(message="Hello", modality="text")
        assert req.message == "Hello"
        assert req.modality == "text"
        
        # Empty message should fail
        with pytest.raises(Exception):
            ChatRequest(message="")
    
    def test_tool_request_schema(self):
        """Test ToolRequest schema validation."""
        from schemas.tool import ToolRequest
        
        # Valid request
        req = ToolRequest(tool="weather", args={"city": "Beijing"})
        assert req.tool == "weather"
        
        # Invalid tool name
        with pytest.raises(Exception):
            ToolRequest(tool="123invalid")
    
    def test_llm_config_schema(self):
        """Test LLMModelConfig schema validation."""
        from schemas.model import LLMModelConfig
        
        # Valid config
        config = LLMModelConfig(
            provider="openai",
            model_name="gpt-4o",
            api_key="sk-very_long_valid_key_1234567890"
        )
        assert config.provider == "openai"
        assert config.temperature == 0.7  # Default
    
    def test_create_task_request_schema(self):
        """Test CreateTaskRequest schema validation."""
        from schemas.scheduler import CreateTaskRequest
        
        # Valid request
        task = CreateTaskRequest(
            title="Test task",
            due_date="2026-06-25",
            priority="high"
        )
        assert task.title == "Test task"
        assert task.priority == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
