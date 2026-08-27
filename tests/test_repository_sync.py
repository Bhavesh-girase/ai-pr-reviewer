import json
import hmac
import hashlib
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from fastapi import HTTPException

from src.security.webhook_signature import verify_github_signature
from src.services.repository_sync_service import RepositorySyncService
from src.services.webhook_service import WebhookService
from src.sync.incremental_indexer import IncrementalIndexer
from src.utils.security import encryption_service

@pytest.fixture
def sample_secret():
    return "test-secret-key-32-bytes-long-for-hmac!!"

@pytest.fixture
def mock_project_data():
    return {
        "id": "proj-uuid-123",
        "user_id": "user-uuid-456",
        "project_name": "Test Repo",
        "github_owner": "test-owner",
        "github_repository": "test-repo",
        "default_branch": "main",
        "auth_type": "connected_account",
        "current_commit_hash": "commit_aaa_111",
        "clone_path": "/tmp/test-repo",
        "chroma_path": "/tmp/test-chroma",
        "status": "READY",
        "sync_status": "READY",
        "webhook_secret_encrypted": encryption_service.encrypt("test-secret-key-32-bytes-long-for-hmac!!"),
        "webhook_status": "ACTIVE"
    }

class MockRemotes(list):
    def __init__(self, remotes_list, origin_mock):
        super().__init__(remotes_list)
        self.origin = origin_mock

def setup_mock_git_repo(old_sha="commit_aaa_111", new_sha="commit_aaa_111"):
    mock_origin = MagicMock()
    mock_origin.name = "origin"
    mock_origin.set_url = MagicMock()
    mock_origin.fetch = MagicMock()
    mock_origin.refs = {"main": MagicMock(commit=MagicMock(hexsha=new_sha))}

    mock_repo = MagicMock()
    mock_repo.head.commit.hexsha = old_sha
    mock_repo.remotes = MockRemotes([mock_origin], mock_origin)
    mock_repo.git.checkout = MagicMock()
    mock_repo.git.reset = MagicMock()
    return mock_repo

def test_incremental_indexer_delete_and_sync_changes(tmp_path):
    indexer = IncrementalIndexer.__new__(IncrementalIndexer)
    indexer.repository_name = "test-repo"
    indexer.persist_directory = str(tmp_path)
    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": ["src/main.py:0", "src/main.py:1"]}
    indexer.collection = mock_collection
    indexer.vectorstore = MagicMock()

    deleted_count = indexer.delete_file_chunks("src/main.py")
    assert deleted_count == 2
    mock_collection.delete.assert_called_with(ids=["src/main.py:0", "src/main.py:1"])

    with patch.object(indexer, "delete_file_chunks") as mock_delete, \
         patch.object(indexer, "index_single_file", return_value=3) as mock_index:
        total = indexer.sync_changes(
            repository_path=str(tmp_path),
            added_files=["src/new_feature.py"],
            modified_files=["src/utils.py"],
            deleted_files=["src/old_file.py"],
            renamed_files=[("src/old_name.py", "src/new_name.py")]
        )
        assert mock_delete.call_count == 4
        assert mock_index.call_count == 3
        assert total == 9

def test_manual_repository_sync_already_up_to_date(mock_project_data):
    async def run():
        service = RepositorySyncService()
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_project_data]

        mock_repo = setup_mock_git_repo("commit_aaa_111", "commit_aaa_111")

        with patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase), \
             patch.object(service, "_resolve_project_and_token", return_value=(mock_project_data, "token_123")), \
             patch("src.services.repository_sync_service.Repo", return_value=mock_repo):

            result = await service.sync_project_repository("proj-uuid-123")
            assert result["status"] == "READY"
            assert result["changed_files_count"] == 0
            assert "already synchronized" in result["message"].lower()

    asyncio.run(run())

def test_manual_repository_sync_with_changes(mock_project_data):
    async def run():
        service = RepositorySyncService()
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_project_data]

        mock_repo = setup_mock_git_repo("commit_aaa_111", "commit_bbb_222")

        with patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase), \
             patch.object(service, "_resolve_project_and_token", return_value=(mock_project_data, "token_123")), \
             patch("src.services.repository_sync_service.Repo", return_value=mock_repo), \
             patch.object(service, "_detect_git_changes", return_value=(["added.py"], ["modified.py"], ["deleted.py"], [])) as mock_diff, \
             patch("src.sync.incremental_indexer.IncrementalIndexer.sync_changes", return_value=6) as mock_sync:

            result = await service.sync_project_repository("proj-uuid-123")
            assert result["status"] == "READY"
            assert result["current_commit"] == "commit_bbb_222"
            assert result["changed_files_count"] == 3
            mock_sync.assert_called_once()

    asyncio.run(run())

