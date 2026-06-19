"""
Custom LLM Integration Module
------------------------------
Supports external LLM providers (OpenAI-compatible APIs, Ollama, etc.)
to extend the Agent's reasoning capabilities.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.custom_llm")


@dataclass
class LLMConfig:
    """Configuration for an external LLM connection."""
    provider: str = "openai"  # "openai" | "ollama" | "custom"
    api_base: str = ""
    model_name: str = ""
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    headers: Dict[str, str] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.headers:
            if self.provider == "openai" or self.provider == "custom":
                # Only add Authorization header if api_key is provided
                headers = {"Content-Type": "application/json"}
                if self.api_key and self.api_key.strip():
                    headers["Authorization"] = f"Bearer {self.api_key}"
                self.headers = headers
            elif self.provider == "ollama":
                self.headers = {"Content-Type": "application/json"}
            else:
                self.headers = {"Content-Type": "application/json"}


@dataclass
class LLMResponse:
    """Standardized response from an LLM provider."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "success": self.success,
            "error": self.error,
        }


class LLMClient:
    """Client for interacting with external LLM APIs."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 60  # seconds
    
    async def chat_completion(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Send a chat completion request to the LLM provider."""
        import httpx
        
        timestamp = time.time()
        # Proper rate limit window check: reset counter when window expires
        if timestamp - self._last_request_time >= self._rate_limit_window:
            self._request_count = 1  # New window, start fresh
        else:
            self._request_count += 1  # Still in same window, increment count
        
        self._last_request_time = timestamp
        
        # Log rate limit status
        if self._request_count > 10:
            logger.warning(
                f"Rate limit warning: {self._request_count} requests in last {self._rate_limit_window}s"
            )
        
        try:
            if self.config.provider == "openai" or self.config.provider == "custom":
                return await self._openai_compatible(messages)
            elif self.config.provider == "ollama":
                return await self._ollama(messages)
            else:
                return LLMResponse(
                    content="",
                    model=self.config.model_name,
                    success=False,
                    error=f"Unsupported provider: {self.config.provider}"
                )
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return LLMResponse(
                content="",
                model=self.config.model_name,
                success=False,
                error=str(e)
            )
    
    async def _openai_compatible(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Handle OpenAI-compatible API requests."""
        import httpx
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            **self.config.extra_params
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                self.config.api_base.rstrip("/") + "/chat/completions",
                headers=self.config.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            choice = data["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.config.model_name),
                usage=data.get("usage", {}),
                finish_reason=choice.get("finish_reason", ""),
                success=True
            )
    
    async def _ollama(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Handle Ollama API requests."""
        import httpx
        
        # Convert OpenAI-style messages to Ollama format
        ollama_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        
        payload = {
            "model": self.config.model_name,
            "messages": ollama_messages,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            },
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                self.config.api_base.rstrip("/") + "/api/chat",
                headers=self.config.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=self.config.model_name,
                success=True
            )
    
    async def test_connection(self) -> bool:
        """Test the LLM connection with a simple request."""
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one word."}
        ]
        response = await self.chat_completion(test_messages)
        return response.success and len(response.content) > 0


# Global LLM client manager
class LLMManager:
    """Manages LLM configurations and clients."""
    
    def __init__(self):
        self._config: Optional[LLMConfig] = None
        self._client: Optional[LLMClient] = None
    
    @property
    def config(self) -> Optional[LLMConfig]:
        return self._config
    
    @property
    def client(self) -> Optional[LLMClient]:
        return self._client
    
    def configure(self, config: LLMConfig):
        """Set up a new LLM configuration and create a client."""
        self._config = config
        self._client = LLMClient(config)
        logger.info(f"LLM configured: provider={config.provider}, model={config.model_name}")
    
    def clear(self):
        """Clear the current LLM configuration."""
        self._config = None
        self._client = None
        logger.info("LLM configuration cleared")
    
    def is_configured(self) -> bool:
        """Check if an LLM is configured."""
        return self._client is not None
    
    async def test_connection(self) -> bool:
        """Test the LLM connection."""
        if not self._client:
            return False
        return await self._client.test_connection()
    
    async def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Send a chat request using the configured LLM."""
        if not self._client:
            return LLMResponse(
                content="",
                model="none",
                success=False,
                error="No LLM configured"
            )
        return await self._client.chat_completion(messages)


# Singleton instance
llm_manager = LLMManager()