"""Base Pydantic schemas for common configurations and fields."""
from datetime import datetime
from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict, Field, model_serializer

T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration for all models."""
    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode (formerly from_orm)
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_assignment=True,  # Validate on assignment
        use_enum_values=True,  # Use enum values instead of enum objects
        populate_by_name=True,  # Allow both field name and alias
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        },
    )

    @model_serializer(mode='wrap')
    def serialize_model(self, serializer: Any, info: Any) -> Any:
        """Serialize model with ISO formatted datetime fields."""
        data: dict[str, Any] = serializer(self)
        # Convert all datetime fields to ISO format
        for key, value in list(data.items()):
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class PaginationParams(BaseSchema):
    """Pagination parameters for request queries."""
    skip: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of records to skip (offset). If not provided, starts from the beginning."
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of records to return. If not provided, returns all records."
    )


class PaginationMeta(BaseSchema):
    """Pagination metadata for responses."""
    total: int = Field(..., ge=0, description="Total number of records")
    skip: int = Field(..., ge=0, description="Number of records skipped (offset)")
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of records per page. None if no limit was applied."
    )
    has_next: bool = Field(..., description="Whether there are more records available")
    has_previous: bool = Field(..., description="Whether there are previous records")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T] = Field(..., description="List of items in the current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

