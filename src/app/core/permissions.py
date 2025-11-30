from collections.abc import Awaitable, Callable
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token


# Security Scheme for Swagger UI
security_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="Enter your JWT access token. Token can be obtained from the /api/v1/auth/login endpoint."
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> dict[str, Any]:
    """
    Validate JWT token and return user information.
    
    This dependency can be used in protected endpoints to require authentication.
    
    Returns
    -------
    dict[str, Any]
        Token payload containing user_id, email, roles, etc.
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        # Verify it's an access token (not refresh token)
        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


def require_roles(*required_roles: str) -> Callable[[], Awaitable[dict[str, Any]]]:
    """
    Create a dependency that checks if the current user has at least one of the required roles.
    
    This is a dependency factory that returns a dependency function. Use it like:
    
    @router.get("/admin-only")
    async def admin_endpoint(
        user: dict = Depends(require_roles("SuperAdmin", "CollegeAdmin"))
    ):
        ...
    
    Parameters
    ----------
    *required_roles : str
        One or more role names that the user must have. User needs at least one.
    
    Returns
    -------
    Callable
        A dependency function that validates user roles.
    
    Raises
    ------
    HTTPException
        403 Forbidden if user doesn't have any of the required roles.
    """
    async def role_checker(
        current_user: dict[str, Any] = Depends(get_current_user)
    ) -> dict[str, Any]:
        """
        Check if current user has required roles.
        
        Parameters
        ----------
        current_user : dict[str, Any]
            User payload from get_current_user dependency.
        
        Returns
        -------
        dict[str, Any]
            User payload if authorized.
        
        Raises
        ------
        HTTPException
            403 Forbidden if user doesn't have required roles.
        """
        user_roles: list[str] = current_user.get("roles", [])
        
        # Check if user has at least one of the required roles
        if not required_roles:
            # If no roles specified, allow any authenticated user
            return current_user
        
        # Check if user has any of the required roles
        has_required_role = any(role in user_roles for role in required_roles)
        
        if not has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker

