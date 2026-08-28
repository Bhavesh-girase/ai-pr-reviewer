import time
import logging
from collections import defaultdict
from typing import Dict, List, Optional
import threading
from fastapi import HTTPException, status

from src.config import REVIEW_RATE_LIMIT_PER_MINUTE

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

    def check_rate_limit(self, key: str) -> None:
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

# Global Review Rate Limiter instance (e.g., 10 reviews per minute per user)
review_rate_limiter = RateLimiter(
    max_requests=REVIEW_RATE_LIMIT_PER_MINUTE,
    window_seconds=60
)
