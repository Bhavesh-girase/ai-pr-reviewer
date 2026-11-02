from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.security.rate_limiter import DistributedRateLimiter


def test_distributed_limiter_calls_shared_rpc_with_configured_window():
    limiter = DistributedRateLimiter(max_requests=4, window_seconds=60)
    supabase = MagicMock()
    supabase.rpc.return_value.execute.return_value = SimpleNamespace(
        data=[{"allowed": True, "retry_after": 0}]
    )

    with patch("src.security.rate_limiter.get_supabase_client", return_value=supabase) as get_client:
        limiter.check_rate_limit("user-1", "user-jwt")

    get_client.assert_called_once_with("user-jwt")
    supabase.rpc.assert_called_once_with(
        "consume_review_rate_limit",
        {"p_max_requests": 4, "p_window_seconds": 60},
    )
    supabase.rpc.return_value.execute.assert_called_once_with()


def test_distributed_limiter_preserves_429_and_retry_after_from_database():
    limiter = DistributedRateLimiter(max_requests=2, window_seconds=60)
    supabase = MagicMock()
    supabase.rpc.return_value.execute.return_value = SimpleNamespace(
        data=[{"allowed": False, "retry_after": 17}]
    )

    with patch("src.security.rate_limiter.get_supabase_client", return_value=supabase):
        with pytest.raises(HTTPException) as exc:
            limiter.check_rate_limit("user-1", "user-jwt")

    assert exc.value.status_code == 429
    assert exc.value.headers["Retry-After"] == "17"
    assert "Rate limit exceeded" in exc.value.detail


def test_distributed_limiter_fails_closed_when_shared_store_is_unavailable():
    limiter = DistributedRateLimiter(max_requests=2, window_seconds=60)

    with patch("src.security.rate_limiter.get_supabase_client", side_effect=RuntimeError("database unavailable")):
        with pytest.raises(HTTPException) as exc:
            limiter.check_rate_limit("user-1", "user-jwt")

    assert exc.value.status_code == 503
    assert exc.value.headers["Retry-After"] == "30"


def test_distributed_limiter_requires_authenticated_user_token():
    limiter = DistributedRateLimiter(max_requests=2, window_seconds=60)

    with pytest.raises(HTTPException) as exc:
        limiter.check_rate_limit("user-1")

    assert exc.value.status_code == 503
