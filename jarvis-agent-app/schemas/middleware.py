"""
Schema validation middleware and utilities.
"""

import uuid
import time
from typing import Callable, Any, Dict
from datetime import datetime
from functools import wraps
from fastapi import Request, HTTPException
from pydantic import BaseModel, ValidationError


class ValidationMiddleware:
    """
    Middleware for request validation utilities.
    """
    
    @staticmethod
    def generate_request_id() -> str:
        """Generate a unique request ID."""
        return f"req_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def extract_client_info(request: Request) -> Dict[str, Any]:
        """Extract client identification info."""
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return {
            "ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "request_id": ValidationMiddleware.generate_request_id(),
        }


def validate_request_schema(schema_class: type):
    """
    Decorator for automatic request validation.
    
    Usage:
        @app.post("/api/chat")
        @validate_request_schema(ChatRequest)
        async def chat(request: ChatRequest):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # The schema validation is already handled by FastAPI's type hints
            # This decorator can add additional pre-processing if needed
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def response_with_metadata(response_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add standard metadata to response.
    
    Args:
        response_data: The actual response data
        request_id: Optional request ID for tracing
    
    Returns:
        Response dict with metadata
    """
    return {
        **response_data,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
    }


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    def model_post_init(self, __context: Any) -> None:
        # Enforce reasonable limits
        self.page = max(1, self.page)
        self.page_size = max(1, min(100, self.page_size))
        self.sort_order = "asc" if self.sort_order.lower() == "asc" else "desc"


class SortParams(BaseModel):
    """Sorting parameters."""
    
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    def model_post_init(self, __context: Any) -> None:
        self.sort_order = "asc" if self.sort_order.lower() == "asc" else "desc"
