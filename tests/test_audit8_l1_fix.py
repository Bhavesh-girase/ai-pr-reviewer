import os
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock heavy vector / AI libraries for instant unit test execution
for mod in ["langchain_huggingface", "langchain_google_genai", "langchain_chroma", "chromadb", "sentence_transformers"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from src.services.repository_sync_service import RepositorySyncService

# ----------------------------------------------------
# AUDIT 8 L-1: REPOSITORY SYNC OWNERSHIP HARDENING TESTS
# ----------------------------------------------------

def test_unauthorized_user_sync_raises_403_and_blocks_git_operations():
    """
    Verify that if User A attempts to sync User B's project:
    1. HTTP 403 Forbidden is raised with generic detail.
    2. No custom token or PAT is decrypted.
    3. No Git clone / fetch / diff operation is ever executed.
    """
    service = RepositorySyncService()
    user_b_project = {
        "id": "proj-uuid-user-b",
        "user_id": "user-uuid-b",
        "project_name": "User B Secret Repo",
        "github_owner": "owner-b",
        "github_repository": "secret-repo",
        "auth_type": "custom_token",
        "custom_token": "gAAAAABencrypted_token_b...",
        "default_branch": "main",
        "status": "READY",
        "sync_status": "READY"
    }

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [user_b_project]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [user_b_project]

    with patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase), \
         patch("src.services.repository_sync_service.encryption_service.decrypt_or_passthrough") as mock_decrypt, \
         patch("src.services.repository_sync_service.github_credentials_service.get_decrypted_pat") as mock_pat, \
         patch("src.services.repository_sync_service.Repo") as mock_git_repo:

        # User A calls sync on User B's project
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(service.sync_project_repository(
                project_id="proj-uuid-user-b",
                user_id="user-uuid-a-attacker",
                user_token="user_a_jwt_token"
            ))

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "You do not have permission to sync this project."

        # Verify no token decryption was attempted
        mock_decrypt.assert_not_called()
        mock_pat.assert_not_called()

        # Verify no Git operation was executed
        mock_git_repo.assert_not_called()
        mock_git_repo.clone_from.assert_not_called()

def test_owner_sync_resolves_credentials_and_proceeds():
    """
    Verify that the authentic owner can resolve their project and proceed with synchronization.
    """
    service = RepositorySyncService()
    owner_project = {
        "id": "proj-uuid-owner",
        "user_id": "user-uuid-owner",
        "project_name": "Owner Repo",
        "github_owner": "owner",
        "github_repository": "repo",
        "auth_type": "connected_account",
        "default_branch": "main",
        "status": "READY"
    }

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [owner_project]

    with patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase), \
         patch("src.services.repository_sync_service.github_credentials_service.get_decrypted_pat", return_value="pat_123"):

        project, token = service._resolve_project_and_token(
            project_id="proj-uuid-owner",
            user_id="user-uuid-owner",
            user_token="owner_jwt_token"
        )

        assert project["id"] == "proj-uuid-owner"
        assert token == "pat_123"

def test_missing_project_raises_404():
    """
    Verify that querying a non-existent project returns 404 Not Found.
    """
    service = RepositorySyncService()
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase):
        with pytest.raises(HTTPException) as exc_info:
            service._resolve_project_and_token(
                project_id="non-existent-proj",
                user_id="any-user",
                user_token="any_token"
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

def test_internal_background_sync_without_user_id_allowed():
    """
    Verify that internal/background operations where user_id is None continue to resolve the project.
    """
    service = RepositorySyncService()
    project_data = {
        "id": "proj-uuid-bg",
        "user_id": "user-uuid-bg",
        "project_name": "Background Project",
        "github_owner": "owner",
        "github_repository": "repo",
        "auth_type": "connected_account",
        "default_branch": "main"
    }

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project_data]

    with patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase), \
         patch("src.services.repository_sync_service.github_credentials_service.get_decrypted_pat", return_value="bg_pat"):

        project, token = service._resolve_project_and_token(
            project_id="proj-uuid-bg",
            user_id=None,
            user_token=None
        )

        assert project["id"] == "proj-uuid-bg"
        assert token == "bg_pat"

if __name__ == "__main__":
    print("Running Audit 8 L-1 Fix Tests directly...", flush=True)
    test_unauthorized_user_sync_raises_403_and_blocks_git_operations()
    print("  PASSED: test_unauthorized_user_sync_raises_403_and_blocks_git_operations", flush=True)
    test_owner_sync_resolves_credentials_and_proceeds()
    print("  PASSED: test_owner_sync_resolves_credentials_and_proceeds", flush=True)
    test_missing_project_raises_404()
    print("  PASSED: test_missing_project_raises_404", flush=True)
    test_internal_background_sync_without_user_id_allowed()
    print("  PASSED: test_internal_background_sync_without_user_id_allowed", flush=True)
    print("ALL AUDIT 8 L-1 TESTS PASSED!", flush=True)