def test_repository_sync_failure_preserves_old_commit(mock_project_data):
    async def run():
        service = RepositorySyncService()
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_project_data]

        mock_repo = setup_mock_git_repo("commit_aaa_111", "commit_bbb_222")
        mock_repo.remotes.origin.fetch.side_effect = Exception("Git network timeout")

        with patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase), \
             patch.object(service, "_resolve_project_and_token", return_value=(mock_project_data, "token_123")), \
             patch("src.services.repository_sync_service.Repo", return_value=mock_repo):

            with pytest.raises(HTTPException) as exc:
                await service.sync_project_repository("proj-uuid-123")
            assert exc.value.status_code == 500

            mock_supabase.table.return_value.update.assert_called()

    asyncio.run(run())

def test_push_webhook_on_default_branch(sample_secret, mock_project_data):
    async def run():
        service = WebhookService()
        payload = {
            "ref": "refs/heads/main",
            "before": "commit_aaa_111",
            "after": "commit_bbb_222",
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-owner"}
            }
        }
        raw_body = json.dumps(payload).encode("utf-8")
        computed = hmac.new(sample_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={computed}",
            "x-github-delivery": "deliv-push-uuid-1",
            "x-github-event": "push"
        }

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.select.return_value.ilike.return_value.ilike.return_value.execute.return_value.data = [mock_project_data]
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "deliv-rec-1"}]

        with patch("src.services.webhook_service.get_supabase_client", return_value=mock_supabase), \
             patch("src.services.repository_sync_service.repository_sync_service.sync_project_repository", return_value={"status": "READY"}) as mock_repo_sync:

            result = await service.handle_webhook(raw_body, headers)
            assert result["status"] == "processed"
            assert result["event_type"] == "push"
            assert result["branch"] == "main"
            mock_repo_sync.assert_called_once_with(
                project_id="proj-uuid-123",
                target_commit="commit_bbb_222",
                base_commit="commit_aaa_111"
            )

    asyncio.run(run())

def test_push_webhook_on_non_default_branch_ignored(sample_secret, mock_project_data):
    async def run():
        service = WebhookService()
        payload = {
            "ref": "refs/heads/feature-branch",
            "before": "commit_aaa_111",
            "after": "commit_bbb_222",
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-owner"}
            }
        }
        raw_body = json.dumps(payload).encode("utf-8")
        computed = hmac.new(sample_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={computed}",
            "x-github-delivery": "deliv-push-uuid-2",
            "x-github-event": "push"
        }

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.select.return_value.ilike.return_value.ilike.return_value.execute.return_value.data = [mock_project_data]
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "deliv-rec-2"}]

        with patch("src.services.webhook_service.get_supabase_client", return_value=mock_supabase), \
             patch("src.services.repository_sync_service.repository_sync_service.sync_project_repository") as mock_repo_sync:

            result = await service.handle_webhook(raw_body, headers)
            assert result["status"] == "ignored"
            assert result["reason"] == "non_default_branch"
            assert result["branch"] == "feature-branch"
            mock_repo_sync.assert_not_called()

    asyncio.run(run())

def test_concurrency_lock_protection(mock_project_data):
    async def run():
        service = RepositorySyncService()
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_project_data]

        mock_repo = setup_mock_git_repo("commit_aaa_111", "commit_bbb_222")

        with patch.object(service, "_resolve_project_and_token", return_value=(mock_project_data, "token_123")), \
             patch("src.services.repository_sync_service.get_supabase_client", return_value=mock_supabase), \
             patch("src.services.repository_sync_service.Repo", return_value=mock_repo), \
             patch.object(service, "_detect_git_changes", return_value=([], [], [], [])), \
             patch("src.sync.incremental_indexer.IncrementalIndexer.sync_changes", return_value=0):

            task1 = asyncio.create_task(service.sync_project_repository("proj-uuid-123"))
            task2 = asyncio.create_task(service.sync_project_repository("proj-uuid-123"))

            results = await asyncio.gather(task1, task2)
            assert len(results) == 2
            assert results[0]["status"] == "READY"
            assert results[1]["status"] == "READY"

    asyncio.run(run())
