"""
Tool-related schemas.
"""

from typing import Dict, Any, List, Optional
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class ToolRequest(BaseSchema):
    """Tool call request schema."""
    
    tool: str = Field(..., min_length=1, max_length=64, pattern=r'^[a-zA-Z][a-zA-Z0-9_]*$', description="Tool name")
    args: Dict[str, Any] = Field(default={}, description="Tool arguments")
    
    @field_validator('tool')
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        # Tools must start with letter, contain only alphanumeric and underscore
        if not v.replace('_', '').isalnum():
            raise ValueError('tool name must contain only letters, numbers, and underscores')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool": "weather",
                "args": {
                    "city": "Beijing"
                }
            }
        }


class ToolDefinition(BaseSchema):
    """Tool definition for listing."""
    
    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(default=None, description="Tool description")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Parameter schema")
    category: Optional[str] = Field(default=None, description="Tool category")


class ToolResponse(ResponseBase):
    """Tool call response schema."""
    
    result: Dict[str, Any] = Field(..., description="Tool execution result")
    tool: Optional[str] = Field(default=None, description="Called tool name")
    duration_ms: Optional[float] = Field(default=None, ge=0, description="Execution time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": {
                    "city": "Beijing",
                    "temperature": 25,
                    "condition": "Sunny"
                },
                "tool": "weather",
                "duration_ms": 150.5,
            }
        }


class ToolsListResponse(ResponseBase):
    """Available tools list response."""
    
    available_tools: List[ToolDefinition] = Field(..., description="List of available tools")
    total: int = Field(..., description="Total number of tools")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "available_tools": [
                    {"name": "weather", "description": "Get weather information", "category": "external"}
                ],
                "total": 1,
            }
        }
