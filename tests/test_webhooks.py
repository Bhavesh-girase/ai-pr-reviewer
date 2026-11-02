import json
import hmac
import hashlib
import asyncio
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException
from src.security.webhook_signature import verify_github_signature
from src.services.webhook_service import WebhookService
from src.services.webhook_registration_service import WebhookRegistrationService
from src.services.pull_request_sync_service import PullRequestSyncService
from src.utils.security import encryption_service

@pytest.fixture
def sample_secret():
    return "test-secret-key-32-bytes-long-for-hmac!!"

@pytest.fixture
def sample_payload():
    return {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "id": 123456789,
            "number": 42,
            "title": "feat: new webhook sync system",
            "body": "Implements event-driven synchronization",
            "state": "open",
            "draft": False,
            "merged": False,
            "merged_at": None,
            "closed_at": None,
            "user": {
                "login": "octocat",
                "avatar_url": "https://avatars.githubusercontent.com/u/583231"
            },
            "head": {"ref": "feature/webhooks", "sha": "headsha42"},
            "base": {"ref": "main", "sha": "basesha42"},
            "html_url": "https://github.com/test-owner/test-repo/pull/42",
            "additions": 150,
            "deletions": 20,
            "changed_files": 5,
            "comments": 2,
            "commits": 3,
            "created_at": "2026-08-26T10:00:00Z",
            "updated_at": "2026-08-26T10:00:00Z"
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "test-owner"}
        }
    }

def test_verify_github_signature_valid(sample_secret, sample_payload):
    raw_body = json.dumps(sample_payload).encode("utf-8")
    computed = hmac.new(sample_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    sig_header = f"sha256={computed}"

    assert verify_github_signature(raw_body, sig_header, sample_secret) is True

def test_verify_github_signature_invalid(sample_secret, sample_payload):
    raw_body = json.dumps(sample_payload).encode("utf-8")
    sig_header = "sha256=invalid_hash_value_here"

    assert verify_github_signature(raw_body, sig_header, sample_secret) is False

def test_verify_github_signature_missing_or_malformed(sample_payload):
    raw_body = json.dumps(sample_payload).encode("utf-8")
    assert verify_github_signature(raw_body, None, "secret") is False
    assert verify_github_signature(raw_body, "malformed-header", "secret") is False

def test_webhook_missing_signature_raises_401(sample_payload):
    async def run():
        service = WebhookService()
        raw_body = json.dumps(sample_payload).encode("utf-8")
        headers = {"x-github-delivery": "deliv-123", "x-github-event": "pull_request"}

        with pytest.raises(HTTPException) as exc:
            await service.handle_webhook(raw_body, headers)
        assert exc.value.status_code == 401
    asyncio.run(run())

def test_webhook_replay_protection():
    async def run():
        service = WebhookService()
        sample_secret = "test-secret-key-32-bytes-long-for-hmac!!"
        payload = {
            "repository": {"name": "test-repo", "owner": {"login": "test-owner"}},
            "action": "opened",
        }
        raw_body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(sample_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "x-github-delivery": "deliv-existing-uuid",
            "x-github-event": "pull_request"
        }

        mock_supabase = MagicMock()
        project = {
            "id": "proj-1",
            "github_owner": "test-owner",
            "github_repository": "test-repo",
            "webhook_secret_encrypted": encryption_service.encrypt(sample_secret),
        }
        existing_delivery = {
            "id": "deliv-1",
            "project_id": "proj-1",
            "status": "PROCESSED",
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        execute = AsyncMock(side_effect=[
            SimpleNamespace(data=[project]),
            RuntimeError("duplicate delivery id"),
            SimpleNamespace(data=[existing_delivery]),
        ])

        with patch("src.services.webhook_service.get_supabase_client", return_value=mock_supabase), \
             patch("src.services.webhook_service._execute", execute):
            result = await service.handle_webhook(raw_body, headers)
            assert result["status"] == "ignored"
            assert result["reason"] == "duplicate_delivery"
            assert execute.await_count == 3
    asyncio.run(run())

def test_webhook_opened_event_processing(sample_secret, sample_payload):
    async def run():
        service = WebhookService()
        raw_body = json.dumps(sample_payload).encode("utf-8")
        computed = hmac.new(sample_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={computed}",
            "x-github-delivery": "deliv-new-unique-uuid",
            "x-github-event": "pull_request"
        }

        encrypted_secret = encryption_service.encrypt(sample_secret)
        mock_project = {
            "id": "proj-uuid-123",
            "github_owner": "test-owner",
            "github_repository": "test-repo",
            "webhook_secret_encrypted": encrypted_secret,
            "webhook_status": "ACTIVE"
        }

        mock_supabase = MagicMock()
        # Replay lookup returns empty
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        # Project lookup returns candidates
        mock_supabase.table.return_value.select.return_value.ilike.return_value.ilike.return_value.execute.return_value.data = [mock_project]
        # Insert delivery returns id
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "deliv-rec-1"}]

        execute = AsyncMock(side_effect=[
            SimpleNamespace(data=[mock_project]),
            SimpleNamespace(data=[{"id": "deliv-rec-1"}]),
            SimpleNamespace(data=[]),
            SimpleNamespace(data=[]),
        ])

        with patch("src.services.webhook_service.get_supabase_client", return_value=mock_supabase), \
             patch("src.services.webhook_service._execute", execute):
            with patch("src.services.pull_request_sync_service.pull_request_sync_service.sync_single_pull_request") as mock_sync:
                result = await service.handle_webhook(raw_body, headers)
                assert result["status"] == "processed"
                assert result["action"] == "opened"
                assert result["pr_number"] == 42
                mock_sync.assert_called_once()
    asyncio.run(run())


