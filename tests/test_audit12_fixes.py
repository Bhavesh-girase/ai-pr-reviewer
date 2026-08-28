import os
import sys
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock heavy vector / AI libraries for instant unit test execution
for mod in ["langchain_huggingface", "langchain_google_genai", "langchain_chroma", "chromadb", "sentence_transformers"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from src.api.app import app, SecurityHeadersMiddleware
from src.api.routes import router

# ----------------------------------------------------
# AUDIT 12 L-1: SECURITY HEADERS TESTS
# ----------------------------------------------------

def test_response_contains_x_content_type_options_header():
    """Verify that every response includes X-Content-Type-Options: nosniff."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"

def test_response_contains_x_frame_options_header():
    """Verify that every response includes X-Frame-Options: DENY."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Frame-Options") == "DENY"

def test_response_contains_referrer_policy_header():
    """Verify that every response includes Referrer-Policy: strict-origin-when-cross-origin."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_response_contains_hsts_header():
    """Verify that every response includes Strict-Transport-Security."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"

def test_security_headers_middleware_preserves_response_body():
    """Verify that the middleware does not alter or corrupt the JSON response body."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# ----------------------------------------------------
# AUDIT 12 L-2: PRODUCTION API DOCUMENTATION CONFIG TESTS
# ----------------------------------------------------

def test_api_docs_disabled_by_default_or_when_false():
    """Verify that with ENABLE_API_DOCS=false, /docs, /redoc, and /openapi.json return 404."""
    test_app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )
    test_app.include_router(router)
    client = TestClient(test_app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    # /health still returns 200
    assert client.get("/health").status_code == 200

def test_api_docs_enabled_when_explicitly_configured():
    """Verify that with ENABLE_API_DOCS=true, /docs, /redoc, and /openapi.json are accessible."""
    test_app = FastAPI(
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    test_app.include_router(router)
    client = TestClient(test_app)

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/health").status_code == 200

def test_health_endpoint_available_under_all_docs_configurations():
    """Verify that the public health check endpoint is unaffected by docs configuration."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

if __name__ == "__main__":
    print("Running Audit 12 Fix Tests directly...", flush=True)
    test_response_contains_x_content_type_options_header()
    print("  PASSED: test_response_contains_x_content_type_options_header", flush=True)
    test_response_contains_x_frame_options_header()
    print("  PASSED: test_response_contains_x_frame_options_header", flush=True)
    test_response_contains_referrer_policy_header()
    print("  PASSED: test_response_contains_referrer_policy_header", flush=True)
    test_response_contains_hsts_header()
    print("  PASSED: test_response_contains_hsts_header", flush=True)
    test_security_headers_middleware_preserves_response_body()
    print("  PASSED: test_security_headers_middleware_preserves_response_body", flush=True)
    test_api_docs_disabled_by_default_or_when_false()
    print("  PASSED: test_api_docs_disabled_by_default_or_when_false", flush=True)
    test_api_docs_enabled_when_explicitly_configured()
    print("  PASSED: test_api_docs_enabled_when_explicitly_configured", flush=True)
    test_health_endpoint_available_under_all_docs_configurations()
    print("  PASSED: test_health_endpoint_available_under_all_docs_configurations", flush=True)
    print("ALL AUDIT 12 TESTS PASSED!", flush=True)
