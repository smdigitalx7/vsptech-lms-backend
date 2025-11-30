from pydantic import EmailStr, Field
from .base import BaseSchema


class AccessTokenDetails(BaseSchema):
    """Access token payload details."""
    user_id: int
    email: str
    roles: list[str] = Field(default_factory=list, description="List of user role names")


class RefreshTokenDetails(BaseSchema):
    """Refresh token payload details."""
    user_id: int


class LoginRequest(BaseSchema):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseSchema):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    roles: list[str] = Field(default_factory=list, description="List of user role names")

