from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"])
router.include_router(users_router, tags=["Users"])

