"""
Memory and profile schemas.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class ProfileRequest(BaseSchema):
    """User profile update request."""
    
    key: str = Field(..., min_length=1, max_length=128, description="Preference key")
    value: Any = Field(..., description="Preference value")
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        # Keys should be alphanumeric with underscores
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('key must contain only letters, numbers, hyphens, and underscores')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "preferred_language",
                "value": "zh-CN",
            }
        }


class MemoryEpisode(BaseSchema):
    """Memory episode schema."""
    
    id: Optional[str] = Field(default=None, description="Episode identifier")
    timestamp: datetime = Field(..., description="When this episode occurred")
    user_input: Optional[str] = Field(default=None, description="User's input")
    agent_response: Optional[str] = Field(default=None, description="Agent's response")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context at the time")
    tools_used: Optional[List[str]] = Field(default=None, description="Tools invoked")
    sentiment: Optional[str] = Field(default=None, description="Detected sentiment")


class MemoryResponse(ResponseBase):
    """Memory retrieval response."""
    
    episodes: List[MemoryEpisode] = Field(default_factory=list, description="Memory episodes")
    total: int = Field(default=0, description="Total episodes available")
    retrieved: int = Field(default=0, description="Number of episodes returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "episodes": [
                    {
                        "id": "ep_001",
                        "timestamp": "2026-06-19T10:00:00",
                        "user_input": "查询北京天气",
                        "agent_response": "今天北京晴，气温25度",
                        "tools_used": ["weather"],
                        "sentiment": "neutral",
                    }
                ],
                "total": 50,
                "retrieved": 1,
            }
        }


class UserProfileResponse(ResponseBase):
    """User profile response."""
    
    profile: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    last_updated: Optional[datetime] = Field(default=None, description="Profile last updated")
    preferences_count: int = Field(default=0, description="Number of stored preferences")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "profile": {
                    "preferred_language": "zh-CN",
                    "timezone": "Asia/Shanghai",
                    "notifications_enabled": True,
                },
                "last_updated": "2026-06-19T11:30:00",
                "preferences_count": 3,
            }
        }
