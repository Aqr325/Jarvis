"""
Tests for schema validation layer.
"""

import pytest
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBaseSchemas:
    """Tests for base schema classes."""
    
    def test_response_base_default_values(self):
        """ResponseBase should have default values."""
        from schemas.base import ResponseBase
        
        resp = ResponseBase()
        assert resp.success is True
        assert resp.timestamp is not None
    
    def test_error_response_required_fields(self):
        """ErrorResponse should require error and message."""
        from schemas.base import ErrorResponse
        
        # Should work with required fields
        error = ErrorResponse(
            error="TEST_ERROR",
            message="Test error message"
        )
        assert error.success is False
        assert error.error == "TEST_ERROR"
        
        # Should fail without required fields
        with pytest.raises(ValidationError):
            ErrorResponse()


class TestChatSchemas:
    """Tests for chat-related schemas."""
    
    def test_chat_request_valid(self):
        """Valid ChatRequest should be created."""
        from schemas.chat import ChatRequest
        
        req = ChatRequest(message="Hello", modality="text")
        assert req.message == "Hello"
        assert req.modality == "text"
    
    def test_chat_request_auto_trim(self):
        """ChatRequest should auto-trim strings."""
        from schemas.chat import ChatRequest
        
        req = ChatRequest(message="  Hello  ", modality="  text  ")
        assert req.message == "Hello"
        assert req.modality == "text"
    
    def test_chat_request_empty_message(self):
        """Empty message should fail validation."""
        from schemas.chat import ChatRequest
        
        with pytest.raises(ValidationError):
            ChatRequest(message="")
    
    def test_chat_request_invalid_modality(self):
        """Invalid modality should fail validation."""
        from schemas.chat import ChatRequest
        
        with pytest.raises(ValidationError):
            ChatRequest(message="Hello", modality="invalid")
    
    def test_chat_request_too_long(self):
        """Message exceeding max length should fail."""
        from schemas.chat import ChatRequest
        
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 5000)
    
    def test_chat_response_structure(self):
        """ChatResponse should have all required fields."""
        from schemas.chat import ChatResponse
        from datetime import datetime
        
        resp = ChatResponse(
            session_id="test",
            output="Test response",
            timestamp=datetime.now()
        )
        assert resp.session_id == "test"
        assert resp.output == "Test response"


class TestToolSchemas:
    """Tests for tool-related schemas."""
    
    def test_tool_request_valid(self):
        """Valid ToolRequest should be created."""
        from schemas.tool import ToolRequest
        
        req = ToolRequest(tool="weather", args={"city": "Beijing"})
        assert req.tool == "weather"
        assert req.args == {"city": "Beijing"}
    
    def test_tool_request_invalid_name(self):
        """Tool name with special chars should fail."""
        from schemas.tool import ToolRequest
        
        with pytest.raises(ValidationError):
            ToolRequest(tool="tool@name")
    
    def test_tool_request_starts_with_number(self):
        """Tool name starting with number should fail."""
        from schemas.tool import ToolRequest
        
        with pytest.raises(ValidationError):
            ToolRequest(tool="123tool")
    
    def test_tool_response_structure(self):
        """ToolResponse should have required fields."""
        from schemas.tool import ToolResponse
        
        resp = ToolResponse(result={"data": "test"}, tool="weather")
        assert resp.result == {"data": "test"}
        assert resp.tool == "weather"


class TestModelSchemas:
    """Tests for model configuration schemas."""
    
    def test_llm_config_valid_openai(self):
        """Valid OpenAI config should be created."""
        from schemas.model import LLMModelConfig
        
        config = LLMModelConfig(
            provider="openai",
            model_name="gpt-4o",
            api_key="sk-valid_key_1234567890"
        )
        assert config.provider == "openai"
        assert config.temperature == 0.7
    
    def test_llm_config_invalid_provider(self):
        """Invalid provider should fail validation."""
        from schemas.model import LLMModelConfig
        
        with pytest.raises(ValidationError):
            LLMModelConfig(
                provider="invalid_provider_xyz",
                model_name="test"
            )
    
    def test_llm_config_temperature_range(self):
        """Temperature outside [0, 2] should fail."""
        from schemas.model import LLMModelConfig
        
        # Below minimum
        with pytest.raises(ValidationError):
            LLMModelConfig(
                provider="openai",
                model_name="gpt-4o",
                temperature=-0.5
            )
        
        # Above maximum
        with pytest.raises(ValidationError):
            LLMModelConfig(
                provider="openai",
                model_name="gpt-4o",
                temperature=2.5
            )
    
    def test_llm_config_api_key_too_short(self):
        """API key shorter than 10 chars should fail."""
        from schemas.model import LLMModelConfig
        
        with pytest.raises(ValidationError):
            LLMModelConfig(
                provider="openai",
                model_name="gpt-4o",
                api_key="short"
            )
    
    def test_llm_config_extra_field_rejected(self):
        """Extra unknown fields should be rejected."""
        from schemas.model import LLMModelConfig
        
        with pytest.raises(ValidationError):
            LLMModelConfig(
                provider="openai",
                model_name="gpt-4o",
                invalid_field="should fail"
            )


