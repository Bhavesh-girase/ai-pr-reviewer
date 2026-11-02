import os
import secrets
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from starlette.concurrency import run_in_threadpool

from src.api.auth import get_supabase_client
from src.github.github_client import GitHubClient
from src.utils.security import encryption_service
from src.services.project_service import project_service
from src.services.github_credentials_service import github_credentials_service
from src.services.pull_request_sync_service import pull_request_sync_service

logger = logging.getLogger(__name__)


async def _execute(query):
    """Execute a synchronous Supabase/PostgREST query outside the event loop."""
    return await run_in_threadpool(query.execute)


class WebhookRegistrationService:
    """
    Handles GitHub repository webhook registration, secret generation,
    lifecycle state transitions, and initial PR synchronization.
    """

    def _get_webhook_url(self) -> str:
        base_url = os.getenv(
            "GITHUB_WEBHOOK_BASE_URL",
            os.getenv("WEBHOOK_BASE_URL", os.getenv("VITE_API_BASE_URL", "https://pr-reviewer-api.local"))
        )
        return f"{base_url.rstrip('/')}/webhooks/github"

    def _resolve_project_and_token(
        self,
        project_id: str,
        user_id: str,
        user_token: str
    ) -> tuple[Dict[str, Any], str]:
        project = project_service.get_project_by_id(project_id, user_id, user_token)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        token = github_credentials_service.resolve_project_token(
            project,
            user_id,
            user_token,
        )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No GitHub access token available to manage webhooks."
            )

        return project, token

    async def register_webhook(
        self,
        project_id: str,
        user_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        """
        Generates encrypted secret, registers webhook on GitHub,
        updates DB to ACTIVE, and executes initial PR synchronization.
        """
        project, token = await run_in_threadpool(
            self._resolve_project_and_token,
            project_id,
            user_id,
            user_token,
        )
        owner = project["github_owner"]
        repo = project["github_repository"]
        webhook_url = self._get_webhook_url()

        # Step 1: Generate cryptographic secret
        raw_secret = secrets.token_hex(32)
        encrypted_secret = encryption_service.encrypt(raw_secret)

        supabase = await run_in_threadpool(get_supabase_client, user_token)

        # Mark status REGISTERING
        await _execute(
            supabase.table("projects").update({"webhook_status": "REGISTERING"}).eq("id", project_id)
        )

        # Step 2: Register on GitHub REST API
        client = GitHubClient(token=token)
        try:
            hook_res = await run_in_threadpool(
                client.create_webhook,
                owner=owner,
                repository=repo,
                webhook_url=webhook_url,
                secret=raw_secret,
                events=["pull_request"],
            )
            webhook_id = hook_res.get("id")
        except HTTPException as he:
            logger.error(f"GitHub webhook registration failed for {owner}/{repo}: {he.detail}")
            await _execute(supabase.table("projects").update({
                "webhook_status": "FAILED",
                "error_message": f"Webhook registration failed: {he.detail}"
            }).eq("id", project_id))
            raise
        except Exception as e:
            logger.error(f"Unexpected error registering webhook for {owner}/{repo}: {str(e)}")
            await _execute(supabase.table("projects").update({
                "webhook_status": "FAILED",
                "error_message": f"Webhook registration failed: {str(e)}"
            }).eq("id", project_id))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register GitHub webhook: {str(e)}"
            )

        now_iso = datetime.now(timezone.utc).isoformat()

        # Step 3: Update DB record to ACTIVE
        update_payload = {
            "github_webhook_id": webhook_id,
            "webhook_status": "ACTIVE",
            "webhook_registered_at": now_iso,
            "webhook_secret_encrypted": encrypted_secret,
            "error_message": None
        }
        await _execute(supabase.table("projects").update(update_payload).eq("id", project_id))

        # Step 4: Perform Initial Pull Request Synchronization
        synced_count = 0
        try:
            synced_count = await run_in_threadpool(
                pull_request_sync_service.sync_project_pull_requests,
                project_id=project_id,
                user_id=user_id,
                user_token=user_token,
            )
        except Exception as e:
            logger.warning(f"Initial PR sync warning for project {project_id}: {str(e)}")

        logger.info(f"Successfully registered webhook #{webhook_id} for project {project_id} (Synced {synced_count} PRs)")

        return {
            "message": "GitHub Webhook registered and verified successfully.",
            "github_webhook_id": webhook_id,
            "webhook_status": "ACTIVE",
            "synced_prs_count": synced_count
        }

    async def delete_webhook(
        self,
        project_id: str,
        user_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        """
        Removes webhook from GitHub and updates project webhook_status to DISABLED.
        """
        project, token = await run_in_threadpool(
            self._resolve_project_and_token,
            project_id,
            user_id,
            user_token,
        )
        owner = project["github_owner"]
        repo = project["github_repository"]
        hook_id = project.get("github_webhook_id")

        if hook_id:
            client = GitHubClient(token=token)
            try:
                await run_in_threadpool(
                    client.delete_webhook,
                    owner=owner,
                    repository=repo,
                    hook_id=int(hook_id),
                )
            except Exception as e:
                logger.warning(f"Failed to delete webhook #{hook_id} from GitHub: {str(e)}")

        supabase = await run_in_threadpool(get_supabase_client, user_token)
        await _execute(supabase.table("projects").update({
            "github_webhook_id": None,
            "webhook_status": "DISABLED",
            "webhook_secret_encrypted": None
        }).eq("id", project_id))

        return {"message": "Webhook unregistered successfully."}

    def get_webhook_status(
        self,
        project_id: str,
        user_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        """
        Returns safe webhook status metadata. Never leaks secrets or tokens.
        """
        project = project_service.get_project_by_id(project_id, user_id, user_token)
        webhook_url = self._get_webhook_url()

        return {
            "project_id": project_id,
            "webhook_status": project.get("webhook_status", "NOT_REGISTERED"),
            "webhook_registered_at": project.get("webhook_registered_at"),
            "last_webhook_event_at": project.get("last_webhook_event_at"),
            "github_webhook_id": project.get("github_webhook_id"),
            "webhook_url": webhook_url
        }

webhook_registration_service = WebhookRegistrationService()
