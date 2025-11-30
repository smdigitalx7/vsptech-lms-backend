from typing import Optional
import redis.asyncio as redis
from arq import ArqRedis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.utils import cache, queue
from app.services.auth_service import AuthService
from app.services.college_service import CollegeService
from app.services.role_service import RoleService
from app.services.user_service import UserService


def get_cache_client() -> Optional[redis.Redis]:
    """Provide Redis cache client if initialized; otherwise None."""
    return cache.cache_manager.client


def get_queue_pool() -> Optional[ArqRedis]:
    """Provide ARQ Redis pool if initialized; otherwise None."""
    return queue.pool


# Authentication Service
def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)


# College Service
def get_college_service(db: AsyncSession = Depends(get_db_session)) -> CollegeService:
    """Get college service instance."""
    return CollegeService(db)


# Role Service
def get_role_service(db: AsyncSession = Depends(get_db_session)) -> RoleService:
    """Get role service instance."""
    return RoleService(db)


# User Service
def get_user_service(db: AsyncSession = Depends(get_db_session)) -> UserService:
    """Get user service instance."""
    return UserService(db)

