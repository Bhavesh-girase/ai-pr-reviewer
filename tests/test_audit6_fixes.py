import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from git import Repo, GitCommandError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock heavy vector / AI libraries for instant unit test execution
for mod in ["langchain_huggingface", "langchain_google_genai", "langchain_chroma", "chromadb", "sentence_transformers"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from src.utils.security import encryption_service, sanitize_error_message
from src.github.repository_manager import clone_repository, prepare_repository
from src.services.project_service import project_service
from src.schemas.project import ProjectResponseSchema

# ----------------------------------------------------
# 1. M-1: GIT CONFIG & AUTHENTICATION WITHOUT PERSISTENCE
# ----------------------------------------------------

def test_clone_repository_does_not_persist_pat_in_git_config():
    """Verify that clone_repository leaves a clean origin URL without token in .git/config."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir) / "test_repo"
        clean_url = "https://github.com/octocat/Hello-World.git"
        secret_token = "ghp_TestSecretToken1234567890abcdef"

        with patch("git.Repo.clone_from") as mock_clone:
            def fake_clone(url, path, c=None):
                path.mkdir(parents=True, exist_ok=True)
                r = Repo.init(path)
                r.create_remote("origin", url)
                return r

            mock_clone.side_effect = fake_clone
            clone_repository(clean_url, repo_dir, token=secret_token)

            # Check clone arguments: clean URL was used, token was passed in ephemeral config
            assert mock_clone.called
            args, kwargs = mock_clone.call_args
            assert args[0] == clean_url
            assert kwargs.get("c") == [f"http.extraHeader=Authorization: Bearer {secret_token}"]

            # Inspect actual .git/config
            git_config_path = repo_dir / ".git" / "config"
            assert git_config_path.exists()
            config_content = git_config_path.read_text(encoding="utf-8")

            # Must NOT contain token
            assert secret_token not in config_content
            assert "x-access-token" not in config_content
            assert "Authorization" not in config_content
            assert "url = https://github.com/octocat/Hello-World.git" in config_content

def test_update_repository_uses_persistent_git_options():
    """Verify that update_repository uses set_persistent_git_options for ephemeral auth."""
    from src.github.repository_manager import update_repository
    secret_token = "ghp_TestSecretToken1234567890abcdef"
    with patch("src.github.repository_manager.Repo") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        update_repository(Path("/dummy/path"), token=secret_token)

        # Ensure set_persistent_git_options was called with extraHeader
        mock_repo.git.set_persistent_git_options.assert_any_call(
            c=f"http.extraHeader=Authorization: Bearer {secret_token}"
        )
        mock_repo.git.pull.assert_called_once()
        # Ensure cleanup reset occurred
        assert mock_repo.git.set_persistent_git_options.call_count == 2

# ----------------------------------------------------
# 2. M-2: CENTRALIZED ERROR SANITIZER
# ----------------------------------------------------

def test_sanitize_git_url_with_x_access_token():
    raw_error = "GitCommandError: cmd 'git clone https://x-access-token:ghp_1234567890abcdef@github.com/owner/repo.git' failed"
    sanitized = sanitize_error_message(raw_error)
    assert "ghp_1234567890abcdef" not in sanitized
    assert "https://***@github.com/owner/repo.git" in sanitized

def test_sanitize_bearer_token_and_raw_pat():
    raw_error = "HTTP 401: Authorization failed for Bearer mySecretJwtToken and standalone ghp_VerySecretTokenValue12345 and github_pat_11AAAAAA00000000000000_12345678"
    sanitized = sanitize_error_message(raw_error)
    assert "mySecretJwtToken" not in sanitized
    assert "ghp_VerySecretTokenValue12345" not in sanitized
    assert "github_pat_11AAAAAA00000000000000_12345678" not in sanitized
    assert "Bearer ***" in sanitized
    assert "ghp_***" in sanitized
    assert "github_pat_***" in sanitized

def test_sanitize_git_command_error_object():
    err = GitCommandError(
        ["git", "fetch", "https://x-access-token:ghp_SuperSecret999@github.com/owner/repo.git"],
        128,
        stderr="fatal: Authentication failed for 'https://x-access-token:ghp_SuperSecret999@github.com/owner/repo.git/'"
    )
    sanitized = sanitize_error_message(err)
    assert "ghp_SuperSecret999" not in sanitized
    assert "https://***@github.com" in sanitized

# ----------------------------------------------------
# 3. M-3: ENCRYPTION & COMPATIBILITY FOR projects.custom_token
# ----------------------------------------------------

def test_custom_token_encryption_on_project_create():
    """Verify that project_service encrypts custom_token before persisting to DB."""
    user_id = "user-audit6-123"
    user_token = "jwt-user-token"
    raw_pat = "ghp_PersonalCustomTokenSecret123"

    with patch("src.services.project_service.get_supabase_client") as mock_supabase, \
         patch("src.services.project_service.project_provisioner.provision_project", new_callable=AsyncMock) as mock_prov:
        
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client

        # Mock table().insert().execute()
        created_row = {
            "id": "proj-uuid-1",
            "user_id": user_id,
            "project_name": "Test Project",
            "github_owner": "octocat",
            "github_repository": "hello-world",
            "default_branch": "main",
            "auth_type": "custom_token",
            "custom_token": encryption_service.encrypt(raw_pat),
            "status": "CREATING"
        }
        mock_client.table().insert.return_value.execute.return_value = MagicMock(data=[created_row])
        mock_client.table().update.return_value.eq.return_value.execute.return_value = MagicMock(data=[created_row])
        mock_prov.return_value = {"status": "READY", "clone_path": "/data/test"}

        # Also mock get_repository
        with patch.object(project_service, "_get_github_client_for_user") as mock_gh:
            mock_gh_client = MagicMock()
            mock_gh_client.get_repository.return_value = {"default_branch": "main"}
            mock_gh.return_value = mock_gh_client

            import asyncio
            input_data = {
                "project_name": "Test Project",
                "github_owner": "octocat",
                "github_repository": "hello-world",
                "auth_type": "custom_token",
                "custom_token": raw_pat
            }
            res = asyncio.run(project_service.create_project(user_id, user_token, input_data))

            # Verify insert payload contained ciphertext, NOT plaintext
            insert_call_args = mock_client.table().insert.call_args[0][0]
            assert insert_call_args["custom_token"] != raw_pat
            assert insert_call_args["custom_token"].startswith("gAAAAA")
            # Verify response schema does not expose custom_token
            assert "custom_token" not in res
            assert res.get("has_custom_token") is True

def test_custom_token_decrypt_or_passthrough_compatibility():
    """Verify decrypt_or_passthrough cleanly decrypts ciphertext and preserves legacy plaintext."""
    real_token = "ghp_LegacyOrModernToken12345"

    # Case A: Encrypted ciphertext
    ciphertext = encryption_service.encrypt(real_token)
    decrypted = encryption_service.decrypt_or_passthrough(ciphertext)
    assert decrypted == real_token

    # Case B: Legacy plaintext in existing database row
    legacy_plaintext = "ghp_ExistingUnencryptedToken12345"
    passthrough = encryption_service.decrypt_or_passthrough(legacy_plaintext)
    assert passthrough == legacy_plaintext

# ----------------------------------------------------
# 4. L-1: WORKSPACE PATH ISOLATION
# ----------------------------------------------------

def test_prepare_repository_uses_explicit_local_path():
    """Verify prepare_repository strictly utilizes the provided project local_path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_repo_path = Path(tmp_dir) / "data" / "repositories" / "user-123" / "proj-456"
        clean_url = "https://github.com/octocat/Hello-World.git"

        with patch("src.github.repository_manager.clone_repository") as mock_clone:
            mock_clone.return_value = project_repo_path
            res_path = prepare_repository(clean_url, local_path=project_repo_path)
            assert res_path == project_repo_path
            mock_clone.assert_called_once_with(clean_url, project_repo_path, token=None)

if __name__ == "__main__":
    print("Running Audit 6 Fixes Tests directly...", flush=True)
    test_clone_repository_does_not_persist_pat_in_git_config()
    print("  PASSED: test_clone_repository_does_not_persist_pat_in_git_config", flush=True)
    test_sanitize_git_url_with_x_access_token()
    print("  PASSED: test_sanitize_git_url_with_x_access_token", flush=True)
    test_sanitize_bearer_token_and_raw_pat()
    print("  PASSED: test_sanitize_bearer_token_and_raw_pat", flush=True)
    test_sanitize_git_command_error_object()
    print("  PASSED: test_sanitize_git_command_error_object", flush=True)
    test_custom_token_encryption_on_project_create()
    print("  PASSED: test_custom_token_encryption_on_project_create", flush=True)
    test_custom_token_decrypt_or_passthrough_compatibility()
    print("  PASSED: test_custom_token_decrypt_or_passthrough_compatibility", flush=True)
    test_prepare_repository_uses_explicit_local_path()
    print("  PASSED: test_prepare_repository_uses_explicit_local_path", flush=True)
    print("ALL 7 AUDIT 6 TESTS PASSED!", flush=True)
