"""Pydantic schemas for request/response validation."""

from .base import (
    BaseSchema,
    PaginationParams,
    PaginationMeta,
    PaginatedResponse,
)

from .auth import (
    AccessTokenDetails,
    RefreshTokenDetails,
    LoginRequest,
    TokenResponse,
)



from .college import (
    CollegeCreate,
    CollegeUpdate,
    CollegeResponse,
    CollegeListResponse,
)

from .errors import (
    ErrorDetail,
    ErrorResponse,
)

from .role import (
    RoleResponse,
)

from .user import (
    RegisterAdminRequest,
    AssociateUserWithCollegeRequest,
)

from .section_type import (
    SectionTypeCreate,
    SectionTypeUpdate,
    SectionTypeResponse,
)

__all__ = [
    # Base schemas
    "BaseSchema",
    "PaginationParams",
    "PaginationMeta",
    "PaginatedResponse",
    # Auth schemas
    "AccessTokenDetails",
    "RefreshTokenDetails",
    "LoginRequest",
    "TokenResponse",
    # College schemas
    "CollegeCreate",
    "CollegeUpdate",
    "CollegeResponse",
    "CollegeListResponse",
    # Error schemas
    "ErrorDetail",
    "ErrorResponse",
    # Role schemas
    "RoleResponse",
    # User schemas
    "RegisterAdminRequest",
    "AssociateUserWithCollegeRequest",
    # Section type schemas
    "SectionTypeCreate",
    "SectionTypeUpdate",
    "SectionTypeResponse",
]
