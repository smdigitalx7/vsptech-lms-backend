"""Error response schemas for consistent error formatting."""
from typing import Optional
from pydantic import Field
from .base import BaseSchema


class ErrorDetail(BaseSchema):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field name that caused the error (for validation errors)")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseSchema):
    """Standard error response format."""
    success: bool = Field(False, description="Indicates the request failed")
    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[list[ErrorDetail]] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: str = Field(..., description="ISO timestamp of when the error occurred")

