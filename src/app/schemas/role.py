"""Role schemas."""
from pydantic import Field
from .base import BaseSchema


class RoleResponse(BaseSchema):
    """Role response schema (read-only)."""
    id: int = Field(..., description="Role database ID")
    name: str = Field(..., max_length=50, description="Role name")

