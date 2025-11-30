from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
from app.core.logger import get_access_logger
from app.core.config import MILLISECONDS_PER_SECOND
import time

class AccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.access_logger = get_access_logger("access_middleware")
    
    async def dispatch(self, request: Request, call_next: ASGIApp) -> Response:  # type: ignore[override]
        # Start timing
        start_time = time.time()
        
        # Extract request info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        path = request.url.path
        
        # Get or generate request_id
        request_id = getattr(request.state, "request_id", None)
        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
        
        # Log request
        self.access_logger.info(
            "HTTP Request",
            method=method,
            path=path,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        # Process request
        response: Response = await call_next(request)  # type: ignore[assignment]
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        self.access_logger.info(
            "HTTP Response",
            method=method,
            path=path,
            status_code=response.status_code,  # type: ignore[attr-defined]
            process_time_ms=round(process_time * MILLISECONDS_PER_SECOND, 2),
            client_ip=client_ip,
            request_id=request_id
        )
        
        return response  # type: ignore[return-value]

