"""User service for business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole, Role
from app.models.college import College, CollegeUser
from app.models.enums import UserStatusEnum
from app.core.security import hash_password
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


class UserService:
    """User service for business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_admin(
        self,
        email: str,
        password: str,
        full_name: str,
        college_id: int
    ) -> User:
        """Register a new admin user with college association.
        
        Automatically assigns the "CollegeAdmin" role to the user.

        Parameters
        ----------
        email : str
            User email.
        password : str
            User password.
        full_name : str
            User full name.
        college_id : int
            College ID to associate the admin with.

        Returns
        -------
        User
            Created user object.

        Raises
        ------
        ValueError
            If registration fails (e.g., user exists, college not found, CollegeAdmin role not found).
        """
        # Check if user already exists
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User with this email already exists")

        # Validate college exists
        college_result = await self.db.execute(
            select(College).where(College.id == college_id, College.deleted_at.is_(None))
        )
        college = college_result.scalar_one_or_none()

        if not college:
            raise ValueError("College not found")

        # Get CollegeAdmin role by name
        role_result = await self.db.execute(
            select(Role).where(Role.name == "CollegeAdmin")
        )
        role = role_result.scalar_one_or_none()

        if not role:
            raise ValueError("CollegeAdmin role not found")

        try:
            # Hash password
            password_hash = await hash_password(password)

            # Create user
            user = User(
                email=email,
                password_hash=password_hash,
                name=full_name,
                status=UserStatusEnum.ACTIVE
            )

            self.db.add(user)
            await self.db.flush()

            # Create user-role association with CollegeAdmin role
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id
            )
            self.db.add(user_role)

            # Create college-user association
            college_user = CollegeUser(
                user_id=user.id,
                college_id=college_id,
                is_primary=True  # Can be set to True if this is the primary admin
            )
            self.db.add(college_user)

            await self.db.flush()

            return user
        except Exception as e:
            logger.error(
                f"Error in register_admin service method: {str(e)}",
                exc_info=True,
                email=email,
                college_id=college_id
            )
            raise

    async def associate_user_with_college(
        self,
        user_id: int,
        college_id: int,
        is_primary: bool = False
    ) -> CollegeUser:
        """Associate an existing user with a college.
        
        Creates a relationship in the college_users table.

        Parameters
        ----------
        user_id : int
            User ID to associate with college.
        college_id : int
            College ID to associate the user with.
        is_primary : bool
            Whether this is the primary college for the user.

        Returns
        -------
        CollegeUser
            Created college-user relationship object.

        Raises
        ------
        ValueError
            If association fails (e.g., user not found, college not found, relationship already exists).
        """
        # Validate user exists and is not deleted
        user_result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Validate college exists and is not deleted
        college_result = await self.db.execute(
            select(College).where(College.id == college_id, College.deleted_at.is_(None))
        )
        college = college_result.scalar_one_or_none()

        if not college:
            raise ValueError("College not found")

        # Check if relationship already exists
        existing_result = await self.db.execute(
            select(CollegeUser).where(
                CollegeUser.user_id == user_id,
                CollegeUser.college_id == college_id
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise ValueError("User is already associated with this college")

        # Create college-user association
        college_user = CollegeUser(
            user_id=user_id,
            college_id=college_id,
            is_primary=is_primary
        )
        self.db.add(college_user)
        await self.db.flush()

        return college_user

