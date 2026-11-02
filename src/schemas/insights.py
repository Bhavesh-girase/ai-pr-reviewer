from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class DateRangeEnum(str, Enum):
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    ALL_TIME = "all"

class InsightsOverviewSchema(BaseModel):
    total_pull_requests: int = 0
    open_pull_requests: int = 0
    merged_pull_requests: int = 0
    closed_pull_requests: int = 0
    total_reviews: int = 0
    completed_reviews: int = 0
    failed_reviews: int = 0
    total_issues_detected: int = 0
    avg_review_duration_ms: Optional[int] = 0

class ReviewActivityPointSchema(BaseModel):
    date: str
    total_reviews: int = 0
    completed_reviews: int = 0
    failed_reviews: int = 0

class SeverityDistributionSchema(BaseModel):
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_issues: int = 0

class SeverityTrendPointSchema(BaseModel):
    date: str
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

class IssueCategoryPointSchema(BaseModel):
    category: str
    count: int = 0
    percentage: float = 0.0

class ProblematicFileSchema(BaseModel):
    filename: str
    total_issues: int = 0
    high_critical_count: int = 0
    review_count: int = 0

class PullRequestStatisticsSchema(BaseModel):
    total_prs: int = 0
    open_prs: int = 0
    merged_prs: int = 0
    closed_prs: int = 0
    draft_prs: int = 0
    avg_changed_files: float = 0.0
    avg_additions: float = 0.0
    avg_deletions: float = 0.0

class ReviewPerformanceSchema(BaseModel):
    avg_duration_ms: Optional[int] = 0
    fastest_duration_ms: Optional[int] = None
    slowest_duration_ms: Optional[int] = None
    completed_reviews: int = 0
    failed_reviews: int = 0
    total_reviews: int = 0
    success_rate: float = 0.0

class RepositoryHealthSchema(BaseModel):
    status: str = "Strong"  # "Strong", "Good", "Needs Attention"
    summary_text: str = ""
    critical_issues_recent: int = 0
    high_issues_recent: int = 0
    failure_rate_percentage: float = 0.0
    sync_status: str = "READY"
    last_synced_at: Optional[str] = None
    factors: List[str] = Field(default_factory=list)

class LatestReviewSummarySchema(BaseModel):
    id: str
    github_pr_number: int
    pr_title: Optional[str] = None
    status: str
    issues_count: int = 0
    high_count: int = 0
    critical_count: int = 0
    head_commit_sha: Optional[str] = None
    created_at: Optional[str] = None

class LatestPullRequestSummarySchema(BaseModel):
    github_pr_number: int
    title: str
    state: str
    author_login: str
    changed_files_count: int = 0
    updated_at: Optional[str] = None

class InsightsResponseSchema(BaseModel):
    project_id: str
    date_range: DateRangeEnum
    overview: InsightsOverviewSchema
    review_activity: List[ReviewActivityPointSchema] = Field(default_factory=list)
    severity_distribution: SeverityDistributionSchema
    severity_trends: List[SeverityTrendPointSchema] = Field(default_factory=list)
    issue_categories: List[IssueCategoryPointSchema] = Field(default_factory=list)
    problematic_files: List[ProblematicFileSchema] = Field(default_factory=list)
    pull_request_statistics: PullRequestStatisticsSchema
    review_performance: ReviewPerformanceSchema
    repository_health: RepositoryHealthSchema
    latest_reviews: List[LatestReviewSummarySchema] = Field(default_factory=list)
    latest_pull_requests: List[LatestPullRequestSummarySchema] = Field(default_factory=list)
    has_data: bool = False
