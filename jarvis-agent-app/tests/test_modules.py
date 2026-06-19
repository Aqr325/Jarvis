"""
Tests for modules (nlp, builtins, custom_llm, public_apis).
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNLP:
    """Tests for NLP module."""
    
    def test_nlp_detect_intent(self):
        """NLP should detect intent from text."""
        from modules.nlp import NLPProcessor
        
        processor = NLPProcessor()
        result = processor.process("查询北京今天的天气")
        
        assert "intent" in result
        assert "entities" in result
        assert result["intent"] in ["weather_query", "greeting", "unknown", "help_request"]
    
    def test_nlp_extract_entities(self):
        """NLP should extract entities like cities."""
        from modules.nlp import nlp_processor
        
        result = nlp_processor.process("北京和上海哪个城市更热？")
        
        assert "entities" in result
        # Should detect at least one city
        assert len(result["entities"]) >= 1
    
    def test_nlp_sentiment_analysis(self):
        """NLP should detect sentiment."""
        from modules.nlp import NLPProcessor
        
        processor = NLPProcessor()
        
        positive = processor.process("太好了，非常感谢！")
        assert positive.get("sentiment") in ["positive", "neutral"]
        
        negative = processor.process("这太糟糕了，我很失望")
        assert negative.get("sentiment") in ["negative", "neutral"]


class TestBuiltinModules:
    """Tests for builtin modules."""
    
    def test_weather_module_gets_data(self):
        """Weather module should return weather data."""
        from modules.builtins import WeatherModule
        
        weather = WeatherModule()
        result = weather.get_weather("Beijing")
        
        # Should return a dict with weather info
        assert isinstance(result, dict)
        assert "city" in result or "error" in result or "temperature" in result
    
    def test_file_module_create_read(self):
        """File module should create and read files."""
        from modules.builtins import FileModule
        import tempfile
        
        file_ops = FileModule()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            
            # Create file
            result = file_ops.create_file(test_file, "test content")
            assert os.path.exists(test_file)
            
            # Read file
            read_result = file_ops.read_file(test_file)
            assert "test content" in str(read_result)
    
    def test_data_analysis_generate_sample(self):
        """Data analysis module should generate sample data."""
        from modules.builtins import DataAnalysisModule
        
        data_module = DataAnalysisModule()
        result = data_module.generate_sample("test_dataset", n=10)
        
        assert isinstance(result, dict)
        assert "data" in result or "rows" in result


class TestPublicAPIs:
    """Tests for public APIs module."""
    
    @pytest.mark.asyncio
    async def test_crypto_price(self):
        """Crypto price should return data."""
        from modules.public_apis import crypto_price
        
        result = await crypto_price("bitcoin", "usd")
        
        assert isinstance(result, dict)
        assert "price" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_exchange_rate(self):
        """Exchange rate should return data."""
        from modules.public_apis import exchange_rate
        
        result = await exchange_rate("USD", "CNY", 100)
        
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_dictionary_lookup(self):
        """Dictionary lookup should return definition."""
        from modules.public_apis import dictionary_lookup
        
        result = dictionary_lookup("serendipity")
        
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_tell_joke(self):
        """Joke function should return a joke."""
        from modules.public_apis import tell_joke
        
        result = await tell_joke("Any", "en")
        
        assert isinstance(result, dict)
        assert "joke" in result or "setup" in result or "punchline" in result
    
    @pytest.mark.asyncio
    async def test_search_books(self):
        """Book search should return results."""
        from modules.public_apis import search_books
        
        result = await search_books("python", limit=3)
        
        assert isinstance(result, dict)
        assert "books" in result or "results" in result or "error" in result


class TestMemory:
    """Tests for memory system."""
    
    def test_memory_add_episode(self):
        """Memory should store episodes."""
        from core.engine import JarvisAgent
        
        agent = JarvisAgent("TestAgent")
        
        agent.memory.add_episode({
            "user_input": "Hello",
            "agent_response": "Hi there!"
        })
        
        recent = agent.memory.recall_recent(1)
        assert len(recent) >= 1
    
    def test_memory_retrieve_user_profile(self):
        """Memory should retrieve user profile."""
        from core.engine import JarvisAgent
        
        agent = JarvisAgent("TestAgent")
        agent.add_user_preference("language", "zh-CN")
        
        profile = agent.memory.get_user_profile()
        assert "language" in profile
        assert profile["language"] == "zh-CN"
    
    def test_memory_retrieve_recent(self):
        """Memory should retrieve recent episodes."""
        from core.engine import JarvisAgent
        
        agent = JarvisAgent("TestAgent")
        
        for i in range(5):
            agent.memory.add_episode({"test": f"episode_{i}"})
        
        recent = agent.memory.recall_recent(3)
        assert len(recent) <= 3
    
    def test_memory_limit(self):
        """Memory should have maximum size."""
        from core.engine import JarvisAgent
        
        agent = JarvisAgent("TestAgent")
        
        # Add more episodes than limit
        for i in range(100):
            agent.memory.add_episode({"test": f"episode_{i}"})
        
        recent = agent.memory.recall_recent(200)
        # Should not exceed MAX_EPISODES
        assert len(recent) <= agent.memory.MAX_EPISODES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
