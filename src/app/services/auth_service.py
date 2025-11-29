from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings, SECONDS_PER_MINUTE
from app.schemas.auth import AccessTokenDetails, RefreshTokenDetails, TokenResponse
from app.models.user import User
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> tuple[TokenResponse, str]:
        """Authenticate user and return tokens.

        Parameters
        ----------
        email : str
            User email.
        password : str
            User password.

        Returns
        -------
        tuple[TokenResponse, str]
            Token response and refresh token.

        Raises
        ------
        ValueError
            If authentication fails.
        """
        # Get user from database
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        # Verify password
        if not await verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Create tokens
        access_token_details = AccessTokenDetails(user_id=user.user_id, email=user.email)
        refresh_token_details = RefreshTokenDetails(user_id=user.user_id)

        access_token = await create_access_token(access_token_details)
        refresh_token = await create_refresh_token(refresh_token_details)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * SECONDS_PER_MINUTE
        )

        return token_response, refresh_token

    async def register_user(self, email: str, password: str, full_name: str) -> tuple[TokenResponse, str]:
        """Register a new user and return tokens.

        Parameters
        ----------
        email : str
            User email.
        password : str
            User password.
        full_name : str
            User full name.

        Returns
        -------
        tuple[TokenResponse, str]
            Token response and refresh token.

        Raises
        ------
        ValueError
            If registration fails.
        """
        # Check if user already exists
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = await hash_password(password)

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=True
        )

        self.db.add(user)
        await self.db.flush()

        # Create tokens
        access_token_details = AccessTokenDetails(user_id=user.user_id, email=user.email)
        refresh_token_details = RefreshTokenDetails(user_id=user.user_id)

        access_token = await create_access_token(access_token_details)
        refresh_token = await create_refresh_token(refresh_token_details)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * SECONDS_PER_MINUTE
        )

        return token_response, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> tuple[TokenResponse, str]:
        """Refresh access token using refresh token.

        Parameters
        ----------
        refresh_token : str
            Refresh token.

        Returns
        -------
        tuple[TokenResponse, str]
            New token response and new refresh token.

        Raises
        ------
        ValueError
            If refresh token is invalid.
        """
        try:
            # Decode refresh token
            payload = decode_token(refresh_token)

            if payload.get("token_type") != "refresh":
                raise ValueError("Invalid token type")

            user_id = payload.get("user_id")
            if not user_id:
                raise ValueError("Invalid token payload")

            # Get user from database
            result = await self.db.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                raise ValueError("User not found or inactive")

            # Create new tokens
            access_token_details = AccessTokenDetails(user_id=user.user_id, email=user.email)
            refresh_token_details = RefreshTokenDetails(user_id=user.user_id)

            access_token = await create_access_token(access_token_details)
            new_refresh_token = await create_refresh_token(refresh_token_details)

            token_response = TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * SECONDS_PER_MINUTE
            )

            return token_response, new_refresh_token

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise ValueError("Invalid refresh token") from e

