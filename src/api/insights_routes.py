import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status

from src.api.auth import get_current_user
from src.schemas.insights import InsightsResponseSchema
from src.services.insights_service import insights_service

logger = logging.getLogger("insights_routes")

router = APIRouter(tags=["Insights"])

@router.get(
    "/projects/{project_id}/insights",
    response_model=InsightsResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_project_insights(
    project_id: str,
    range: Optional[str] = Query("30d", description="Date filter range (7d, 30d, 90d, all)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves deterministic project analytics, time-series review trends, severity distribution,
    dynamically extracted issue categories, top problematic files, and repository review health.
    """
    return await insights_service.get_project_insights(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
        range_str=range or "30d",
    )
