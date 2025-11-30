from fastapi import APIRouter
from .auth import router as auth_router
from .colleges import router as colleges_router
from .enums import router as enums_router
from .logs import router as logs_router
from .roles import router as roles_router
from .users import router as users_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"])
router.include_router(colleges_router, tags=["Colleges"])
router.include_router(enums_router, tags=["Enums"])
router.include_router(logs_router, tags=["Logs"])
router.include_router(roles_router, tags=["Roles"])
router.include_router(users_router, tags=["Users"])

