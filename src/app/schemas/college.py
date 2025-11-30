"""College schemas."""
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field
from app.models.enums import CollegeStatusEnum
from .base import BaseSchema


class CollegeCreate(BaseSchema):
    """College creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    status: CollegeStatusEnum = Field(
        default=CollegeStatusEnum.ACTIVE,
        description="College status"
    )


class CollegeUpdate(BaseSchema):
    """College update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="College name")
    email: Optional[EmailStr] = Field(None, description="College email address")
    phone: Optional[str] = Field(None, max_length=20, description="College phone number")
    status: Optional[CollegeStatusEnum] = Field(None, description="College status")


class CollegeResponse(BaseSchema):
    """College response schema."""
    id: int = Field(..., description="College database ID")
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    status: CollegeStatusEnum = Field(..., description="College status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")


class CollegeListResponse(BaseSchema):
    """College list response schema."""
    id: int
    name: str
    email: str
    phone: Optional[str]
    status: CollegeStatusEnum
    created_at: datetime
    updated_at: datetime


