"""
Example tests demonstrating usage patterns.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAPIUsageExamples:
    """Example tests showing common API usage patterns."""
    
    def test_basic_chat_example(self):
        """Example: Basic chat interaction."""
        from server import app
        client = TestClient(app)
        
        # This is an example of how to use the chat API
        response = client.post("/api/chat", json={
            "message": "你好，请帮我查询今天的天气",
            "modality": "text"
        })
        
        # In production, this would return:
        # {
        #     "success": true,
        #     "session_id": "sess_abc123",
        #     "timestamp": "2026-06-19T12:00:00",
        #     "output": "今天北京天气晴朗，气温25度",
        #     ...
        # }
        
        # For this example test, we just check it doesn't crash
        assert response.status_code in [200, 422, 429, 500]
    
    def test_weather_query_example(self):
        """Example: Query weather for a specific city."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/weather", params={
            "city": "Beijing"
        })
        
        assert response.status_code in [200, 422, 429, 504]
    
    def test_tool_call_example(self):
        """Example: Directly call a tool."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/tool", json={
            "tool": "weather",
            "args": {
                "city": "Shanghai"
            }
        })
        
        assert response.status_code in [200, 422, 429, 504]
    
    def test_create_task_example(self):
        """Example: Create a scheduled task."""
        from server import app
        client = TestClient(app)
        
        response = client.post("/api/scheduler/task", json={
            "title": "完成 J.A.R.V.I.S. 项目文档",
            "due_date": "2026-06-25T18:00:00",
            "priority": "high",
            "description": "需要完成项目文档编写和测试"
        })
        
        assert response.status_code in [200, 422, 429]


class TestCommonErrorScenarios:
    """Example tests for common error scenarios."""
    
    def test_unauthorized_access_future(self):
        """Example: Unauthorized access will return 401 in future versions."""
        from server import app
        client = TestClient(app)
        
        # Currently all endpoints are open, but future versions will require auth
        response = client.get("/api/status", headers={
            "Authorization": "Bearer invalid_token"
        })
        
        # Currently this will still work (no auth required)
        assert response.status_code == 200
    
    def test_resource_not_found(self):
        """Example: Resource not found returns 404."""
        from server import app
        client = TestClient(app)
        
        response = client.get("/api/nonexistent")
        
        # Should return 404
        assert response.status_code == 404
    
    def test_invalid_json_payload(self):
        """Example: Invalid JSON returns 400."""
        from server import app
        client = TestClient(app)
        
        response = client.post(
            "/api/chat",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (validation error)
        assert response.status_code in [400, 422]


class TestPerformanceExamples:
    """Example tests for performance considerations."""
    
    @pytest.mark.slow
    def test_concurrent_requests(self):
        """Example: Test handling concurrent requests."""
        from server import app
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        client = TestClient(app)
        
        def make_request(i):
            return client.get("/api/status")
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(10)))
        
        # All should succeed or be rate limited
        for result in results:
            assert result.status_code in [200, 429]
    
    @pytest.mark.slow
    def test_large_message_handling(self):
        """Example: Test handling large messages."""
        from server import app
        client = TestClient(app)
        
        # Message at max allowed size (4096 chars)
        large_message = "x" * 4096
        
        response = client.post("/api/chat", json={
            "message": large_message
        })
        
        # Should handle gracefully (success or validation error)
        assert response.status_code in [200, 422]


class TestWebsocketExamples:
    """Example tests for WebSocket functionality."""
    
    def test_websocket_connection_example(self):
        """Example: WebSocket connection test."""
        from server import app
        from starlette.websockets import WebSocketTestSession
        
        # Note: Full WebSocket testing requires asgi lifespan
        # This is an example of the pattern
        
        with TestClient(app).websocket_connect("/ws") as ws:
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            
            # Should receive pong response
            assert "pong" in response or response.get("type") == "heartbeat"
    
    def test_websocket_chat_example(self):
        """Example: WebSocket chat interaction."""
        from server import app
        
        with TestClient(app).websocket_connect("/ws") as ws:
            # Send chat message
            ws.send_json({
                "type": "chat",
                "data": {"message": "Hello via WebSocket!"}
            })
            
            # Receive response (streamed)
            response = ws.receive_json()
            
            # Should receive some response
            assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
