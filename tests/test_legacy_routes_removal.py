import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_legacy_review_pr_route_is_removed():
    """Verify that the unauthenticated POST /review-pr endpoint is no longer accessible (404)."""
    response = client.post("/review-pr", json={
        "repo_url": "https://github.com/owner/repo",
        "owner": "owner",
        "repository": "repo",
        "pull_number": 1
    })
    assert response.status_code == 404

def test_legacy_webhook_route_is_removed():
    """Verify that the unauthenticated POST /webhook endpoint is no longer accessible (404)."""
    response = client.post("/webhook", json={"test": "payload"})
    assert response.status_code == 404

def test_health_check_endpoint_preserved():
    """Verify that GET /health remains active."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_github_webhook_endpoint_active_and_requires_signature():
    """Verify that POST /webhooks/github is mounted and rejects unsigned requests (401)."""
    response = client.post("/webhooks/github", json={"action": "opened"})
    assert response.status_code == 401
    assert "signature" in response.text.lower() or "missing" in response.text.lower()

def test_authenticated_review_endpoint_active_and_requires_jwt():
    """Verify that POST /projects/{project_id}/pull-requests/{pr_number}/review requires JWT auth."""
    response = client.post("/projects/test-proj-id/pull-requests/1/review")
    assert response.status_code in (401, 403)
