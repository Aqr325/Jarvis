"""
LLM model configuration schemas.
"""

from typing import Dict, Any, Optional, Literal
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class LLMModelConfig(BaseSchema):
    """External LLM model configuration schema."""
    
    provider: str = Field(..., description="LLM provider (openai/ollama/custom)")
    api_base_url: str = Field(default="", max_length=512, description="API base URL")
    model_name: str = Field(..., min_length=1, max_length=128, description="Model name/identifier")
    api_key: str = Field(default="", max_length=512, description="API key (empty for local models)")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    max_tokens: int = Field(default=4096, ge=1, le=100000, description="Max tokens per response")
    timeout: int = Field(default=60, ge=5, le=300, description="Request timeout in seconds")
    extra_params: Dict[str, Any] = Field(default={}, description="Additional provider-specific parameters")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"openai", "ollama", "custom", "anthropic", "gemini", "azure"}
        if v.lower() not in allowed:
            raise ValueError(f'provider must be one of {sorted(allowed)}')
        return v.lower()
    
    @field_validator('api_key')
    @classmethod
    def sanitize_api_key(cls, v: str) -> str:
        # Reject obviously invalid API keys (too short for real keys)
        if v and len(v) < 10:
            raise ValueError('api_key appears too short (minimum 10 characters for valid keys)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "api_base_url": "https://api.openai.com/v1",
                "model_name": "gpt-4o",
                "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
                "temperature": 0.7,
                "max_tokens": 4096,
                "timeout": 60,
            }
        }


class LLMTestRequest(BaseSchema):
    """LLM connection test request."""
    
    provider: str = Field(..., description="Provider to test")
    api_base: str = Field(default="", max_length=512, description="API base URL")
    model_name: str = Field(..., min_length=1, max_length=128, description="Model to test")
    api_key: str = Field(default="", max_length=512, description="API key")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        return v.lower()


class LLMStatusResponse(ResponseBase):
    """LLM status response schema."""
    
    provider: Optional[str] = Field(default=None, description="Configured provider")
    model_name: Optional[str] = Field(default=None, description="Configured model")
    api_base_url: Optional[str] = Field(default=None, description="API endpoint")
    connected: bool = Field(default=False, description="Connection status")
    last_tested: Optional[str] = Field(default=None, description="Last connection test time")
    capabilities: Optional[Dict[str, Any]] = Field(default=None, description="Model capabilities")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "provider": "openai",
                "model_name": "gpt-4o",
                "api_base_url": "https://api.openai.com/v1",
                "connected": True,
                "last_tested": "2026-06-19T12:00:00",
            }
        }


class ModelConfigResponse(ResponseBase):
    """Model configuration response."""
    
    status: str = Field(..., description="Configuration status")
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    api_base: Optional[str] = Field(default=None)
    message: str = Field(..., description="Human-readable message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status": "configured",
                "provider": "openai",
                "model": "gpt-4o",
                "message": "外部模型已配置: openai/gpt-4o",
            }
        }


class ModelCapability(BaseSchema):
    """LLM capability description."""
    
    name: str = Field(..., description="Capability name")
    supported: bool = Field(..., description="Whether model supports this")
    notes: Optional[str] = Field(default=None, description="Additional notes")
