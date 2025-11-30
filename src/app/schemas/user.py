"""User schemas."""
from pydantic import EmailStr, Field
from typing import Optional
from .base import BaseSchema


class RegisterAdminRequest(BaseSchema):
    """Register admin request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    college_id: int = Field(..., description="College ID to associate the admin with")


class AssociateUserWithCollegeRequest(BaseSchema):
    """Associate user with college request schema."""
    user_id: int = Field(..., description="User ID to associate with college")
    college_id: int = Field(..., description="College ID to associate the user with")
    is_primary: Optional[bool] = Field(default=False, description="Whether this is the primary college for the user")

