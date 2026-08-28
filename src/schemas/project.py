from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class ProjectStatusEnum(str, Enum):
    CREATING = "CREATING"
    CLONING = "CLONING"
    INDEXING = "INDEXING"
    READY = "READY"
    FAILED = "FAILED"

class ProjectSyncStatusEnum(str, Enum):
    READY = "READY"
    SYNCING = "SYNCING"
    SYNC_FAILED = "SYNC_FAILED"

class ProjectCreateSchema(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=100, description="Name of the project")
    github_owner: str = Field(..., min_length=1, max_length=100, description="GitHub repository owner/organization")
    github_repository: str = Field(..., min_length=1, max_length=100, description="GitHub repository name")
    default_branch: Optional[str] = Field("main", max_length=100, description="Default branch name")
    auth_type: str = Field("connected_account", max_length=50, description="Authentication mode: connected_account or custom_token")
    custom_token: Optional[str] = Field(None, max_length=500, description="Optional custom GitHub Personal Access Token")

class ProjectUpdateSchema(BaseModel):
    project_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated project name")
    github_owner: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated GitHub repository owner")
    github_repository: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated GitHub repository name")
    default_branch: Optional[str] = Field(None, max_length=100, description="Updated default branch")
    auth_type: Optional[str] = Field(None, max_length=50, description="Updated authentication mode")
    custom_token: Optional[str] = Field(None, max_length=500, description="Updated custom GitHub token")

class ProjectResponseSchema(BaseModel):
    id: str
    user_id: str
    project_name: str
    github_owner: str
    github_repository: str
    default_branch: str
    auth_type: str
    has_custom_token: bool = False
    clone_path: Optional[str] = None
    chroma_path: Optional[str] = None
    current_commit_hash: Optional[str] = None
    last_indexed_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    status: ProjectStatusEnum
    sync_status: Optional[str] = "READY"
    sync_error_message: Optional[str] = None
    last_sync_started_at: Optional[datetime] = None
    last_sync_completed_at: Optional[datetime] = None
    github_webhook_id: Optional[int] = None
    webhook_status: Optional[str] = "NOT_REGISTERED"
    webhook_registered_at: Optional[datetime] = None
    last_webhook_event_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectSyncResponseSchema(BaseModel):
    status: str
    current_commit: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    last_indexed_at: Optional[datetime] = None
    changed_files_count: int = 0
    message: str

class ProjectSyncStatusResponseSchema(BaseModel):
    project_id: str
    status: str
    sync_status: str
    current_commit_hash: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    last_indexed_at: Optional[datetime] = None
    last_sync_started_at: Optional[datetime] = None
    last_sync_completed_at: Optional[datetime] = None
    sync_error_message: Optional[str] = None
    is_syncing: bool = False
