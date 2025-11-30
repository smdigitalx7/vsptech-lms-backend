"""Global exception handler middleware."""
from typing import Optional
from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
from app.core.logger import get_error_logger
from app.schemas.errors import ErrorResponse, ErrorDetail


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and handle unhandled exceptions globally."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.error_logger = get_error_logger("exception_handler")
    
    async def dispatch(self, request: Request, call_next: ASGIApp) -> Response:  # type: ignore[override]
        """Process request and catch any unhandled exceptions."""
        try:
            response: Response = await call_next(request)  # type: ignore[assignment]
            return response  # type: ignore[return-value]
        except Exception as exc:
            # Get request ID if available
            request_id = getattr(request.state, "request_id", None)
            
            # Log the exception with full traceback
            self.error_logger.error(
                f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
                exc_info=True,
                request_id=request_id,
                path=request.url.path,
                method=request.method,
            )
            
            # Return standardized error response
            return await self._create_error_response(
                request=request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="InternalServerError",
                message="An unexpected error occurred. Please try again later.",
                request_id=request_id,
            )
    
    @staticmethod
    async def _create_error_response(
        request: Request,
        status_code: int,
        error: str,
        message: str,
        details: Optional[list[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ) -> JSONResponse:
        """Create a standardized error response."""
        error_response = ErrorResponse(
            success=False,
            error=error,
            message=message,
            details=details,
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump(exclude_none=True),
        )

