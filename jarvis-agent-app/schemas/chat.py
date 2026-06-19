"""
Chat-related schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class ChatRequest(BaseSchema):
    """Chat request schema with validation."""
    
    message: str = Field(..., min_length=1, max_length=4096, description="User input message")
    modality: str = Field(default="text", description="Input modality (text/image/audio)")
    session_id: Optional[str] = Field(default=None, max_length=64, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    
    @field_validator('modality')
    @classmethod
    def validate_modality(cls, v: str) -> str:
        allowed = {"text", "image", "audio", "video"}
        if v not in allowed:
            raise ValueError(f'modality must be one of {allowed}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好，请帮我查询今天的天气",
                "modality": "text",
                "session_id": "sess_abc123",
            }
        }


class ReasoningOutput(BaseSchema):
    """Reasoning output structure."""
    
    output: str = Field(..., description="Final response output")
    reasoning: Optional[str] = Field(default=None, description="Chain of thought reasoning")
    nlp_pipeline: Optional[Dict[str, Any]] = Field(default=None, description="NLP analysis results")
    tools_used: Optional[List[str]] = Field(default=None, description="Tools that were invoked")
    confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Confidence score")


class ChatResponse(ResponseBase):
    """Chat response schema."""
    
    session_id: str = Field(..., description="Active session identifier")
    output: str = Field(..., description="Agent response content")
    reasoning: Optional[ReasoningOutput] = Field(default=None, description="Reasoning details")
    nlp: Optional[Dict[str, Any]] = Field(default=None, description="NLP analysis")
    timestamp: datetime = Field(..., description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "sess_abc123",
                "timestamp": "2026-06-19T12:00:00",
                "output": "今天北京天气晴朗，气温25度...",
                "reasoning": {
                    "output": "今天北京天气晴朗，气温25度",
                    "reasoning": "意图识别：天气查询",
                    "confidence": 0.95,
                },
                "nlp": {
                    "intent": "weather_query",
                    "entities": {"city": "北京"},
                    "sentiment": "neutral",
                    "confidence": 0.92,
                },
            }
        }


class WebSocketMessage(BaseSchema):
    """WebSocket message schema."""
    
    type: str = Field(..., description="Message type (chat/tool_call/ping)")
    data: Dict[str, Any] = Field(..., description="Message payload")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "chat",
                "data": {
                    "message": "你好",
                    "session_id": "sess_123",
                }
            }
        }
