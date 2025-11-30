"""Global exception handlers for FastAPI application."""
from datetime import datetime, timezone
from typing import Any, cast
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logger import get_error_logger, get_app_logger
from app.schemas.errors import ErrorResponse, ErrorDetail


error_logger = get_error_logger("exception_handlers")
app_logger = get_app_logger("exception_handlers")


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTPException (FastAPI/Starlette HTTP exceptions)."""
    request_id = getattr(request.state, "request_id", None)
    
    # Log the exception
    error_logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
    )
    
    # Extract error message
    message: str
    error_details: list[ErrorDetail] | None
    
    if isinstance(exc.detail, dict):
        detail_dict = cast(dict[str, Any], exc.detail)
        message = str(detail_dict.get("message", exc.detail))
        details = detail_dict.get("details")
        if details and isinstance(details, list):
            details_list = cast(list[dict[str, Any]], details)
            error_details = [
                ErrorDetail(
                    field=str(detail.get("field")) if detail.get("field") else None,
                    message=str(detail.get("message", detail)),
                    code=str(detail.get("code")) if detail.get("code") else None,
                )
                for detail in details_list
            ]
        else:
            error_details = None
    elif isinstance(exc.detail, list):
        # Handle list of errors (e.g., from validation)
        error_details = [
            ErrorDetail(message=str(item), field=None, code=None) for item in exc.detail
        ]
        message = "Validation error"
    else:
        message = str(exc.detail)
        error_details = None
    
    error_response = ErrorResponse(
        success=False,
        error=f"HTTP{exc.status_code}",
        message=message,
        details=error_details,
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors (Pydantic validation)."""
    request_id = getattr(request.state, "request_id", None)
    
    # Extract validation errors
    errors = exc.errors()
    error_details: list[ErrorDetail] = []
    
    for error in errors:
        field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
        error_msg = error.get("msg", "Validation error")
        error_type = error.get("type", "validation_error")
        
        error_details.append(
            ErrorDetail(
                field=field_path if field_path != "body" else None,
                message=error_msg,
                code=error_type,
            )
        )
    
    # Log validation errors
    error_logger.warning(
        f"Validation error: {len(errors)} field(s) failed validation",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        validation_errors=errors,
    )
    
    error_response = ErrorResponse(
        success=False,
        error="ValidationError",
        message="Request validation failed. Please check your input.",
        details=error_details,
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(exclude_none=True),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions (fallback handler)."""
    request_id = getattr(request.state, "request_id", None)
    
    # Log the exception with full traceback
    error_logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    
    error_response = ErrorResponse(
        success=False,
        error="InternalServerError",
        message="An unexpected error occurred. Please try again later.",
        details=None,
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(exclude_none=True),
    )

