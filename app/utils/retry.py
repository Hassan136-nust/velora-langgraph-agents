"""
Retry / exponential-backoff utilities and error classification.
"""

import time
import functools
from datetime import datetime, timezone


def classify_error(exc: Exception) -> str:
    """Classify an exception into a standard error type."""
    name = type(exc).__name__.lower()
    msg = str(exc).lower()

    if any(k in msg for k in ("rate limit", "429", "quota", "too many requests")):
        return "API_LIMIT"
    if any(k in msg for k in ("timeout", "timed out", "deadline")):
        return "TIMEOUT"
    if any(k in msg for k in ("connection", "network", "dns", "unreachable", "refused")):
        return "NETWORK_ERROR"
    if "auth" in msg or "401" in msg or "403" in msg:
        return "AUTH_ERROR"
    return "UNKNOWN"


def make_error_response(exc: Exception, fallback_action: str = "") -> dict:
    """Build a structured error JSON from an exception."""
    return {
        "error": {
            "type": classify_error(exc),
            "message": f"{type(exc).__name__}: {exc}",
            "fallback_action": fallback_action or "Using cached or reduced research mode",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator: retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap.
        exceptions: Tuple of exception types to catch.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        break
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
