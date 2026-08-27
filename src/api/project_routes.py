import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status, HTTPException
from src.api.auth import get_current_user
from src.schemas.project import (
    ProjectCreateSchema,
    ProjectUpdateSchema,
    ProjectResponseSchema,
    ProjectSyncResponseSchema,
    ProjectSyncStatusResponseSchema,
)
from src.services.project_service import project_service
from src.services.repository_sync_service import repository_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponseSchema])
async def list_projects(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns all provisioned projects belonging to the authenticated user.
    Uses Supabase RLS via user JWT token.
    """
    return project_service.get_user_projects(current_user["id"], current_user["token"])

@router.get("/{project_id}", response_model=ProjectResponseSchema)
async def get_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieves project details by UUID for the authenticated user.
    """
    return project_service.get_project_by_id(project_id, current_user["id"], current_user["token"])

@router.post("", response_model=ProjectResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateSchema,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Creates a new project record and triggers full backend provisioning:
    1. Validates repository metadata against GitHub API
    2. Allocates isolated project storage
    3. Clones repository using authenticated PAT
    4. Indexes codebase into project ChromaDB vector store
    5. Reads latest commit hash and transitions status to READY
    """
    return await project_service.create_project(
        user_id=current_user["id"],
        user_token=current_user["token"],
        input_data=payload.model_dump()
    )

@router.put("/{project_id}", response_model=ProjectResponseSchema)
async def update_project(
    project_id: str,
    payload: ProjectUpdateSchema,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Updates project metadata. Re-clones & re-indexes repository if owner/repository changes.
    """
    return await project_service.update_project(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"],
        update_data=payload.model_dump(exclude_unset=True)
    )

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deletes project record from database and recursively removes local repository and Chroma storage.
    """
    return project_service.delete_project(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"]
    )

@router.post("/{project_id}/sync", response_model=ProjectSyncResponseSchema)
async def sync_project_repository(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Manually triggers full repository and ChromaDB index synchronization.
    Fetches remote commits, calculates diff, incrementally updates vector store,
    and updates commit hash & timestamps.
    """
    return await repository_sync_service.sync_project_repository(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"]
    )

@router.get("/{project_id}/sync-status", response_model=ProjectSyncStatusResponseSchema)
async def get_project_sync_status(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieves real-time synchronization status and timestamps for a project.
    """
    return repository_sync_service.get_sync_status(
        project_id=project_id,
        user_id=current_user["id"],
        user_token=current_user["token"]
    )
