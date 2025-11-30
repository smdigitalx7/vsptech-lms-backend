from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from .core.setup import create_application
from .api import router
from .core.config import settings
from .core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from .middleware.access_logger import AccessLogMiddleware
from .middleware.exception_handler import ExceptionHandlerMiddleware

app = create_application(router=router)

# Register global exception handlers
# Order matters: more specific handlers should be registered first
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add exception handler middleware (catches unhandled exceptions)
# This should be added early in the middleware stack
app.add_middleware(ExceptionHandlerMiddleware)

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

