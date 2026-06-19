"""
Base schema definitions - shared across all API schemas.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Base schema with common fields."""
    
    class Config:
        extra = "forbid"  # Reject unknown fields
        str_strip_whitespace = True  # Auto-trim string fields


class ResponseBase(BaseSchema):
    """Base response schema with metadata."""
    
    success: bool = Field(default=True, description="Request success status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2026-06-19T12:00:00",
                "request_id": "req_abc123",
            }
        }


class ErrorResponse(BaseSchema):
    """Standard error response schema."""
    
    success: bool = Field(default=False)
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "Invalid input parameters",
                "timestamp": "2026-06-19T12:00:00",
            }
        }
