from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_college_service
from app.core.permissions import require_roles
from app.schemas.college import CollegeResponse, CollegeListResponse, CollegeCreate, CollegeUpdate
from app.schemas.base import PaginatedResponse, PaginationParams
from app.services.college_service import CollegeService
from app.core.logger import get_app_logger

router = APIRouter(prefix="/colleges", tags=["Colleges"])
logger = get_app_logger(__name__)


@router.get("", response_model=PaginatedResponse[CollegeListResponse])
async def get_all_colleges(
    pagination: PaginationParams = Depends(),
    current_user: dict[str,Any] = Depends(require_roles("SuperAdmin", "CollegeAdmin")),    
    college_service: CollegeService = Depends(get_college_service)
) -> PaginatedResponse[CollegeListResponse]:
    """Get all colleges with role-based filtering and pagination.
    
    - SuperAdmin: Returns all colleges
    - CollegeAdmin: Returns only assigned colleges
    
    Parameters
    ----------
    pagination : PaginationParams
        Pagination parameters (skip, limit) from query string.
    current_user : dict
        Current authenticated user (from require_roles dependency).
    college_service : CollegeService
        College service instance.
    
    Returns
    -------
    PaginatedResponse[CollegeListResponse]
        Paginated list of colleges based on user role with pagination metadata.
    """
    try:
        user_id: int | None = current_user.get("user_id")
        user_roles: list[str] | None = current_user.get("roles", [])
        
        result = await college_service.get_all_colleges(
            user_id=user_id,
            user_roles=user_roles,
            skip=pagination.skip,
            limit=pagination.limit
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching colleges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch colleges"
        )


@router.get("/{college_id}", response_model=CollegeResponse)
async def get_college_by_id(
    college_id: int,
    current_user: dict[str,Any] = Depends(require_roles("SuperAdmin", "CollegeAdmin")),
    college_service: CollegeService = Depends(get_college_service)
) -> CollegeResponse:
    """Get college by ID with role-based access control.
    
    - SuperAdmin: Can access any college
    - CollegeAdmin: Can only access assigned colleges
    
    Parameters
    ----------
    college_id : int
        College ID.
    current_user : dict
        Current authenticated user (from require_roles dependency).
    college_service : CollegeService
        College service instance.
    
    Returns
    -------
    CollegeResponse
        College details.
    
    Raises
    ------
    HTTPException
        404 if college not found or user doesn't have access.
    """
    try:
        user_id: int | None = current_user.get("user_id")
        user_roles = current_user.get("roles", [])
        
        college = await college_service.get_college_by_id(
            college_id=college_id,
            user_id=user_id,
            user_roles=user_roles
        )
        
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found or access denied"
            )
        
        return college
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching college {college_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch college"
        )


@router.post("", response_model=CollegeResponse, status_code=status.HTTP_201_CREATED)
async def create_college(
    college_data: CollegeCreate,
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin")),
    college_service: CollegeService = Depends(get_college_service)
) -> CollegeResponse:
    """Create a new college (SuperAdmin only).
    
    Parameters
    ----------
    college_data : CollegeCreate
        College creation data.
    current_user : dict
        Current authenticated user (must be SuperAdmin).
    college_service : CollegeService
        College service instance.
    
    Returns
    -------
    CollegeResponse
        Created college.
    
    Raises
    ------
    HTTPException
        400 if college creation fails (e.g., email already exists).
        403 if user is not SuperAdmin.
    """
    try:
        college = await college_service.create_college(college_data)
        return college
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating college: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create college"
        )


@router.put("/{college_id}", response_model=CollegeResponse)
async def update_college(
    college_id: int,
    college_data: CollegeUpdate,
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin")),
    college_service: CollegeService = Depends(get_college_service)
) -> CollegeResponse:
    """Update a college (SuperAdmin only).
    
    Parameters
    ----------
    college_id : int
        College ID to update.
    college_data : CollegeUpdate
        College update data.
    current_user : dict
        Current authenticated user (must be SuperAdmin).
    college_service : CollegeService
        College service instance.
    
    Returns
    -------
    CollegeResponse
        Updated college.
    
    Raises
    ------
    HTTPException
        400 if update fails (e.g., email already exists for another college).
        404 if college not found.
        403 if user is not SuperAdmin.
    """
    try:
        college = await college_service.update_college(college_id, college_data)
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )
        return college
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating college {college_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update college"
        )

