"""
File operation schemas.
"""

from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class FileOperationRequest(BaseSchema):
    """File operation request schema."""
    
    path: str = Field(..., min_length=1, max_length=1024, description="File path")
    content: Optional[str] = Field(default=None, max_length=100000, description="File content for create/edit")
    operation: str = Field(default="create", description="Operation type")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        # Basic path security: no directory traversal
        if '..' in v:
            raise ValueError('path cannot contain directory traversal sequences')
        if v.startswith('/') or v.startswith('~'):
            raise ValueError('absolute paths are not allowed for security')
        return v
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        allowed = {"create", "read", "list", "delete", "move"}
        if v.lower() not in allowed:
            raise ValueError(f'operation must be one of {sorted(allowed)}')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": "notes/todo.txt",
                "content": "Buy groceries\nCall mom",
                "operation": "create",
            }
        }


class FileInfo(BaseSchema):
    """File information schema."""
    
    name: str = Field(..., description="File name")
    path: str = Field(..., description="Full path")
    size: Optional[int] = Field(default=None, description="File size in bytes")
    modified: Optional[str] = Field(default=None, description="Last modified time")
    is_directory: bool = Field(default=False, description="Whether this is a directory")


class FileOperationResponse(ResponseBase):
    """File operation response schema."""
    
    result: Dict[str, Any] = Field(..., description="Operation result")
    file_info: Optional[FileInfo] = Field(default=None, description="File information")
    files: Optional[List[FileInfo]] = Field(default=None, description="Directory listing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": {"status": "created", "path": "notes/todo.txt"},
                "file_info": {
                    "name": "todo.txt",
                    "path": "notes/todo.txt",
                    "size": 25,
                    "modified": "2026-06-19T12:00:00",
                    "is_directory": False,
                },
            }
        }
