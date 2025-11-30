"""Role API endpoints."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_role_service
from app.core.permissions import require_roles
from app.schemas.role import RoleResponse
from app.services.role_service import RoleService
from app.core.logger import get_app_logger

router = APIRouter(prefix="/roles", tags=["Roles"])
logger = get_app_logger(__name__)


@router.get("", response_model=list[RoleResponse])
async def get_all_roles(
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin")),
    role_service: RoleService = Depends(get_role_service)
) -> list[RoleResponse]:
    """Get all roles.
    
    Returns a list of all roles with id and name only.
    
    Parameters
    ----------
    current_user : dict
        Current authenticated user (from require_roles dependency).
    role_service : RoleService
        Role service instance.
    
    Returns
    -------
    list[RoleResponse]
        List of all roles.
    
    Raises
    ------
    HTTPException
        500 if failed to fetch roles.
    """
    try:
        roles = await role_service.get_all_roles()
        return roles
    
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch roles"
        )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role_by_id(
    role_id: int,
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin", "CollegeAdmin")),
    role_service: RoleService = Depends(get_role_service)
) -> RoleResponse:
    """Get role by ID.
    
    Parameters
    ----------
    role_id : int
        Role ID.
    current_user : dict
        Current authenticated user (from require_roles dependency).
    role_service : RoleService
        Role service instance.
    
    Returns
    -------
    RoleResponse
        Role details.
    
    Raises
    ------
    HTTPException
        404 if role not found.
        500 if failed to fetch role.
    """
    try:
        role = await role_service.get_role_by_id(role_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        return role
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch role"
        )

