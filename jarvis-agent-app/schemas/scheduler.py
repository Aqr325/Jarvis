"""
Scheduler task schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class CreateTaskRequest(BaseSchema):
    """Create scheduler task request."""
    
    title: str = Field(..., min_length=1, max_length=256, description="Task title")
    due_date: str = Field(..., max_length=64, description="Due date (ISO 8601 or natural language)")
    priority: str = Field(default="medium", description="Task priority level")
    description: Optional[str] = Field(default=None, max_length=2048, description="Task description")
    tags: Optional[List[str]] = Field(default=None, max_length=10, description="Task tags")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "urgent"}
        if v.lower() not in allowed:
            raise ValueError(f'priority must be one of {sorted(allowed)}')
        return v.lower()
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: str) -> str:
        # Accept ISO 8601 or natural language (e.g., "tomorrow", "next Monday")
        # Validation happens at processing time
        if len(v) > 64:
            raise ValueError('due_date too long')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "完成 J.A.R.V.I.S. Agent 项目审计",
                "due_date": "2026-06-25T18:00:00",
                "priority": "high",
                "description": "进行全面安全审计和性能优化",
                "tags": ["project", "review"],
            }
        }


class TaskResponse(BaseSchema):
    """Task response schema."""
    
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    due_date: str = Field(..., description="Due date")
    priority: str = Field(..., description="Priority level")
    status: str = Field(default="pending", description="Task status")
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "task_abc123",
                "title": "完成 J.A.R.V.I.S. Agent 项目审计",
                "due_date": "2026-06-25T18:00:00",
                "priority": "high",
                "status": "pending",
                "created_at": "2026-06-19T12:00:00",
            }
        }


class SchedulerStats(BaseSchema):
    """Scheduler statistics."""
    
    total: int = Field(default=0, description="Total tasks")
    pending: int = Field(default=0, description="Pending tasks")
    completed: int = Field(default=0, description="Completed tasks")
    overdue: int = Field(default=0, description="Overdue tasks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "pending": 5,
                "completed": 4,
                "overdue": 1,
            }
        }


class SchedulerTasksResponse(ResponseBase):
    """List tasks response."""
    
    tasks: List[TaskResponse] = Field(default_factory=list, description="Task list")
    stats: SchedulerStats = Field(default_factory=SchedulerStats, description="Statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "tasks": [
                    {
                        "id": "task_001",
                        "title": "Task 1",
                        "due_date": "2026-06-20",
                        "priority": "high",
                        "status": "pending",
                        "created_at": "2026-06-19T10:00:00",
                    }
                ],
                "stats": {"total": 1, "pending": 1, "completed": 0, "overdue": 0},
            }
        }
