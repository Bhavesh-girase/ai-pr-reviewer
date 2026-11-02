import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

from src.services.insights_service import INSIGHTS_PAGE_SIZE, InsightsService, _iter_project_rows
from src.schemas.insights import InsightsResponseSchema

@pytest.fixture
def mock_project_data():
    return {
        "id": "proj-uuid-123",
        "user_id": "user-uuid-456",
        "project_name": "Test Project",
        "github_owner": "test-owner",
        "github_repository": "test-repo",
        "default_branch": "main",
        "sync_status": "READY",
        "last_synced_at": "2026-08-26T20:00:00Z",
        "status": "READY"
    }

@pytest.fixture
def mock_prs():
    return [
        {
            "id": "pr-1",
            "project_id": "proj-uuid-123",
            "github_pr_number": 1,
            "title": "Feature 1",
            "state": "MERGED",
            "is_draft": False,
            "additions": 100,
            "deletions": 20,
            "changed_files_count": 3,
            "created_at": "2026-08-20T10:00:00Z"
        },
        {
            "id": "pr-2",
            "project_id": "proj-uuid-123",
            "github_pr_number": 2,
            "title": "Feature 2",
            "state": "OPEN",
            "is_draft": False,
            "additions": 50,
            "deletions": 10,
            "changed_files_count": 1,
            "created_at": "2026-08-25T10:00:00Z"
        }
    ]

@pytest.fixture
def mock_reviews():
    return [
        {
            "id": "rev-1",
            "project_id": "proj-uuid-123",
            "pull_request_id": "pr-1",
            "github_pr_number": 1,
            "status": "COMPLETED",
            "issues_count": 3,
            "critical_count": 0,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 0,
            "files_reviewed": 2,
            "review_duration_ms": 3500,
            "created_at": "2026-08-20T11:00:00Z",
            "review_result": {
                "reviews": [
                    {
                        "filename": "src/database.py",
                        "review": {
                            "issues": [
                                {"category": "Security", "severity": "HIGH", "title": "SQL Injection", "file": "src/database.py"},
                                {"category": "Performance", "severity": "MEDIUM", "title": "Slow Query", "file": "src/database.py"}
                            ]
                        }
                    },
                    {
                        "filename": "src/utils.py",
                        "review": {
                            "issues": [
                                {"category": "Maintainability", "severity": "MEDIUM", "title": "Complex function", "file": "src/utils.py"}
                            ]
                        }
                    }
                ]
            }
        },
        {
            "id": "rev-2",
            "project_id": "proj-uuid-123",
            "pull_request_id": "pr-2",
            "github_pr_number": 2,
            "status": "FAILED",
            "issues_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "files_reviewed": 0,
            "review_duration_ms": None,
            "created_at": "2026-08-25T12:00:00Z",
            "review_result": None
        }
    ]

def test_get_project_insights_aggregation(mock_project_data, mock_prs, mock_reviews):
    async def run():
        service = InsightsService()
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            t_mock = MagicMock()
            if table_name == "projects":
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
            elif table_name == "pull_requests":
                query = MagicMock()
                query.eq.return_value = query
                query.gte.return_value = query
                query.in_.return_value = query
                query.order.return_value = query
                query.range.return_value = query
                query.execute.return_value = MagicMock(data=mock_prs)
                t_mock.select.return_value.eq.return_value = query
            elif table_name == "reviews":
                query = MagicMock()
                query.eq.return_value = query
                query.gte.return_value = query
                query.order.return_value = query
                query.range.return_value = query
                query.execute.return_value = MagicMock(data=mock_reviews)
                t_mock.select.return_value.eq.return_value = query
            return t_mock

        mock_supabase.table.side_effect = table_side_effect

        with patch("src.services.insights_service.get_supabase_client", return_value=mock_supabase):
            insights = await service.get_project_insights(
                project_id="proj-uuid-123",
                user_id="user-uuid-456",
                user_token="user_token",
                range_str="30d"
            )

            assert insights["project_id"] == "proj-uuid-123"
            assert insights["date_range"] == "30d"
            InsightsResponseSchema.model_validate(insights)
            assert insights["overview"]["total_pull_requests"] == 2
            assert insights["overview"]["merged_pull_requests"] == 1
            assert insights["overview"]["open_pull_requests"] == 1
            assert insights["overview"]["total_reviews"] == 2
            assert insights["overview"]["completed_reviews"] == 1
            assert insights["overview"]["failed_reviews"] == 1
            assert insights["overview"]["total_issues_detected"] == 3

            # Check dynamic categories derived from JSONB
            categories = {c["category"]: c["count"] for c in insights["issue_categories"]}
            assert categories["Security"] == 1
            assert categories["Performance"] == 1
            assert categories["Maintainability"] == 1

            # Check problematic files
            top_file = insights["problematic_files"][0]
            assert top_file["filename"] == "src/database.py"
            assert top_file["total_issues"] == 2
            assert top_file["high_critical_count"] == 1

            # Check performance
            assert insights["review_performance"]["avg_duration_ms"] == 3500
            assert insights["review_performance"]["success_rate"] == 50.0

            # Check repository health
            assert insights["repository_health"]["status"] in ["Good", "Strong", "Needs Attention"]
            assert len(insights["repository_health"]["factors"]) > 0

    asyncio.run(run())

