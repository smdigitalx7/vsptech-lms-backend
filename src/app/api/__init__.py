from fastapi import APIRouter
from .v1 import router as v1_router
from . import health

router = APIRouter(prefix="/api/v1")

router.include_router(v1_router)
router.include_router(health.router)

