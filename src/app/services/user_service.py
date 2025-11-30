from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import hash_password
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


class UserService:
    """User service for business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user.

        Parameters
        ----------
        user_data : UserCreate
            User creation data.

        Returns
        -------
        UserResponse
            Created user.

        Raises
        ------
        ValueError
            If user creation fails.
        """
        # Check if user already exists
        result = await self.db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = await hash_password(user_data.password)

        # Create user
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            is_active=True
        )

        self.db.add(user)
        await self.db.flush()

        return UserResponse.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        Optional[UserResponse]
            User if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        return UserResponse.model_validate(user)

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """List users with pagination.

        Parameters
        ----------
        skip : int
            Number of records to skip.
        limit : int
            Maximum number of records to return.

        Returns
        -------
        List[UserResponse]
            List of users.
        """
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        users = result.scalars().all()

        return [UserResponse.model_validate(user) for user in users]

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """Update user.

        Parameters
        ----------
        user_id : int
            User ID.
        user_data : UserUpdate
            User update data.

        Returns
        -------
        Optional[UserResponse]
            Updated user if found, None otherwise.

        Raises
        ------
        ValueError
            If update fails.
        """
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Check if email is being changed and if it's already taken
        if user_data.email and user_data.email != user.email:
            email_check = await self.db.execute(select(User).where(User.email == user_data.email))
            if email_check.scalar_one_or_none():
                raise ValueError("User with this email already exists")

        # Update user fields
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        await self.db.flush()

        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: int) -> bool:
        """Delete user.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        bool
            True if user was deleted, False if not found.
        """
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        await self.db.delete(user)
        await self.db.flush()

        return True

