import time
import logging
from collections import defaultdict
from typing import Dict, List, Optional
import threading
from fastapi import HTTPException, status

from src.config import LLM_REQUESTS_PER_MINUTE, REVIEW_RATE_LIMIT_PER_MINUTE
from src.api.auth import get_supabase_client
from src.utils.security import sanitize_error_message

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Sliding-window rate limiter per identity key (e.g., authenticated user_id).
    Maintains timestamp logs and calculates wait times before allowing requests.
    Thread-safe and async-safe.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check_rate_limit(self, key: str, user_token: Optional[str] = None) -> None:
        """
        Records a request for the given key and raises HTTPException(429) if limit exceeded.
        """
        now = time.time()
        with self._lock:
            # Evict timestamps outside the sliding window
            cutoff = now - self.window_seconds
            timestamps = [t for t in self._history[key] if t > cutoff]
            self._history[key] = timestamps

            if len(timestamps) >= self.max_requests:
                oldest_timestamp = timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest_timestamp)))
                logger.warning(f"Rate limit exceeded for key '{key}'. Current: {len(timestamps)}/{self.max_requests}. Retry-After: {retry_after}s")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many review requests. Rate limit exceeded. Please wait a moment before trying again.",
                    headers={"Retry-After": str(retry_after)}
                )

            # Record this request
            self._history[key].append(now)

    def reset(self, key: Optional[str] = None) -> None:
        """
        Resets history for a specific key or all keys (useful for testing).
        """
        with self._lock:
            if key:
                self._history.pop(key, None)
            else:
                self._history.clear()


class DistributedRateLimiter:
    """Use a Postgres RPC for an atomic per-user limit shared by all workers."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def check_rate_limit(self, key: str, user_token: Optional[str] = None) -> None:
        if not user_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review rate limiting is temporarily unavailable.",
                headers={"Retry-After": "30"},
            )

        try:
            supabase = get_supabase_client(user_token)
            result = supabase.rpc(
                "consume_review_rate_limit",
                {
                    "p_max_requests": self.max_requests,
                    "p_window_seconds": self.window_seconds,
                },
            ).execute()
            data = result.data or []
            row = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else None
            if not row or "allowed" not in row:
                raise RuntimeError("Rate-limit RPC returned an invalid response")
        except Exception as exc:
            logger.error(
                "Distributed review rate-limit check failed for user %s: %s",
                key,
                sanitize_error_message(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review rate limiting is temporarily unavailable.",
                headers={"Retry-After": "30"},
            )

        if not row["allowed"]:
            try:
                retry_after = max(1, int(row.get("retry_after", 1)))
            except (TypeError, ValueError):
                retry_after = 1
            logger.warning("Distributed review rate limit exceeded for user '%s'", key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many review requests. Rate limit exceeded. Please wait a moment before trying again.",
                headers={"Retry-After": str(retry_after)},
            )


class SharedLLMRateLimiter:
    """Wait for a shared Postgres-backed model request slot across all workers."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def wait_for_slot(self) -> None:
        supabase = get_supabase_client()
        while True:
            result = supabase.rpc(
                "consume_ai_request_rate_limit",
                {
                    "p_max_requests": self.max_requests,
                    "p_window_seconds": self.window_seconds,
                },
            ).execute()
            data = result.data or []
            row = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else None
            if not row or "allowed" not in row:
                raise RuntimeError("AI rate-limit RPC returned an invalid response")
            if row["allowed"]:
                return

            try:
                retry_after = max(1, int(row.get("retry_after", 1)))
            except (TypeError, ValueError):
                retry_after = 1
            logger.info("Shared AI request limit reached; waiting %s seconds", retry_after)
            time.sleep(retry_after)


# The production endpoint uses the database-backed limiter. Keep RateLimiter
# available as a small process-local implementation for isolated unit tests.
review_rate_limiter = DistributedRateLimiter(
    max_requests=REVIEW_RATE_LIMIT_PER_MINUTE,
    window_seconds=60
)

llm_request_rate_limiter = SharedLLMRateLimiter(
    max_requests=LLM_REQUESTS_PER_MINUTE,
    window_seconds=60,
)
