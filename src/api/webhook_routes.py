import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, status, HTTPException
from src.api.auth import get_current_user
from src.schemas.webhook import (
    WebhookStatusResponseSchema,
    WebhookRegisterResponseSchema,
)
from src.services.webhook_service import webhook_service
from src.services.webhook_registration_service import webhook_registration_service
from src.services.pull_request_sync_service import pull_request_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])

@router.post("/webhooks/github", status_code=status.HTTP_200_OK)
async def github_webhook_receiver(request: Request):
    """
    Public webhook receiver for incoming GitHub webhook events.
    Verifies HMAC-SHA256 signature, validates delivery ID, and authoritatively
    syncs Pull Request state in PostgreSQL.
    """
    raw_body = await request.body()
    headers = dict(request.headers)
    return await webhook_service.handle_webhook(raw_body, headers)

@router.get("/projects/{project_id}/webhook", response_model=WebhookStatusResponseSchema)
async def get_project_webhook_status(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves safe webhook status metadata for a project.
    """
    return webhook_registration_service.get_webhook_status(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.post("/projects/{project_id}/webhook", response_model=WebhookRegisterResponseSchema)
async def register_project_webhook(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Registers a GitHub webhook for the project repository, generates a secure encrypted secret,
    and performs an initial PR synchronization.
    """
    return await webhook_registration_service.register_webhook(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.post("/projects/{project_id}/webhook/retry", response_model=WebhookRegisterResponseSchema)
async def retry_project_webhook_registration(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retries failed webhook registration for a project.
    """
    return await webhook_registration_service.register_webhook(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.delete("/projects/{project_id}/webhook")
async def delete_project_webhook(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Deletes the webhook from GitHub and updates project webhook_status to DISABLED.
    """
    return await webhook_registration_service.delete_webhook(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.post("/projects/{project_id}/sync-prs")
async def manual_sync_project_pull_requests(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Manually triggers full Pull Request synchronization from GitHub REST API into PostgreSQL.
    """
    count = pull_request_sync_service.sync_project_pull_requests(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )
    return {
        "message": f"Successfully synchronized {count} pull requests from GitHub.",
        "synced_prs_count": count
    }
