from typing import Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func,update
from app.models.college import College, CollegeUser
from app.schemas.college import CollegeResponse, CollegeListResponse
from app.schemas.base import PaginatedResponse, PaginationMeta
from app.core.logger import get_app_logger

if TYPE_CHECKING:
    from app.schemas.college import CollegeCreate, CollegeUpdate

logger = get_app_logger(__name__)


class CollegeService:
    """College service for business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_colleges(
        self, 
        user_id: int | None = None, 
        user_roles: list[str] | None = None, 
        skip: Optional[int] = None, 
        limit: Optional[int] = None
    ) -> PaginatedResponse[CollegeListResponse]:
        """Get all colleges with role-based filtering and pagination.
        
        Parameters
        ----------
        user_id : int | None
            Current user ID.
        user_roles : list[str] | None
            List of user roles.
        skip : Optional[int]
            Number of records to skip. If None, no offset is applied.
        limit : Optional[int]
            Maximum number of records to return. If None, returns all records.
        
        Returns
        -------
        PaginatedResponse[CollegeListResponse]
            Paginated list of colleges based on user role.
        """
        # Use 0 if skip is None
        skip_value = skip if skip is not None else 0
        
        # Build base query for filtering
        if user_roles and "SuperAdmin" in user_roles:
            # SuperAdmin can see all colleges
            base_query = select(College).where(College.deleted_at.is_(None))
            count_query = select(func.count(College.id)).where(College.deleted_at.is_(None))
        else:
            # CollegeAdmin can only see their assigned colleges
            # Get college IDs assigned to the user
            college_user_result = await self.db.execute(
                select(CollegeUser.college_id)
                .where(CollegeUser.user_id == user_id)
            )
            assigned_college_ids = [row[0] for row in college_user_result.all()]
            
            if not assigned_college_ids:
                # User has no assigned colleges - return empty paginated response
                return PaginatedResponse[CollegeListResponse](
                    items=[],
                    pagination=PaginationMeta(
                        total=0,
                        skip=skip_value,
                        limit=limit,
                        has_next=False,
                        has_previous=False
                    )
                )
            
            base_query = select(College).where(
                College.id.in_(assigned_college_ids),
                College.deleted_at.is_(None)
            )
            count_query = select(func.count(College.id)).where(
                College.id.in_(assigned_college_ids),
                College.deleted_at.is_(None)
            )
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        # Get paginated results
        result = await self.db.execute(
            base_query
            .offset(skip_value)
            .limit(limit)
            .order_by(College.created_at.desc())
        )
        colleges = result.scalars().all()
        
        # Calculate pagination metadata
        has_next = (skip_value + (limit if limit else 0)) < total if limit else False
        has_previous = skip_value > 0
        
        return PaginatedResponse[CollegeListResponse](
            items=[CollegeListResponse.model_validate(college) for college in colleges],
            pagination=PaginationMeta(
                total=total,
                skip=skip_value,
                limit=limit,
                has_next=has_next,
                has_previous=has_previous
            )
        )

    async def get_college_by_id(
        self, 
        college_id: int, 
        user_id: int | None = None, 
        user_roles: list[str] | None = None
    ) -> Optional[CollegeResponse]:
        """Get college by ID with role-based access control.
        
        Parameters
        ----------
        college_id : int
            College ID.
        user_id : int
            Current user ID.
        user_roles : list[str] | None
            List of user roles.
        
        Returns
        -------
        Optional[CollegeResponse]
            College if found and user has access, None otherwise.
        """
        # Get the college
        result = await self.db.execute(
            select(College).where(
                College.id == college_id,
                College.deleted_at.is_(None)
            )
        )
        college = result.scalar_one_or_none()
        
        if not college:
            return None
        
        # SuperAdmin can access any college
        if user_roles and "SuperAdmin" in user_roles:
            return CollegeResponse.model_validate(college)
        
        # CollegeAdmin can only access their assigned colleges
        college_user_result = await self.db.execute(
            select(CollegeUser)
            .where(
                CollegeUser.user_id == user_id,
                CollegeUser.college_id == college_id
            )
        )
        college_user = college_user_result.scalar_one_or_none()
        
        if not college_user:
            # User doesn't have access to this college
            return None
        
        return CollegeResponse.model_validate(college)

    async def create_college(self, college_data: "CollegeCreate") -> CollegeResponse:
        """Create a new college.
        
        Parameters
        ----------
        college_data : CollegeCreate
            College creation data.
        
        Returns
        -------
        CollegeResponse
            Created college.
        
        Raises
        ------
        ValueError
            If college creation fails (e.g., email already exists).
        """
        # Check if college with same email already exists
        result = await self.db.execute(
            select(College).where(College.email == college_data.email, College.deleted_at.is_(None))
        )
        existing_college = result.scalar_one_or_none()
        
        if existing_college:
            raise ValueError("College with this email already exists")
        
        # Create new college
        college = College(
            name=college_data.name,
            email=college_data.email,
            phone=college_data.phone,
            status=college_data.status
        )
        
        self.db.add(college)
        await self.db.flush()
        
        return CollegeResponse.model_validate(college)

    async def update_college(
        self, 
        college_id: int, 
        college_data: "CollegeUpdate"
    ) -> Optional[CollegeResponse]:
        """Update a college.
        
        Parameters
        ----------
        college_id : int
            College ID to update.
        college_data : CollegeUpdate
            College update data.
        
        Returns
        -------
        Optional[CollegeResponse]
            Updated college if found, None otherwise.
        
        Raises
        ------
        ValueError
            If update fails (e.g., email already exists for another college).
        """
        # First check if college exists
        result = await self.db.execute(
            select(College).where(
                College.id == college_id,
                College.deleted_at.is_(None)
            )
        )
        college = result.scalar_one_or_none()
        
        if not college:
            return None
        
        # Get only the fields that were explicitly set (exclude_unset=True)
        update_data = college_data.model_dump(exclude_unset=True)
        
        # If no fields to update, return the existing college
        if not update_data:
            return CollegeResponse.model_validate(college)
        
        # Check if email is being updated and if it conflicts with another college
        if "email" in update_data and update_data["email"] != college.email:
            email_check_result = await self.db.execute(
                select(College).where(
                    College.email == update_data["email"],
                    College.id != college_id,
                    College.deleted_at.is_(None)
                )
            )
            conflicting_college = email_check_result.scalar_one_or_none()
            if conflicting_college:
                raise ValueError("College with this email already exists")
        
        # Use SQLAlchemy update() for efficient bulk update
        await self.db.execute(
            update(College)
            .where(College.id == college_id, College.deleted_at.is_(None))
            .values(**update_data)
        )
        await self.db.flush()
        
        # Refresh the college object to get updated values
        await self.db.refresh(college)
        
        return CollegeResponse.model_validate(college)