def test_empty_project_insights(mock_project_data):
    async def run():
        service = InsightsService()
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            t_mock = MagicMock()
            if table_name == "projects":
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
            elif table_name == "pull_requests":
                query = MagicMock()
                query.eq.return_value = query
                query.gte.return_value = query
                query.in_.return_value = query
                query.order.return_value = query
                query.range.return_value = query
                query.execute.return_value = MagicMock(data=[])
                t_mock.select.return_value.eq.return_value = query
            elif table_name == "reviews":
                query = MagicMock()
                query.eq.return_value = query
                query.gte.return_value = query
                query.order.return_value = query
                query.range.return_value = query
                query.execute.return_value = MagicMock(data=[])
                t_mock.select.return_value.eq.return_value = query
            return t_mock

        mock_supabase.table.side_effect = table_side_effect

        with patch("src.services.insights_service.get_supabase_client", return_value=mock_supabase):
            insights = await service.get_project_insights(
                project_id="proj-uuid-123",
                user_id="user-uuid-456",
                user_token="user_token",
                range_str="7d"
            )

            assert insights["overview"]["total_reviews"] == 0
            assert insights["overview"]["total_pull_requests"] == 0
            assert insights["has_data"] is False
            assert len(insights["issue_categories"]) == 0
            assert len(insights["problematic_files"]) == 0
            assert insights["review_performance"]["success_rate"] == 100.0

    asyncio.run(run())

def test_unauthorized_insights_access_rejected(mock_project_data):
    async def run():
        service = InsightsService()
        mock_supabase = MagicMock()

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[mock_project_data] # owned by user-uuid-456
        )

        with patch("src.services.insights_service.get_supabase_client", return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc:
                await service.get_project_insights(
                    project_id="proj-uuid-123",
                    user_id="stranger-user-999",
                    user_token="stranger_token"
                )
            assert exc.value.status_code == 403

    asyncio.run(run())


def test_insights_iterator_reads_beyond_postgrest_default_row_limit():
    rows = [{"id": f"review-{index}"} for index in range(INSIGHTS_PAGE_SIZE * 2 + 1)]
    query = MagicMock()
    query.eq.return_value = query
    query.order.return_value = query

    def set_page_range(start, end):
        query.execute.return_value = SimpleNamespace(data=rows[start:end + 1])
        return query

    query.range.side_effect = set_page_range
    supabase = MagicMock()
    supabase.table.return_value.select.return_value = query

    result_rows = list(_iter_project_rows(
        supabase=supabase,
        table_name="reviews",
        columns="id",
        project_id="project-1",
        cutoff_iso=None,
        order_by="created_at",
    ))

    assert len(result_rows) == len(rows)
    assert [call.args for call in query.range.call_args_list] == [
        (0, INSIGHTS_PAGE_SIZE - 1),
        (INSIGHTS_PAGE_SIZE, INSIGHTS_PAGE_SIZE * 2 - 1),
        (INSIGHTS_PAGE_SIZE * 2, INSIGHTS_PAGE_SIZE * 3 - 1),
    ]