class TestSchedulerSchemas:
    """Tests for scheduler schemas."""
    
    def test_create_task_request_valid(self):
        """Valid task creation should work."""
        from schemas.scheduler import CreateTaskRequest
        
        task = CreateTaskRequest(
            title="Test task",
            due_date="2026-06-25",
            priority="high"
        )
        assert task.title == "Test task"
        assert task.priority == "high"
    
    def test_create_task_request_invalid_priority(self):
        """Invalid priority should fail."""
        from schemas.scheduler import CreateTaskRequest
        
        with pytest.raises(ValidationError):
            CreateTaskRequest(
                title="Test",
                due_date="2026-06-25",
                priority="ultra_high"
            )
    
    def test_create_task_request_empty_title(self):
        """Empty title should fail."""
        from schemas.scheduler import CreateTaskRequest
        
        with pytest.raises(ValidationError):
            CreateTaskRequest(
                title="",
                due_date="2026-06-25"
            )


class TestFileSchemas:
    """Tests for file operation schemas."""
    
    def test_file_request_valid(self):
        """Valid file request should work."""
        from schemas.file import FileOperationRequest
        
        req = FileOperationRequest(path="notes/test.txt", operation="create")
        assert req.path == "notes/test.txt"
        assert req.operation == "create"
    
    def test_file_request_directory_traversal(self):
        """Directory traversal should be rejected."""
        from schemas.file import FileOperationRequest
        
        with pytest.raises(ValidationError):
            FileOperationRequest(path="../etc/passwd", operation="read")
    
    def test_file_request_absolute_path(self):
        """Absolute paths should be rejected."""
        from schemas.file import FileOperationRequest
        
        with pytest.raises(ValidationError):
            FileOperationRequest(path="/etc/passwd", operation="read")
    
    def test_file_request_invalid_operation(self):
        """Invalid operation should be rejected."""
        from schemas.file import FileOperationRequest
        
        with pytest.raises(ValidationError):
            FileOperationRequest(path="test.txt", operation="exec")


class TestPublicAPISchemas:
    """Tests for public API schemas."""
    
    def test_crypto_request_default_values(self):
        """CryptoRequest should have defaults."""
        from schemas.public_apis import CryptoRequest
        
        req = CryptoRequest()
        assert req.coin_id == "bitcoin"
        assert req.vs_currency == "usd"
    
    def test_exchange_request_valid(self):
        """Valid exchange request should work."""
        from schemas.public_apis import ExchangeRequest
        
        req = ExchangeRequest(
            from_currency="USD",
            to_currency="CNY",
            amount=100
        )
        assert req.from_currency == "USD"
        assert req.amount == 100
    
    def test_exchange_request_invalid_currency(self):
        """Invalid currency code should fail."""
        from schemas.public_apis import ExchangeRequest
        
        with pytest.raises(ValidationError):
            ExchangeRequest(
                from_currency="US",  # Only 2 chars
                to_currency="CNY"
            )
    
    def test_book_search_request_valid(self):
        """Valid book search should work."""
        from schemas.public_apis import BookSearchRequest
        
        req = BookSearchRequest(query="Python", limit=10)
        assert req.query == "Python"
        assert req.limit == 10
    
    def test_book_isbn_request_valid(self):
        """Valid ISBN should be accepted."""
        from schemas.public_apis import BookISBNRequest
        
        req = BookISBNRequest(isbn="978-0-596-51774-8")
        assert req.isbn == "978-0-596-51774-8"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
