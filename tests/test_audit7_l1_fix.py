import os
import sys
import asyncio
from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock heavy vector / AI libraries for instant unit test execution
for mod in ["langchain_huggingface", "langchain_google_genai", "langchain_chroma", "chromadb", "sentence_transformers"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from src.api.auth import get_current_user

# ----------------------------------------------------
# 1. AUDIT 7 L-1: AUTHENTICATION ERROR SANITIZATION TESTS
# ----------------------------------------------------

def test_missing_access_token_raises_clean_401():
    """Verify that an empty credentials token raises 401 with clean message."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(credentials))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing access token"

def test_invalid_or_expired_token_returns_clean_401():
    """Verify that a rejected user token returns generic 401 message."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-expired-jwt-token")
    
    with patch("src.api.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = MagicMock(user=None)
        mock_get_client.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(credentials))
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired access token."

def test_internal_upstream_exception_does_not_leak_details_to_client():
    """
    Verify that if Supabase/GoTrue throws an internal exception containing sensitive infrastructure info
    (e.g. internal database URL or connection failure), it is NEVER exposed in the HTTP response.
    """
    sensitive_internal_error = "Internal database connection failed at postgres://admin:secret123@internal-db-cluster:5432/auth_db"
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="jwt-causing-upstream-error")
    
    with patch("src.api.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception(sensitive_internal_error)
        mock_get_client.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(credentials))
        
        assert exc_info.value.status_code == 401
        # Crucial security assertion: sensitive internal error MUST NOT be in response detail
        assert sensitive_internal_error not in exc_info.value.detail
        assert "postgres://" not in exc_info.value.detail
        assert "secret123" not in exc_info.value.detail
        assert "internal-db-cluster" not in exc_info.value.detail
        assert exc_info.value.detail == "Invalid or expired access token."

def test_valid_authentication_succeeds():
    """Verify that a valid token returns the authenticated user dictionary."""
    valid_jwt = "valid-mock-user-jwt"
    mock_user_obj = MagicMock()
    mock_user_obj.id = "user-uuid-12345"
    mock_user_obj.email = "test@example.com"
    mock_user_obj.user_metadata = {"name": "Test User"}

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_jwt)

    with patch("src.api.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.get_user.return_value = MagicMock(user=mock_user_obj)
        mock_get_client.return_value = mock_client

        user = asyncio.run(get_current_user(credentials))
        assert user["id"] == "user-uuid-12345"
        assert user["email"] == "test@example.com"
        assert user["user_metadata"] == {"name": "Test User"}
        assert user["token"] == valid_jwt

if __name__ == "__main__":
    print("Running Audit 7 L-1 Fix Tests directly...", flush=True)
    test_missing_access_token_raises_clean_401()
    print("  PASSED: test_missing_access_token_raises_clean_401", flush=True)
    test_invalid_or_expired_token_returns_clean_401()
    print("  PASSED: test_invalid_or_expired_token_returns_clean_401", flush=True)
    test_internal_upstream_exception_does_not_leak_details_to_client()
    print("  PASSED: test_internal_upstream_exception_does_not_leak_details_to_client", flush=True)
    test_valid_authentication_succeeds()
    print("  PASSED: test_valid_authentication_succeeds", flush=True)
    print("ALL AUDIT 7 L-1 TESTS PASSED!", flush=True)
