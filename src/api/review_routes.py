import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, Query, status

from src.api.auth import get_current_user
from src.schemas.review import (
    ReviewResponseSchema,
    ReviewDetailResponseSchema,
    ReviewListResponseSchema,
)
from src.services.review_service import review_service

logger = logging.getLogger("review_routes")

router = APIRouter(tags=["Reviews"])

@router.get(
    "/projects/{project_id}/reviews",
    response_model=ReviewListResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def list_project_reviews(
    project_id: str,
    pr_number: Optional[int] = Query(None, description="Filter by Pull Request number"),
    status: Optional[str] = Query(None, description="Filter by status (QUEUED, RUNNING, COMPLETED, FAILED, ALL)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("created_at", description="Sort field (created_at, completed_at, issues_count)"),
    direction: str = Query("desc", description="Sort direction (asc, desc)"),
    search: Optional[str] = Query(None, description="Search query matching summary"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Lists paginated review history belonging to a project.
    """
    return await review_service.list_project_reviews(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
        pr_number=pr_number,
        status_filter=status,
        page=page,
        per_page=per_page,
        sort=sort,
        direction=direction,
        search=search,
    )

@router.get(
    "/projects/{project_id}/reviews/{review_id}",
    response_model=ReviewDetailResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_review_details(
    project_id: str,
    review_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves full details of a single review including structured review_result JSON.
    """
    return await review_service.get_review_by_id(
        project_id=project_id,
        review_id=review_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )

@router.get(
    "/projects/{project_id}/pull-requests/{pr_number}/reviews",
    response_model=List[ReviewResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_pull_request_reviews(
    project_id: str,
    pr_number: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves all historical reviews performed on a specific Pull Request.
    """
    return await review_service.get_pull_request_reviews(
        project_id=project_id,
        pr_number=pr_number,
        user_id=current_user["id"],
        user_token=current_user["token"],
    )
