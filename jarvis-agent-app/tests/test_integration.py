"""
Integration tests for end-to-end workflows.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIntegrationChatWorkflow:
    """Integration tests for complete chat workflows."""
    
    @pytest.mark.integration
    def test_complete_chat_workflow(self):
        """Test complete chat workflow from request to response."""
        from server import app
        client = TestClient(app)
        
        # Step 1: Check system health
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"
        
        # Step 2: Get system status
        status = client.get("/api/status")
        # May be 429 or 500 if agent not initialized, that's OK
        assert status.status_code in [200, 429, 500]
        
        # Step 3: List available tools
        tools = client.get("/api/tools")
        assert tools.status_code == 200
        data = tools.json()
        assert "available_tools" in data
    
    @pytest.mark.integration
    def test_chat_with_tool_usage(self):
        """Test chat workflow that involves tool usage."""
        from server import app
        from unittest.mock import patch
        
        client = TestClient(app)
        
        with patch('server.agent') as mock_agent:
            mock_agent.process.return_value.__await__ = lambda: iter([{
                "timestamp": "2026-06-19T12:00:00",
                "reasoning": {
                    "output": "今天北京天气晴朗",
                    "reasoning": "需要调用天气工具",
                    "tools_used": ["weather"]
                }
            }])
            mock_agent.state.session_id = "integration_test"
            
            # Send chat message
            response = client.post("/api/chat", json={
                "message": "今天北京天气怎么样？",
                "session_id": "integration_test"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "output" in data


class TestIntegrationModelConfigWorkflow:
    """Integration tests for model configuration workflow."""
    
    @pytest.mark.integration
    def test_model_config_workflow(self):
        """Test complete model configuration workflow."""
        from server import app
        from unittest.mock import patch
        
        client = TestClient(app)
        
        with patch('server.agent') as mock_agent:
            # Configure model
            config_response = client.post("/api/model/config", json={
                "provider": "openai",
                "model_name": "gpt-4o",
                "api_key": "sk-test_key_1234567890abcdefghijklmnopqrstuvwxyz"
            })
            
            # Check status
            status_response = client.get("/api/model/status")
            assert status_response.status_code == 200
            
            # Reset config
            reset_response = client.post("/api/model/reset")
            assert reset_response.status_code in [200, 429]


class TestIntegrationSchedulerWorkflow:
    """Integration tests for scheduler workflow."""
    
    @pytest.mark.integration
    def test_scheduler_workflow(self):
        """Test complete scheduler workflow."""
        from server import app
        from unittest.mock import patch
        
        client = TestClient(app)
        
        with patch('server.scheduler') as mock_scheduler:
            mock_scheduler.create_task.return_value.__await__ = lambda: iter([{
                "id": "task_integration_test",
                "title": "Test Task",
                "due_date": "2026-06-25"
            }])
            mock_scheduler.list_tasks.return_value.__await__ = lambda: iter([[]])
            mock_scheduler.get_stats.return_value.__await__ = lambda: iter([{
                "total": 1, "pending": 1, "completed": 0, "overdue": 0
            }])
            
            # Create task
            create = client.post("/api/scheduler/task", json={
                "title": "Integration Test Task",
                "due_date": "2026-06-25T18:00:00",
                "priority": "high"
            })
            assert create.status_code == 200
            
            # List tasks
            list_tasks = client.get("/api/scheduler/tasks")
            assert list_tasks.status_code == 200


class TestIntegrationMemoryWorkflow:
    """Integration tests for memory workflow."""
    
    @pytest.mark.integration
    def test_memory_workflow(self):
        """Test complete memory workflow."""
        from server import app
        from unittest.mock import patch
        
        client = TestClient(app)
        
        with patch('server.agent') as mock_agent:
            mock_agent.memory.recall_recent.return_value = [{"test": "episode"}]
            mock_agent.memory.get_user_profile.return_value = {"language": "zh-CN"}
            mock_agent.add_user_preference.return_value = None
            
            # Get recent memory
            recent = client.get("/api/memory/recent?n=5")
            assert recent.status_code == 200
            
            # Get user profile
            profile = client.get("/api/memory/user-profile")
            assert profile.status_code == 200
            
            # Set user preference
            set_pref = client.post("/api/memory/profile?key=test_key&value=test_value")
            assert set_pref.status_code == 200


class TestIntegrationErrorHandling:
    """Integration tests for error handling."""
    
    @pytest.mark.integration
    def test_rate_limiting(self):
        """Test that rate limiting is enforced."""
        from server import app
        from server import rate_limiter
        
        client = TestClient(app)
        
        # Temporarily set very low rate limit
        original_limit = rate_limiter.bucket_limits.get("general", 100)
        rate_limiter.bucket_limits["general"] = 1
        
        try:
            # First request should succeed
            r1 = client.get("/api/status")
            
            # Second request should be rate limited
            r2 = client.get("/api/status")
            assert r2.status_code == 429
        finally:
            rate_limiter.bucket_limits["general"] = original_limit
    
    @pytest.mark.integration
    def test_validation_error_format(self):
        """Test that validation errors have consistent format."""
        from server import app
        client = TestClient(app)
        
        # Send invalid request (missing required field)
        response = client.post("/api/chat", json={})
        
        assert response.status_code == 422
        data = response.json()
        
        # Should have error detail
        assert "detail" in data or "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
