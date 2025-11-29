from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from app.core.config import settings
from app.core.dependencies import get_auth_service
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest
from app.services.auth_service import AuthService
from app.core.logger import get_app_logger

router = APIRouter(prefix="/auth")
logger = get_app_logger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Authenticate user and return access token with refresh token in cookie."""
    try:
        token_response, refresh_token = await auth_service.authenticate_user(
            login_data.email, login_data.password
        )

        # Set refresh token in cookie
        is_dev = settings.is_development
        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
            httponly=True,
            secure=not is_dev,
            samesite="lax" if is_dev else "none",
            path="/",
        )

        return token_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    response: Response,
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Register a new user and return access token."""
    try:
        token_response, refresh_token = await auth_service.register_user(
            register_data.email,
            register_data.password,
            register_data.full_name
        )

        # Set refresh token in cookie
        is_dev = settings.is_development
        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
            httponly=True,
            secure=not is_dev,
            samesite="lax" if is_dev else "none",
            path="/",
        )

        return token_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Refresh access token using refresh token from cookie."""
    refresh_token = request.cookies.get("refreshToken")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")

    try:
        token_response, new_refresh_token = await auth_service.refresh_access_token(refresh_token)

        # Update refresh token in cookie
        is_dev = settings.is_development
        response.set_cookie(
            key="refreshToken",
            value=new_refresh_token,
            max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
            httponly=True,
            secure=not is_dev,
            samesite="lax" if is_dev else "none",
            path="/",
        )

        return token_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
) -> dict[str, str]:
    """Logout user by clearing refresh token cookie."""
    is_dev = settings.is_development
    response.delete_cookie(
        "refreshToken",
        httponly=True,
        secure=not is_dev,
        samesite="lax" if is_dev else "none",
        path="/"
    )

    return {"message": "Successfully logged out"}

