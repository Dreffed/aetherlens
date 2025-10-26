"""
Rate limiting middleware for API protection.
"""

import time
from collections import defaultdict

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier (IP address or user ID)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - window_seconds

        # Remove old requests outside window
        self.requests[key] = [
            timestamp for timestamp in self.requests[key] if timestamp > window_start
        ]

        # Check if under limit
        current_count = len(self.requests[key])

        if current_count < max_requests:
            self.requests[key].append(now)
            return True, max_requests - current_count - 1

        return False, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on API endpoints."""

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.limiter = InMemoryRateLimiter()
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to request."""

        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client identifier (IP or user ID)
        client_ip = request.client.host

        # Check minute limit
        minute_allowed, minute_remaining = self.limiter.is_allowed(
            f"{client_ip}:minute", self.requests_per_minute, 60
        )

        # Check hour limit
        hour_allowed, hour_remaining = self.limiter.is_allowed(
            f"{client_ip}:hour", self.requests_per_hour, 3600
        )

        if not minute_allowed:
            logger.warning(
                "Rate limit exceeded (minute)", client_ip=client_ip, path=request.url.path
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Try again in 1 minute.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        if not hour_allowed:
            logger.warning("Rate limit exceeded (hour)", client_ip=client_ip, path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later.", "retry_after": 3600},
                headers={"Retry-After": "3600"},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(minute_remaining)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_remaining)

        return response
