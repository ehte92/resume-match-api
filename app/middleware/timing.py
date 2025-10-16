"""
Performance monitoring middleware.

Tracks request processing time and adds timing headers to responses.
Logs slow requests for performance analysis.
"""

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Threshold for slow request logging (in milliseconds)
SLOW_REQUEST_THRESHOLD_MS = 1000


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log request processing time.

    Adds X-Process-Time header to all responses with timing in milliseconds.
    Logs warning for requests exceeding the slow threshold.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and track timing.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with timing header
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time in milliseconds
        process_time_ms = (time.time() - start_time) * 1000

        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"

        # Log request with timing
        log_message = (
            f"{request.method} {request.url.path} "
            f"- {response.status_code} "
            f"- {process_time_ms:.2f}ms"
        )

        # Warn on slow requests
        if process_time_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(f"SLOW REQUEST: {log_message}")
        else:
            logger.info(log_message)

        return response
