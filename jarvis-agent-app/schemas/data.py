"""
Data analysis and generation schemas.
"""

from typing import Dict, Any, List, Optional
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class AnalyzeRequest(BaseSchema):
    """Data analysis request."""
    
    dataset_name: str = Field(..., min_length=1, max_length=128, description="Dataset name to analyze")
    analysis_type: Optional[str] = Field(default="summary", description="Type of analysis")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Additional analysis parameters")
    
    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"summary", "correlation", "distribution", "outliers", "trend"}
        if v.lower() not in allowed:
            raise ValueError(f'analysis_type must be one of {sorted(allowed)}')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "dataset_name": "sales_2026",
                "analysis_type": "summary",
                "parameters": {"group_by": "category"},
            }
        }


class GenerateDataRequest(BaseSchema):
    """Data generation request."""
    
    name: str = Field(..., min_length=1, max_length=128, description="Dataset name")
    n: int = Field(default=100, ge=1, le=10000, description="Number of records to generate")
    format: str = Field(default="json", description="Output format")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed = {"json", "csv", "text"}
        if v.lower() not in allowed:
            raise ValueError(f'format must be one of {sorted(allowed)}')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "sample_data",
                "n": 500,
                "format": "json",
            }
        }


class DataResponse(ResponseBase):
    """Data operation response."""
    
    data: Dict[str, Any] = Field(..., description="Generated or analyzed data")
    records: Optional[int] = Field(default=None, description="Number of records")
    format: Optional[str] = Field(default=None, description="Data format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "columns": ["id", "name", "value"],
                    "rows": [[1, "Item A", 100], [2, "Item B", 200]],
                },
                "records": 2,
                "format": "json",
            }
        }
