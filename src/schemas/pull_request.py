from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class PullRequestAuthorSchema(BaseModel):
    login: str
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None

class PullRequestItemSchema(BaseModel):
    number: int
    title: str
    author: PullRequestAuthorSchema
    state: str  # OPEN, CLOSED, MERGED, DRAFT
    is_draft: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    source_branch: str
    target_branch: str
    html_url: str
    additions: Optional[int] = 0
    deletions: Optional[int] = 0
    changed_files_count: Optional[int] = 0
    comments_count: Optional[int] = 0
    commits_count: Optional[int] = 0
    review_status: Optional[str] = "PENDING"

class PullRequestListResponseSchema(BaseModel):
    pull_requests: List[PullRequestItemSchema]
    page: int = 1
    per_page: int = 20
    total_count: int = 0

class PullRequestDetailSchema(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    author: PullRequestAuthorSchema
    state: str
    is_draft: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    source_branch: str
    target_branch: str
    source_sha: Optional[str] = None
    target_sha: Optional[str] = None
    html_url: str
    additions: int = 0
    deletions: int = 0
    changed_files_count: int = 0
    comments_count: int = 0
    commits_count: int = 0
    mergeable: Optional[bool] = None

class PullRequestFileSchema(BaseModel):
    sha: Optional[str] = None
    filename: str
    status: str  # added, modified, removed, renamed
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = None
    raw_url: Optional[str] = None
    contents_url: Optional[str] = None
    previous_filename: Optional[str] = None

class PullRequestDiffSchema(BaseModel):
    raw_diff: str
    files_count: int = 0
    additions: int = 0
    deletions: int = 0

class PullRequestReviewRequestSchema(BaseModel):
    notes: Optional[str] = None
