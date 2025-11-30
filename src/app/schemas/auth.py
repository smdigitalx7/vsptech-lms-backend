from pydantic import BaseModel, EmailStr, Field


class AccessTokenDetails(BaseModel):
    """Access token payload details."""
    user_id: int
    email: str


class RefreshTokenDetails(BaseModel):
    """Refresh token payload details."""
    user_id: int


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

