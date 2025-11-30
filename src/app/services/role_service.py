"""Role service for business logic."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import Role
from app.schemas.role import RoleResponse
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


class RoleService:
    """Role service for business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_roles(self) -> list[RoleResponse]:
        """Get all non-system roles.
        
        Returns only roles where is_system_role is False.
        
        Returns
        -------
        list[RoleResponse]
            List of all non-system roles with id and name only.
        """
        result = await self.db.execute(
            select(Role)
            .where(Role.is_system_role.is_(False))
            .order_by(Role.name)
        )
        roles = result.scalars().all()
        
        return [RoleResponse.model_validate(role) for role in roles]

    async def get_role_by_id(self, role_id: int) -> Optional[RoleResponse]:
        """Get role by ID.
        
        Parameters
        ----------
        role_id : int
            Role ID.
        
        Returns
        -------
        Optional[RoleResponse]
            Role if found, None otherwise.
        """
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            return None
        
        return RoleResponse.model_validate(role)

