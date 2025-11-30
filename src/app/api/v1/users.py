"""User API endpoints."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DatabaseError
from app.core.dependencies import get_user_service
from app.core.permissions import require_roles
from app.schemas.user import RegisterAdminRequest, AssociateUserWithCollegeRequest
from app.services.user_service import UserService
from app.core.logger import get_app_logger

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_app_logger(__name__)


@router.post("/register-admin", status_code=status.HTTP_201_CREATED)
async def register_admin(
    admin_data: RegisterAdminRequest,
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin")),
    user_service: UserService = Depends(get_user_service)
) -> dict[str, Any]:
    """Register a new admin user with college association (SuperAdmin only).
    
    Automatically assigns the "CollegeAdmin" role to the registered user.
    
    Parameters
    ----------
    admin_data : RegisterAdminRequest
        Admin registration data including email, password, full_name, and college_id.
    current_user : dict
        Current authenticated user (must be SuperAdmin).
    user_service : UserService
        User service instance.
    
    Returns
    -------
    dict
        Success message with user information.
    
    Raises
    ------
    HTTPException
        400 if registration fails (e.g., user exists, college not found, CollegeAdmin role not found).
        403 if user is not SuperAdmin.
    """
    try:
        user = await user_service.register_admin(
            email=admin_data.email,
            password=admin_data.password,
            full_name=admin_data.full_name,
            college_id=admin_data.college_id
        )

        return {
            "message": "Admin registered successfully",
            "user_id": user.id,
            "email": user.email,
            "name": user.name
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        # Handle database constraint violations
        error_msg = f"Database constraint violation during admin registration: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
        logger.error(error_msg, exc_info=True, email=admin_data.email, college_id=admin_data.college_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed due to database constraint: {str(e.orig) if hasattr(e, 'orig') else 'Duplicate entry or constraint violation'}"
        )
    except DatabaseError as e:
        # Handle other database errors
        error_msg = f"Database error during admin registration: {str(e)}"
        logger.error(error_msg, exc_info=True, email=admin_data.email, college_id=admin_data.college_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        # Log the full exception with traceback
        error_msg = f"Error registering admin: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True, email=admin_data.email, college_id=admin_data.college_id)
        
        # Include error details in response for debugging (can be filtered in production)
        detail_msg = f"Failed to register admin: {type(e).__name__}: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg
        )


@router.post("/associate-college", status_code=status.HTTP_201_CREATED)
async def associate_user_with_college(
    association_data: AssociateUserWithCollegeRequest,
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin")),
    user_service: UserService = Depends(get_user_service)
) -> dict[str, Any]:
    """Associate an existing user with a college (SuperAdmin only).
    
    Creates a relationship between a user and a college in the college_users table.
    
    Parameters
    ----------
    association_data : AssociateUserWithCollegeRequest
        Association data including user_id, college_id, and optionally is_primary.
    current_user : dict
        Current authenticated user (must be SuperAdmin).
    user_service : UserService
        User service instance.
    
    Returns
    -------
    dict
        Success message with association information.
    
    Raises
    ------
    HTTPException
        400 if association fails (e.g., user not found, college not found, relationship already exists).
        403 if user is not SuperAdmin.
    """
    try:
        college_user = await user_service.associate_user_with_college(
            user_id=association_data.user_id,
            college_id=association_data.college_id,
            is_primary=association_data.is_primary or False
        )

        return {
            "message": "User successfully associated with college",
            "user_id": college_user.user_id,
            "college_id": college_user.college_id,
            "is_primary": college_user.is_primary
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error associating user with college: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to associate user with college"
        )

