"""Section type schemas."""
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import BaseSchema


class SectionTypeCreate(BaseSchema):
    """Section type creation schema."""
    code: str = Field(..., min_length=1, max_length=30, description="Unique section type code")
    name: str = Field(..., min_length=1, max_length=100, description="Section type name")
    description: Optional[str] = Field(None, description="Section type description")
    requires_options: bool = Field(default=False, description="Whether this section type requires options")
    requires_media: bool = Field(default=False, description="Whether this section type requires media")
    requires_special_table: bool = Field(default=False, description="Whether this section type requires a special table")
    special_table_name: Optional[str] = Field(None, max_length=50, description="Name of the special table if required")
    is_active: bool = Field(default=True, description="Whether this section type is active")


class SectionTypeUpdate(BaseSchema):
    """Section type update schema."""
    code: Optional[str] = Field(None, min_length=1, max_length=30, description="Unique section type code")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Section type name")
    description: Optional[str] = Field(None, description="Section type description")
    requires_options: Optional[bool] = Field(None, description="Whether this section type requires options")
    requires_media: Optional[bool] = Field(None, description="Whether this section type requires media")
    requires_special_table: Optional[bool] = Field(None, description="Whether this section type requires a special table")
    special_table_name: Optional[str] = Field(None, max_length=50, description="Name of the special table if required")
    is_active: Optional[bool] = Field(None, description="Whether this section type is active")


class SectionTypeResponse(BaseSchema):
    """Section type response schema."""
    id: int = Field(..., description="Section type database ID")
    code: str = Field(..., min_length=1, max_length=30, description="Unique section type code")
    name: str = Field(..., min_length=1, max_length=100, description="Section type name")
    description: Optional[str] = Field(None, description="Section type description")
    requires_options: bool = Field(..., description="Whether this section type requires options")
    requires_media: bool = Field(..., description="Whether this section type requires media")
    requires_special_table: bool = Field(..., description="Whether this section type requires a special table")
    special_table_name: Optional[str] = Field(None, max_length=50, description="Name of the special table if required")
    is_active: bool = Field(..., description="Whether this section type is active")
    created_at: datetime = Field(..., description="Creation timestamp")

