import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from pydantic import ValidationError
from src.api.app import app
from src.schemas.project import ProjectCreateSchema, ProjectUpdateSchema
from src.security.rate_limiter import RateLimiter, review_rate_limiter
from src.config import CORS_ALLOWED_ORIGINS

client = TestClient(app)

# ----------------------------------------------------
# 1. CORS TESTS
# ----------------------------------------------------

def test_cors_trusted_origin_allowed():
    """Verify that requests from allowed origins receive appropriate CORS headers."""
    trusted_origin = "http://localhost:5173"
    response = client.options(
        "/health",
        headers={
            "Origin": trusted_origin,
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == trusted_origin
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_untrusted_origin_rejected():
    """Verify that requests from untrusted origins are NOT granted CORS access."""
    untrusted_origin = "https://evil-attacker.com"
    response = client.options(
        "/health",
        headers={
            "Origin": untrusted_origin,
            "Access-Control-Request-Method": "GET"
        }
    )
    # Untrusted origin should NOT be reflected in access-control-allow-origin
    assert response.headers.get("access-control-allow-origin") != untrusted_origin
    assert response.headers.get("access-control-allow-origin") != "*"

def test_cors_wildcard_not_present_with_credentials():
    """Verify that allow_origins does not contain wildcard '*' in production config."""
    assert "*" not in CORS_ALLOWED_ORIGINS

# ----------------------------------------------------
# 2. RATE LIMITING TESTS
# ----------------------------------------------------

def test_rate_limiter_allows_under_limit():
    """Verify rate limiter allows requests up to max_requests."""
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    user = "user-123"
    limiter.check_rate_limit(user)
    limiter.check_rate_limit(user)
    limiter.check_rate_limit(user)
    # 3 calls allowed without exception

def test_rate_limiter_blocks_over_limit():
    """Verify rate limiter raises 429 when limit is exceeded."""
    from fastapi import HTTPException
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    user = "user-456"
    limiter.check_rate_limit(user)
    limiter.check_rate_limit(user)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit(user)
    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert "Rate limit exceeded" in exc_info.value.detail

def test_rate_limiter_distinct_user_isolation():
    """Verify distinct users maintain separate rate limit buckets."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    user_a = "user-aaa"
    user_b = "user-bbb"
    limiter.check_rate_limit(user_a)
    limiter.check_rate_limit(user_a)
    
    # user_b should not be affected by user_a's rate limit
    limiter.check_rate_limit(user_b)
    limiter.check_rate_limit(user_b)

def test_review_endpoint_enforces_rate_limit():
    """Verify that POST /projects/{project_id}/pull-requests/{pr_number}/review triggers rate limiting."""
    from src.api.auth import get_current_user
    review_rate_limiter.reset("test-rate-user")
    
    # Configure low limit for testing
    original_limit = review_rate_limiter.max_requests
    review_rate_limiter.max_requests = 2
    
    user_auth = {
        "id": "test-rate-user",
        "email": "rate@test.com",
        "user_metadata": {},
        "token": "valid-test-token"
    }
    
    app.dependency_overrides[get_current_user] = lambda: user_auth
    try:
        with patch("src.api.pull_request_routes.pull_request_service.review_pull_request", new_callable=AsyncMock) as mock_review:
            mock_review.return_value = {"status": "QUEUED", "review_id": "rev-1"}
            
            # Call 1: Success
            res1 = client.post("/projects/proj-123/pull-requests/10/review")
            assert res1.status_code == 200
            
            # Call 2: Success
            res2 = client.post("/projects/proj-123/pull-requests/10/review")
            assert res2.status_code == 200
            
            # Call 3: Rate Limited (429)
            res3 = client.post("/projects/proj-123/pull-requests/10/review")
            assert res3.status_code == 429
            assert "Retry-After" in res3.headers
            assert "Rate limit exceeded" in res3.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        review_rate_limiter.max_requests = original_limit
        review_rate_limiter.reset("test-rate-user")

# ----------------------------------------------------
# 3. PYDANTIC LENGTH BOUNDS TESTS
# ----------------------------------------------------

def test_project_create_schema_valid():
    """Verify valid inputs pass schema validation."""
    payload = {
        "project_name": "My Awesome Project",
        "github_owner": "octocat",
        "github_repository": "hello-world",
        "default_branch": "main",
        "auth_type": "connected_account"
    }
    schema = ProjectCreateSchema(**payload)
    assert schema.project_name == "My Awesome Project"
    assert schema.github_owner == "octocat"
    assert schema.github_repository == "hello-world"

def test_project_create_schema_exceeding_max_length():
    """Verify fields exceeding 100 chars fail validation."""
    oversized_string = "a" * 101
    
    # Oversized project_name
    with pytest.raises(ValidationError):
        ProjectCreateSchema(
            project_name=oversized_string,
            github_owner="octocat",
            github_repository="hello-world"
        )
        
    # Oversized github_owner
    with pytest.raises(ValidationError):
        ProjectCreateSchema(
            project_name="Valid Project",
            github_owner=oversized_string,
            github_repository="hello-world"
        )

    # Oversized github_repository
    with pytest.raises(ValidationError):
        ProjectCreateSchema(
            project_name="Valid Project",
            github_owner="octocat",
            github_repository=oversized_string
        )

def test_project_update_schema_exceeding_max_length():
    """Verify update schema enforces max_length on partial updates."""
    oversized_string = "b" * 101
    with pytest.raises(ValidationError):
        ProjectUpdateSchema(project_name=oversized_string)
