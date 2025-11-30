from fastapi.middleware.cors import CORSMiddleware
from .core.setup import create_application
from .api import router
from .core.config import settings
from .middleware.access_logger import AccessLogMiddleware

app = create_application(router=router)

# Add access logging middleware
app.add_middleware(AccessLogMiddleware)

# Configure CORS using settings from .env file
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
    expose_headers=settings.cors_expose_headers_list,
    max_age=settings.cors_max_age,
)

