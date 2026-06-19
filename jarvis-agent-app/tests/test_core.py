"""
Tests for core modules (engine, rate_limiter, timeout, websocket_manager).
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestJarvisAgent:
    """Tests for JarvisAgent class."""
    
    def test_agent_initialization(self):
        """Agent should initialize with name."""
        from core.engine import JarvisAgent
        agent = JarvisAgent("TestAgent")
        assert agent.name == "TestAgent"
    
    def test_agent_process_returns_response(self):
        """Agent process should return response dict."""
        from core.engine import JarvisAgent
        agent = JarvisAgent("TestAgent")
        
        result = agent.process("Hello")
        assert "reasoning" in result
        assert "output" in result["reasoning"]
    
    def test_agent_register_tool(self):
        """Agent should be able to register tools."""
        from core.engine import JarvisAgent
        agent = JarvisAgent("TestAgent")
        
        agent.execution.register_tool("test_tool", lambda: "result")
        assert "test_tool" in agent.execution.tools
    
    def test_agent_call_tool(self):
        """Agent should call registered tools."""
        from core.engine import JarvisAgent
        agent = JarvisAgent("TestAgent")
        
        agent.execution.register_tool("add", lambda a, b: a + b)
        result = agent.call_tool("add", a=5, b=3)
        assert result == 8


class TestDecisionStrategy:
    """Tests for decision strategy enum."""
    
    def test_decision_strategies_exist(self):
        """All decision strategies should be defined."""
        from core.engine import DecisionStrategy
        
        strategies = list(DecisionStrategy)
        assert DecisionStrategy.BUILTIN in strategies
        assert DecisionStrategy.CUSTOM_LLM in strategies
    
    def test_decision_strategy_values(self):
        """Decision strategies should have correct string values."""
        from core.engine import DecisionStrategy
        
        assert DecisionStrategy.BUILTIN.value == "builtin"
        assert DecisionStrategy.CUSTOM_LLM.value == "custom_llm"


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_rate_limiter_allows_within_limit(self):
        """Rate limiter should allow requests within limit."""
        from core.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        # Default limit is 100 requests per minute for general
        for i in range(10):
            result = limiter.is_allowed("test_client", "general")
            assert result["allowed"] is True
    
    def test_rate_limiter_blocks_over_limit(self):
        """Rate limiter should block requests over limit."""
        from core.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Create a custom bucket with low limit
        bucket_id = "test_bucket"
        limiter._buckets[bucket_id] = {"tokens": 3, "last_refill": asyncio.get_event_loop().time()}
        limiter.bucket_limits[bucket_id] = 3
        
        # Should allow 3 requests
        for i in range(3):
            result = limiter.is_allowed("test_client", bucket_id)
            assert result["allowed"] is True
        
        # 4th request should be blocked
        result = limiter.is_allowed("test_client", bucket_id)
        assert result["allowed"] is False
        assert result["retry_after"] > 0


class TestTimeoutManager:
    """Tests for TimeoutManager class."""
    
    @pytest.mark.asyncio
    async def test_timeout_within_limit(self):
        """Operations within timeout should succeed."""
        from core.timeout import TimeoutManager
        
        manager = TimeoutManager()
        manager.configs["test_endpoint"] = {"timeout": 5.0}
        
        async def quick_task():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await manager.execute_with_timeout(quick_task(), "test_endpoint", "client_1")
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        """Operations exceeding timeout should raise TimeoutError."""
        from core.timeout import TimeoutManager
        
        manager = TimeoutManager()
        manager.configs["slow_endpoint"] = {"timeout": 0.5}
        
        async def slow_task():
            await asyncio.sleep(2.0)
            return "should not reach here"
        
        with pytest.raises(asyncio.TimeoutError):
            await manager.execute_with_timeout(slow_task(), "slow_endpoint", "client_1")


class TestWebSocketManager:
    """Tests for WebSocketManager class."""
    
    @pytest.mark.asyncio
    async def test_websocket_connect(self):
        """WebSocketManager should connect clients."""
        from core.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        
        # Create a mock websocket
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.send_text = AsyncMock()
        
        client_id = await manager.connect(mock_ws, "test_client_123")
        assert client_id == "test_client_123"
        assert "test_client_123" in manager.connections
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect(self):
        """WebSocketManager should disconnect clients."""
        from core.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        
        mock_ws = AsyncMock()
        await manager.connect(mock_ws, "test_disconnect")
        
        await manager.disconnect("test_disconnect")
        assert "test_disconnect" not in manager.connections
    
    @pytest.mark.asyncio
    async def test_send_to_client(self):
        """WebSocketManager should send messages to clients."""
        from core.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws, "test_send")
        
        await manager.send_to_client("test_send", "chat", {"message": "Hello"})
        mock_ws.send_json.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
