import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from src.api.auth import get_current_user
from src.schemas.github_settings import (
    GitHubTokenRequest,
    GitHubStatusResponse,
    GitHubTestResponse,
    GitHubConnectResponse,
    GitHubDisconnectResponse
)
from src.services.github_service import github_service
from src.services.github_credentials_service import github_credentials_service

logger = logging.getLogger(__name__)

settings_router = APIRouter(prefix="/settings/github", tags=["Settings & GitHub Integration"])

@settings_router.get("", response_model=GitHubStatusResponse)
async def get_github_integration_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    GET /settings/github
    Returns whether current user has connected a GitHub account and public profile info.
    """
    user_id = current_user["id"]
    user_token = current_user.get("token")
    cred = github_credentials_service.get_credential(user_id, user_token=user_token)
    
    if not cred:
        return GitHubStatusResponse(
            connected=False,
            username=None,
            avatar_url=None,
            name=None
        )
    
    return GitHubStatusResponse(
        connected=True,
        username=cred.get("github_username"),
        avatar_url=cred.get("github_avatar_url"),
        name=cred.get("github_username")
    )

@settings_router.post("/test", response_model=GitHubTestResponse)
async def test_github_connection(
    request: GitHubTokenRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    POST /settings/github/test
    Tests a Personal Access Token against GitHub API without storing it.
    """
    github_info = await github_service.validate_token_and_get_user(request.token)
    return GitHubTestResponse(
        success=True,
        username=github_info["username"],
        name=github_info["name"],
        avatar=github_info["avatar_url"]
    )

@settings_router.post("/connect", response_model=GitHubConnectResponse)
async def connect_github_account(
    request: GitHubTokenRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    POST /settings/github/connect
    Validates, encrypts, and stores PAT in PostgreSQL database for the current user.
    """
    user_id = current_user["id"]
    user_token = current_user.get("token")
    res = await github_credentials_service.connect_credential(user_id, request.token, user_token=user_token)
    return GitHubConnectResponse(**res)

@settings_router.delete("", response_model=GitHubDisconnectResponse)
async def disconnect_github_account(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    DELETE /settings/github
    Disconnects GitHub account and removes stored credential from database.
    """
    user_id = current_user["id"]
    user_token = current_user.get("token")
    res = github_credentials_service.delete_credential(user_id, user_token=user_token)
    return GitHubDisconnectResponse(**res)
