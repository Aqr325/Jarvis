"""
J.A.R.V.I.S. Agent - API Schema Validation Layer
===================================================
Pydantic-based request/response validation for all API endpoints.

This module provides centralized schema definitions for input validation,
output serialization, and API documentation generation.
"""

from .base import BaseSchema, ResponseBase, ErrorResponse
from .chat import ChatRequest, ChatResponse, WebSocketMessage
from .tool import ToolRequest, ToolResponse, ToolsListResponse
from .model import (
    LLMModelConfig,
    LLMTestRequest,
    LLMStatusResponse,
    ModelConfigResponse,
)
from .scheduler import CreateTaskRequest, TaskResponse, SchedulerTasksResponse
from .data import AnalyzeRequest, GenerateDataRequest, DataResponse
from .file import FileOperationRequest, FileOperationResponse
from .memory import ProfileRequest, MemoryResponse, UserProfileResponse
from .public_apis import (
    CryptoRequest,
    ExchangeRequest,
    DictionaryRequest,
    HolidayRequest,
    JokeRequest,
    BookSearchRequest,
    BookISBNRequest,
)
from .admin import CircuitBreakerResponse, SystemHealth
from .errors import APIException, ErrorCode, ValidationErrorException
from .middleware import ValidationMiddleware, PaginationParams

__all__ = [
    # Base
    "BaseSchema", "ResponseBase", "ErrorResponse",
    # Chat
    "ChatRequest", "ChatResponse", "WebSocketMessage",
    # Tool
    "ToolRequest", "ToolResponse", "ToolsListResponse",
    # Model
    "LLMModelConfig", "LLMTestRequest", "LLMStatusResponse", "ModelConfigResponse",
    # Scheduler
    "CreateTaskRequest", "TaskResponse", "SchedulerTasksResponse",
    # Data
    "AnalyzeRequest", "GenerateDataRequest", "DataResponse",
    # File
    "FileOperationRequest", "FileOperationResponse",
    # Memory
    "ProfileRequest", "MemoryResponse", "UserProfileResponse",
    # Public APIs
    "CryptoRequest", "ExchangeRequest", "DictionaryRequest",
    "HolidayRequest", "JokeRequest", "BookSearchRequest", "BookISBNRequest",
    # Admin
    "CircuitBreakerResponse", "SystemHealth",
    # Errors
    "APIException", "ErrorCode", "ValidationErrorException",
    # Middleware
    "ValidationMiddleware", "PaginationParams",
]
