"""Enum schemas."""
from pydantic import Field
from app.schemas.base import BaseSchema


class EnumValueResponse(BaseSchema):
    """Single enum value response."""
    name: str = Field(..., description="Enum value name")
    value: str = Field(..., description="Enum value")


class EnumResponse(BaseSchema):
    """Enum response schema."""
    enum_name: str = Field(..., description="Name of the enum class")
    values: list[EnumValueResponse] = Field(..., description="List of enum values")


class AllEnumsResponse(BaseSchema):
    """Response schema for all enums."""
    enums: dict[str, list[EnumValueResponse]] = Field(..., description="Dictionary of all enums with their values")

