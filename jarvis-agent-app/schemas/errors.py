"""
API error handling and exception definitions.
"""

from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import traceback


class ErrorCode(str, Enum):
    """Standard error codes."""
    
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "GATEWAY_TIMEOUT"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"


class APIException(HTTPException):
    """Base exception for API errors."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error": error_code.value,
                "message": message,
                "details": details,
            },
            headers=headers,
        )


class ValidationErrorException(APIException):
    """Raised when request validation fails."""
    
    def __init__(self, validation_error: ValidationError):
        errors = []
        for err in validation_error.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            })
        
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=f"Validation failed with {len(errors)} error(s)",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": errors},
        )


# Exception handler middleware
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.
    Returns standardized error responses.
    """
    # Pydantic validation errors
    if isinstance(exc, ValidationError):
        raise ValidationErrorException(exc)
    
    # HTTP exceptions (our custom APIException inherits from this)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail.get("error", "UNKNOWN_ERROR") if isinstance(exc.detail, dict) else "UNKNOWN_ERROR",
                "message": exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail),
                "details": exc.detail.get("details") if isinstance(exc.detail, dict) else None,
            },
            headers=exc.headers,
        )
    
    # Log the exception
    import logging
    logger = logging.getLogger("jarvis.error_handler")
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}\n"
        f"{traceback.format_exc()}"
    )
    
    # Internal server error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": ErrorCode.INTERNAL_ERROR.value,
            "message": "Internal server error. Please try again later.",
            "details": None,  # Don't leak internal details
        },
    )
