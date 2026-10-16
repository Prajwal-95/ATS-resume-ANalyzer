"""
In-memory sliding-window rate limiter.

NOTE: This limiter is per-process. In a multi-worker deployment, each worker
maintains its own counters, so effective limits are multiplied by the number
of workers. For distributed rate limiting, use a shared store (e.g., Redis).
"""
import time
import threading
from collections import defaultdict, deque
from typing import Optional

from fastapi import Request, HTTPException, status

from app.config import settings


class RateLimiter:
    """Thread-safe sliding-window rate limiter."""

    def __init__(self):
        self._lock = threading.Lock()
        # key -> deque of timestamps
        self._windows: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, dict]:
        """
        Check if a request under `key` is allowed.
        Returns (allowed, headers_dict).
        """
        now = time.monotonic()
        window_start = now - window_seconds

        with self._lock:
            dq = self._windows[key]
            # Remove expired entries
            while dq and dq[0] < window_start:
                dq.popleft()

            remaining = max_requests - len(dq)
            reset_at = int(dq[0] + window_seconds) if dq else int(now + window_seconds)

            headers = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(max(0, remaining - 1)),
                "X-RateLimit-Reset": str(reset_at),
            }

            if len(dq) >= max_requests:
                return False, headers

            dq.append(now)
            return True, headers

    def cleanup(self, max_age_seconds: int = 3600):
        """Remove stale entries to prevent memory growth."""
        now = time.monotonic()
        with self._lock:
            keys_to_remove = []
            for key, dq in self._windows.items():
                while dq and dq[0] < now - max_age_seconds:
                    dq.popleft()
                if not dq:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._windows[key]


_rate_limiter = RateLimiter()


def get_client_key(request: Request, prefix: str = "default") -> str:
    """Build a rate-limit key from client IP + route prefix."""
    client_ip = request.client.host if request.client else "unknown"
    return f"{prefix}:{client_ip}"


def check_rate_limit(
    request: Request,
    prefix: str = "default",
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None,
) -> dict:
    """
    Check rate limit for a request. Raises HTTPException(429) if exceeded.
    Returns rate-limit headers to include in the response.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return {}

    limit = max_requests or settings.RATE_LIMIT_DEFAULT
    window = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
    key = get_client_key(request, prefix)

    allowed, headers = _rate_limiter.is_allowed(key, limit, window)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={**headers, "Retry-After": str(window)},
        )
    return headers