def test_failed_webhook_delivery_is_claimed_for_retry():
    async def run():
        service = WebhookService()
        supabase = MagicMock()
        existing_delivery = {
            "id": "delivery-1",
            "project_id": "project-1",
            "status": "FAILED",
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        execute = AsyncMock(side_effect=[
            RuntimeError("duplicate delivery id"),
            SimpleNamespace(data=[existing_delivery]),
            SimpleNamespace(data=[{"id": "delivery-1"}]),
        ])

        with patch("src.services.webhook_service._execute", execute):
            record_id, claimed = await service._claim_delivery(
                supabase=supabase,
                project_id="project-1",
                delivery_id="github-delivery-1",
                event_type="pull_request",
                action="opened",
                received_at=datetime.now(timezone.utc).isoformat(),
            )

        assert record_id == "delivery-1"
        assert claimed is True
        assert execute.await_count == 3

    asyncio.run(run())


def test_stale_processing_delivery_can_be_reclaimed():
    async def run():
        service = WebhookService()
        supabase = MagicMock()
        stale_received_at = datetime.now(timezone.utc) - timedelta(minutes=31)
        existing_delivery = {
            "id": "delivery-2",
            "project_id": "project-1",
            "status": "PROCESSING",
            "received_at": stale_received_at.isoformat(),
        }
        execute = AsyncMock(side_effect=[
            RuntimeError("duplicate delivery id"),
            SimpleNamespace(data=[existing_delivery]),
            SimpleNamespace(data=[{"id": "delivery-2"}]),
        ])

        with patch("src.services.webhook_service._execute", execute):
            record_id, claimed = await service._claim_delivery(
                supabase=supabase,
                project_id="project-1",
                delivery_id="github-delivery-2",
                event_type="push",
                action=None,
                received_at=datetime.now(timezone.utc).isoformat(),
            )

        assert record_id == "delivery-2"
        assert claimed is True
        update_payload = supabase.table.return_value.update.call_args.args[0]
        assert update_payload["status"] == "RETRYING"

    asyncio.run(run())


def test_active_webhook_delivery_is_retryable_not_processed_twice():
    async def run():
        service = WebhookService()
        supabase = MagicMock()
        existing_delivery = {
            "id": "delivery-3",
            "project_id": "project-1",
            "status": "PROCESSING",
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        execute = AsyncMock(side_effect=[
            RuntimeError("duplicate delivery id"),
            SimpleNamespace(data=[existing_delivery]),
        ])

        with patch("src.services.webhook_service._execute", execute):
            with pytest.raises(HTTPException) as exc:
                await service._claim_delivery(
                    supabase=supabase,
                    project_id="project-1",
                    delivery_id="github-delivery-3",
                    event_type="push",
                    action=None,
                    received_at=datetime.now(timezone.utc).isoformat(),
                )

        assert exc.value.status_code == 503
        assert exc.value.headers["Retry-After"] == "30"
        assert execute.await_count == 2

    asyncio.run(run())


def test_delivery_record_failure_returns_retryable_503():
    async def run():
        service = WebhookService()
        supabase = MagicMock()
        execute = AsyncMock(side_effect=[
            RuntimeError("database unavailable"),
            SimpleNamespace(data=[]),
        ])

        with patch("src.services.webhook_service._execute", execute):
            with pytest.raises(HTTPException) as exc:
                await service._claim_delivery(
                    supabase=supabase,
                    project_id="project-1",
                    delivery_id="github-delivery-unpersisted",
                    event_type="push",
                    action=None,
                    received_at=datetime.now(timezone.utc).isoformat(),
                )

        assert exc.value.status_code == 503
        assert exc.value.headers["Retry-After"] == "30"
        assert execute.await_count == 2

    asyncio.run(run())

def test_pull_request_sync_service_upsert(sample_payload):
    sync_service = PullRequestSyncService()
    pr_data = sample_payload["pull_request"]

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "pr-record-1", "github_pr_number": 42}]

    with patch("src.services.pull_request_sync_service.get_supabase_client", return_value=mock_supabase):
        result = sync_service.upsert_pull_request_record(
            project_id="proj-123",
            pr_data=pr_data,
            from_webhook=True
        )
        assert result["github_pr_number"] == 42

def test_webhook_registration_flow():
    async def run():
        reg_service = WebhookRegistrationService()
        mock_project = {
            "id": "proj-123",
            "github_owner": "test-owner",
            "github_repository": "test-repo",
            "auth_type": "connected_account"
        }

        mock_supabase = MagicMock()

        with patch.object(reg_service, "_resolve_project_and_token", return_value=(mock_project, "ghp_token")):
            with patch("src.services.webhook_registration_service.get_supabase_client", return_value=mock_supabase):
                with patch("src.github.github_client.GitHubClient.create_webhook", return_value={"id": 998877}):
                    with patch("src.services.pull_request_sync_service.pull_request_sync_service.sync_project_pull_requests", return_value=3):
                        res = await reg_service.register_webhook("proj-123", "user-1", "jwt-token")
                        assert res["webhook_status"] == "ACTIVE"
                        assert res["github_webhook_id"] == 998877
                        assert res["synced_prs_count"] == 3
    asyncio.run(run())
