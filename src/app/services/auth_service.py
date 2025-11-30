from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings, SECONDS_PER_MINUTE
from app.schemas.auth import AccessTokenDetails, RefreshTokenDetails, TokenResponse
from app.models.user import User, UserRole, Role
from app.models.enums import UserStatusEnum
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user_roles(self, user_id: int) -> list[str]:
        """Get user roles as a list of role names.
        
        Parameters
        ----------
        user_id : int
            User ID.
            
        Returns
        -------
        list[str]
            List of role names.
        """
        result = await self.db.execute(
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        roles = result.scalars().all()
        return list(roles)

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
        # Get user from database with roles (exclude soft-deleted users)
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.email == email, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Invalid email or password")

        # Check user status
        if user.status != UserStatusEnum.ACTIVE:
            raise ValueError("User account is inactive")

        # Verify password
        if not await verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Update last login timestamp
        from datetime import datetime, timezone
        user.last_login_at = datetime.now(timezone.utc)
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        await self.db.flush()

        # Get user roles
        roles: list[str] = []
        if user.user_roles:
            roles = [str(user_role.role.name) for user_role in user.user_roles]

        # Create tokens
        access_token_details = AccessTokenDetails.model_validate({
            "user_id": user.id,
            "email": user.email,
            "roles": roles
        })
        refresh_token_details = RefreshTokenDetails.model_validate({
            "user_id": user.id
        })

        access_token = await create_access_token(access_token_details)
        refresh_token = await create_refresh_token(refresh_token_details)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
            user_id=user.id,
            email=user.email,
            roles=roles
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

            # Get user from database with roles
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.user_roles).selectinload(UserRole.role))
                .where(User.id == user_id, User.deleted_at.is_(None))
            )
            user = result.scalar_one_or_none()

            if not user or user.status != UserStatusEnum.ACTIVE:
                raise ValueError("User not found or inactive")

            # Get user roles
            roles: list[str] = []
            if user.user_roles:
                roles = [str(user_role.role.name) for user_role in user.user_roles]

            # Create new tokens
            access_token_details = AccessTokenDetails.model_validate({
                "user_id": user.id,
                "email": user.email,
                "roles": roles
            })
            refresh_token_details = RefreshTokenDetails.model_validate({
                "user_id": user.id
            })

            access_token = await create_access_token(access_token_details)
            new_refresh_token = await create_refresh_token(refresh_token_details)

            token_response = TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
                user_id=user.id,
                email=user.email,
                roles=roles
            )

            return token_response, new_refresh_token

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise ValueError("Invalid refresh token") from e


