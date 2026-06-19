"""
Admin and system monitoring schemas.
"""

from typing import Optional, Dict, Any, List
from pydantic import Field
from ..schemas.base import BaseSchema, ResponseBase


class CircuitBreakerStatus(BaseSchema):
    """Circuit breaker status for an endpoint."""
    
    endpoint: str = Field(..., description="Endpoint path")
    state: str = Field(..., description="Circuit state (closed/open/half-open)")
    failure_count: int = Field(default=0, ge=0, description="Current failure count")
    failure_threshold: int = Field(..., ge=1, description="Threshold to open circuit")
    last_failure: Optional[str] = Field(default=None, description="Last failure time")
    last_success: Optional[str] = Field(default=None, description="Last success time")
    recovery_timeout: int = Field(..., ge=0, description="Recovery timeout in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/chat",
                "state": "closed",
                "failure_count": 0,
                "failure_threshold": 5,
                "recovery_timeout": 30,
            }
        }


class CircuitBreakerResponse(ResponseBase):
    """Circuit breaker status response."""
    
    circuits: Dict[str, CircuitBreakerStatus] = Field(
        default_factory=dict, 
        description="Circuit breaker status per endpoint"
    )
    total_endpoints: int = Field(default=0, description="Total monitored endpoints")
    open_circuits: int = Field(default=0, description="Number of open circuits")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "circuits": {
                    "/api/chat": {
                        "endpoint": "/api/chat",
                        "state": "closed",
                        "failure_count": 0,
                        "failure_threshold": 5,
                        "recovery_timeout": 30,
                    }
                },
                "total_endpoints": 1,
                "open_circuits": 0,
            }
        }


class SystemHealth(BaseSchema):
    """System health status."""
    
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    websocket_enabled: bool = Field(default=True, description="WebSocket support")
    rate_limiting: str = Field(default="active", description="Rate limiting status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "J.A.R.V.I.S. Agent",
                "version": "0.2.0",
                "websocket_enabled": True,
                "rate_limiting": "active",
            }
        }
