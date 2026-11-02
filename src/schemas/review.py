from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl

class ReviewRequest(BaseModel):
    repo_url: Optional[Union[HttpUrl, str]] = None
    owner: str
    repository: str
    pull_number: int

class ReviewStatusEnum(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReviewQueueResponseSchema(BaseModel):
    review_id: str
    status: str
    created_at: Optional[str] = None

class ReviewResponseSchema(BaseModel):
    id: str
    project_id: str
    pull_request_id: str
    github_pr_number: int
    status: str
    summary: Optional[str] = None
    issues_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    files_reviewed: int = 0
    lines_analyzed: int = 0
    model_name: Optional[str] = "Gemini 2.5 Flash"
    review_duration_ms: Optional[int] = None
    base_commit_sha: Optional[str] = None
    head_commit_sha: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    pr_title: Optional[str] = None

class ReviewDetailResponseSchema(ReviewResponseSchema):
    review_result: Optional[Dict[str, Any]] = None

class ReviewListResponseSchema(BaseModel):
    reviews: List[ReviewResponseSchema] = Field(default_factory=list)
    page: int = 1
    per_page: int = 20
    total_count: int = 0
