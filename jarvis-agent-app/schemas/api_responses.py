"""
OpenAPI response model mappings for all API endpoints.
"""

from schemas.base import ErrorResponse
from schemas.chat import ChatResponse
from schemas.tool import ToolResponse, ToolsListResponse
from schemas.model import LLMStatusResponse, ModelConfigResponse
from schemas.scheduler import SchedulerTasksResponse
from schemas.data import DataResponse
from schemas.file import FileOperationResponse
from schemas.memory import MemoryResponse, UserProfileResponse
from schemas.admin import CircuitBreakerResponse, SystemHealth

# Response model mappings for OpenAPI documentation
RESPONSE_MODELS = {
    # Chat endpoints
    "/api/chat": {
        200: {"model": ChatResponse, "description": "Chat response with reasoning"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        504: {"model": ErrorResponse, "description": "Gateway timeout"},
    },
    "/api/tool": {
        200: {"model": ToolResponse, "description": "Tool execution result"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        504: {"model": ErrorResponse, "description": "Gateway timeout"},
    },
    "/api/tools": {
        200: {"model": ToolsListResponse, "description": "Available tools list"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    
    # Model configuration endpoints
    "/api/model/config": {
        200: {"model": ModelConfigResponse, "description": "Model configured successfully"},
        400: {"model": ErrorResponse, "description": "Invalid configuration"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Configuration failed"},
    },
    "/api/model/status": {
        200: {"model": LLMStatusResponse, "description": "Current model status"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/model/test": {
        200: {"model": ModelConfigResponse, "description": "Connection test successful"},
        400: {"model": ErrorResponse, "description": "Invalid configuration"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        502: {"model": ErrorResponse, "description": "Connection failed"},
    },
    "/api/model/reset": {
        200: {"model": ModelConfigResponse, "description": "Model configuration cleared"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    
    # Scheduler endpoints
    "/api/scheduler/task": {
        200: {"model": SchedulerTasksResponse, "description": "Task created"},
        400: {"model": ErrorResponse, "description": "Invalid task data"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/scheduler/tasks": {
        200: {"model": SchedulerTasksResponse, "description": "Tasks list with stats"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    
    # Data endpoints
    "/api/data/generate": {
        200: {"model": DataResponse, "description": "Generated data"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        504: {"model": ErrorResponse, "description": "Gateway timeout"},
    },
    "/api/data/analyze": {
        200: {"model": DataResponse, "description": "Analysis results"},
        400: {"model": ErrorResponse, "description": "Invalid dataset"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        504: {"model": ErrorResponse, "description": "Gateway timeout"},
    },
    
    # File endpoints
    "/api/files/create": {
        200: {"model": FileOperationResponse, "description": "File created"},
        400: {"model": ErrorResponse, "description": "Invalid path"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/files/read": {
        200: {"model": FileOperationResponse, "description": "File content"},
        400: {"model": ErrorResponse, "description": "Invalid path"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        404: {"model": ErrorResponse, "description": "File not found"},
    },
    
    # Memory endpoints
    "/api/memory/recent": {
        200: {"model": MemoryResponse, "description": "Recent memory episodes"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/memory/user-profile": {
        200: {"model": UserProfileResponse, "description": "User profile data"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/memory/profile": {
        200: {"model": UserProfileResponse, "description": "Profile updated"},
        400: {"model": ErrorResponse, "description": "Invalid profile data"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    
    # Weather endpoint
    "/api/weather": {
        200: {"model": DataResponse, "description": "Weather information"},
        400: {"model": ErrorResponse, "description": "Invalid city"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        504: {"model": ErrorResponse, "description": "Gateway timeout"},
    },
    
    # Public API endpoints
    "/api/public/crypto": {
        200: {"model": DataResponse, "description": "Crypto price data"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/crypto/list": {
        200: {"model": DataResponse, "description": "Crypto list"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/exchange": {
        200: {"model": DataResponse, "description": "Exchange rate data"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/exchange/currencies": {
        200: {"model": DataResponse, "description": "Supported currencies"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/dictionary": {
        200: {"model": DataResponse, "description": "Dictionary definition"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/holidays": {
        200: {"model": DataResponse, "description": "Holiday data"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/holidays/next": {
        200: {"model": DataResponse, "description": "Next holidays"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/joke": {
        200: {"model": DataResponse, "description": "Joke content"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/books/search": {
        200: {"model": DataResponse, "description": "Book search results"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/books/isbn": {
        200: {"model": DataResponse, "description": "Book by ISBN"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    "/api/public/capabilities": {
        200: {"description": "API capabilities list"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    
    # Admin endpoints
    "/api/admin/circuit-breaker": {
        200: {"model": CircuitBreakerResponse, "description": "Circuit breaker status"},
    },
    
    # Status endpoint
    "/api/status": {
        200: {"description": "System status"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    
    # Health check
    "/health": {
        200: {"model": SystemHealth, "description": "System health status"},
    },
}

# Common error responses for all endpoints
COMMON_ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad request"},
    401: {"model": ErrorResponse, "description": "Unauthorized (future feature)"},
    403: {"model": ErrorResponse, "description": "Forbidden (future feature)"},
    404: {"model": ErrorResponse, "description": "Not found"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
    503: {"model": ErrorResponse, "description": "Service unavailable"},
}
