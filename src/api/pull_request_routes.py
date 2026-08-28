import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from src.api.auth import get_current_user
from src.schemas.pull_request import (
    PullRequestListResponseSchema,
    PullRequestDetailSchema,
    PullRequestFileSchema,
    PullRequestDiffSchema,
    PullRequestReviewRequestSchema,
)
from src.security.rate_limiter import review_rate_limiter
from src.services.pull_request_service import pull_request_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/pull-requests", tags=["Pull Requests"])

@router.get("", response_model=PullRequestListResponseSchema)
async def list_pull_requests(
    project_id: str,
    state: str = Query("open", description="PR state filter: open, closed, all, merged, draft"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sort: str = Query("created", description="Sort field: created, updated, popularity, long-running"),
    direction: str = Query("desc", description="Sort direction: asc or desc"),
    search: Optional[str] = Query(None, description="Search query across PR title, author, branch, or number"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Fetches real-time Pull Requests for the project's GitHub repository.
    Strictly verifies project existence and multi-user ownership.
    """
    return pull_request_service.get_pull_requests(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
        state=state,
        page=page,
        per_page=per_page,
        sort=sort,
        direction=direction,
        search=search,
    )

@router.get("/{pr_number}", response_model=PullRequestDetailSchema)
async def get_pull_request(
    project_id: str,
    pr_number: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves full metadata for a specific Pull Request from GitHub.
    """
    return pull_request_service.get_pull_request(
        project_id=project_id,
        pr_number=pr_number,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.get("/{pr_number}/files", response_model=List[PullRequestFileSchema])
async def get_pull_request_files(
    project_id: str,
    pr_number: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves changed files, additions/deletions counts, and diff patches for a Pull Request.
    """
    return pull_request_service.get_pull_request_files(
        project_id=project_id,
        pr_number=pr_number,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.get("/{pr_number}/diff", response_model=PullRequestDiffSchema)
async def get_pull_request_diff(
    project_id: str,
    pr_number: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves the raw unified PR diff from GitHub.
    """
    return pull_request_service.get_pull_request_diff(
        project_id=project_id,
        pr_number=pr_number,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.post("/{pr_number}/review")
async def review_pull_request(
    project_id: str,
    pr_number: int,
    payload: Optional[PullRequestReviewRequestSchema] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Executes the existing AI Review Pipeline for the specified Project Pull Request.
    Does not require the user to provide a repository URL manually.
    Rate limited per authenticated user prior to expensive RAG/LLM processing.
    """
    user_id = current_user["id"]
    review_rate_limiter.check_rate_limit(user_id)

    return await pull_request_service.review_pull_request(
        project_id=project_id,
        pr_number=pr_number,
        user_id=user_id,
        user_token=current_user["token"],
    )
