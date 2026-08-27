import asyncio
from unittest.mock import MagicMock, patch, call
import pytest
from fastapi import HTTPException

from src.services.review_service import ReviewService
from src.utils.security import encryption_service

@pytest.fixture
def mock_project_data():
    return {
        "id": "proj-uuid-123",
        "user_id": "user-uuid-456",
        "project_name": "Test Project",
        "github_owner": "test-owner",
        "github_repository": "test-repo",
        "default_branch": "main",
        "auth_type": "connected_account",
        "github_credential_id": "cred-uuid-789",
        "status": "READY"
    }

@pytest.fixture
def mock_credential_data():
    return {
        "id": "cred-uuid-789",
        "user_id": "user-uuid-456",
        "github_username": "testuser",
        "github_user_id": 12345,
        "github_avatar_url": "https://avatar.com/u/1",
        "encrypted_pat": encryption_service.encrypt("pat_test_123")
    }

@pytest.fixture
def mock_pr_data():
    return {
        "id": "pr-db-uuid-1",
        "project_id": "proj-uuid-123",
        "github_pr_number": 42,
        "title": "Add feature X",
        "description": "PR description",
        "author_username": "octocat",
        "author_avatar_url": "https://avatar.com/octocat",
        "source_branch": "feature/x",
        "target_branch": "main",
        "base_commit_sha": "base_sha_111",
        "head_commit_sha": "head_sha_222",
        "state": "OPEN",
        "github_url": "https://github.com/test-owner/test-repo/pull/42"
    }

@pytest.fixture
def mock_ai_review_output():
    return {
        "reviews": [
            {
                "filename": "src/api.py",
                "patch": "@@ -1 +1 @@",
                "original_code": "def old(): pass",
                "modified_code": "def new(): pass",
                "review": {
                    "summary": "Clean API implementation with minor error handling advice.",
                    "issues": [
                        {
                            "severity": "HIGH",
                            "category": "Security",
                            "title": "Missing validation",
                            "description": "Input is not sanitized.",
                            "suggestion": "Add Pydantic schema validation.",
                            "file": "src/api.py",
                            "line": 15
                        },
                        {
                            "severity": "LOW",
                            "category": "Style",
                            "title": "Trailing whitespace",
                            "description": "Clean up whitespace.",
                            "suggestion": "Remove trailing space.",
                            "file": "src/api.py",
                            "line": 20
                        }
                    ]
                },
                "retrieved_context": [
                    {
                        "page_content": "some context code",
                        "metadata": {"relative_path": "src/api.py"},
                        "rerank_score": 0.88,
                        "retrieval_source": "Hybrid"
                    }
                ]
            }
        ],
        "metadata": {
            "duration": 3.45,
            "llm": "Gemini 2.5 Flash",
            "chunks_retrieved": 1,
            "repository": "test-repo",
            "base_branch": "main",
            "head_branch": "feature/x",
            "confidence": 94
        }
    }


def test_connected_account_credential_id_resolution(mock_project_data, mock_credential_data):
    """1 & 2: Test connected_account resolves credential using project.github_credential_id"""
    service = ReviewService()
    mock_supabase = MagicMock()

    accessed_tables = []

    def table_side_effect(table_name):
        accessed_tables.append(table_name)
        t_mock = MagicMock()
        if table_name == "projects":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
        elif table_name == "github_credentials":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_credential_data])
        return t_mock

    mock_supabase.table.side_effect = table_side_effect

    with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase):
        proj, token = service._resolve_project_and_token("proj-uuid-123", "user-uuid-456", "jwt_token")
        assert proj["id"] == "proj-uuid-123"
        assert token == "pat_test_123"
        assert "github_credentials" in accessed_tables
        assert "github_accounts" not in accessed_tables


def test_fallback_credential_resolution_by_user_id(mock_project_data, mock_credential_data):
    """3: Test fallback credential resolution by user_id when github_credential_id is None"""
    service = ReviewService()
    project_without_cred_id = dict(mock_project_data)
    project_without_cred_id["github_credential_id"] = None

    mock_supabase = MagicMock()

    def table_side_effect(table_name):
        t_mock = MagicMock()
        if table_name == "projects":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[project_without_cred_id])
        elif table_name == "github_credentials":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_credential_data])
        return t_mock

    mock_supabase.table.side_effect = table_side_effect

    with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase):
        proj, token = service._resolve_project_and_token("proj-uuid-123", "user-uuid-456", "jwt_token")
        assert proj["id"] == "proj-uuid-123"
        assert token == "pat_test_123"


def test_custom_token_resolution():
    """4: Test custom_token resolution from project record"""
    service = ReviewService()
    custom_project = {
        "id": "proj-custom-1",
        "user_id": "user-uuid-456",
        "project_name": "Custom Token Project",
        "github_owner": "test-owner",
        "github_repository": "test-repo",
        "auth_type": "custom_token",
        "custom_token": encryption_service.encrypt("ghp_custom_token_abc")
    }

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[custom_project]
    )

    with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase):
        proj, token = service._resolve_project_and_token("proj-custom-1", "user-uuid-456", "jwt_token")
        assert proj["id"] == "proj-custom-1"
        assert token == "ghp_custom_token_abc"


def test_missing_credential_raises_clean_400(mock_project_data):
    """5: Test missing credential raises clean 400 instead of 500"""
    service = ReviewService()
    project_no_cred = dict(mock_project_data)
    project_no_cred["github_credential_id"] = None

    mock_supabase = MagicMock()

    def table_side_effect(table_name):
        t_mock = MagicMock()
        if table_name == "projects":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[project_no_cred])
        elif table_name == "github_credentials":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        return t_mock

    mock_supabase.table.side_effect = table_side_effect

    with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase):
        with pytest.raises(HTTPException) as exc:
            service._resolve_project_and_token("proj-uuid-123", "user-uuid-456", "jwt_token")
        assert exc.value.status_code == 400
        assert "No GitHub authentication token found" in exc.value.detail


def test_unauthorized_credential_user_mismatch_raises_403(mock_project_data, mock_credential_data):
    """6: Test that using another user's credential is blocked with 403"""
    service = ReviewService()
    other_user_credential = dict(mock_credential_data)
    other_user_credential["user_id"] = "victim-user-999"

    mock_supabase = MagicMock()

    def table_side_effect(table_name):
        t_mock = MagicMock()
        if table_name == "projects":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
        elif table_name == "github_credentials":
            t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[other_user_credential])
        return t_mock

    mock_supabase.table.side_effect = table_side_effect

    with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase):
        with pytest.raises(HTTPException) as exc:
            service._resolve_project_and_token("proj-uuid-123", "user-uuid-456", "jwt_token")
        assert exc.value.status_code == 403
        assert "permission" in exc.value.detail.lower()


def test_unauthorized_project_access_raises_403(mock_project_data):
    """6: Test that accessing another user's project is blocked with 403"""
    service = ReviewService()
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[mock_project_data]  # belongs to user-uuid-456
    )

    with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase):
        with pytest.raises(HTTPException) as exc:
            service._resolve_project_and_token("proj-uuid-123", "attacker-user-000", "jwt_token")
        assert exc.value.status_code == 403


def test_create_and_execute_review_lifecycle_and_persistence(
    mock_project_data, mock_credential_data, mock_pr_data, mock_ai_review_output
):
    """7, 8, 9, 11, 12, 13: Full execution lifecycle test:
       - Initial record created as RUNNING
       - PRReviewer is invoked with token and repo coordinates
       - Review updated to COMPLETED with persisted review_result
       - No calls to github_accounts or pull_requests.last_reviewed_at
    """
    async def run():
        service = ReviewService()
        mock_supabase = MagicMock()

        table_calls = []
        review_inserted = []
        review_updated = []
        pr_updates = []

        reviews_mock = MagicMock()
        def insert_review(data):
            review_inserted.append(data)
            return MagicMock(execute=MagicMock(return_value=MagicMock(data=[{"id": "rev-uuid-001"}])))
        reviews_mock.insert.side_effect = insert_review

        def update_review(data):
            review_updated.append(data)
            u_mock = MagicMock()
            u_mock.eq.return_value.execute.return_value = MagicMock(data=[])
            return u_mock
        reviews_mock.update.side_effect = update_review

        pr_mock = MagicMock()
        pr_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[mock_pr_data]
        )
        def update_pr(data):
            pr_updates.append(data)
            u_mock = MagicMock()
            u_mock.eq.return_value.execute.return_value = MagicMock(data=[])
            return u_mock
        pr_mock.update.side_effect = update_pr

        def table_side_effect(table_name):
            table_calls.append(table_name)
            if table_name == "projects":
                t_mock = MagicMock()
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
                return t_mock
            elif table_name == "github_credentials":
                t_mock = MagicMock()
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_credential_data])
                return t_mock
            elif table_name == "pull_requests":
                return pr_mock
            elif table_name == "reviews":
                return reviews_mock
            return MagicMock()

        mock_supabase.table.side_effect = table_side_effect

        with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase), \
             patch("src.services.review_service.PRReviewer") as mock_reviewer_cls:

            mock_reviewer_instance = MagicMock()
            mock_reviewer_instance.review.return_value = mock_ai_review_output
            mock_reviewer_cls.return_value = mock_reviewer_instance

            result = await service.create_and_execute_review(
                project_id="proj-uuid-123",
                pr_number=42,
                user_id="user-uuid-456",
                user_token="user_jwt_token"
            )

            # 7: Initial review record created with RUNNING
            assert len(review_inserted) == 1
            assert review_inserted[0]["status"] == "RUNNING"
            assert review_inserted[0]["github_pr_number"] == 42
            assert review_inserted[0]["base_commit_sha"] == "base_sha_111"
            assert review_inserted[0]["head_commit_sha"] == "head_sha_222"

            # 8: PRReviewer is actually invoked
            mock_reviewer_cls.assert_called_once_with(github_token="pat_test_123")
            mock_reviewer_instance.review.assert_called_once_with(
                repo_url="https://github.com/test-owner/test-repo",
                owner="test-owner",
                repository="test-repo",
                pull_number=42
            )

            # 9 & 11: Successful review -> COMPLETED with review_result persisted
            assert result["id"] == "rev-uuid-001"
            assert result["status"] == "COMPLETED"
            assert result["issues_count"] == 2
            assert result["high_count"] == 1
            assert result["low_count"] == 1
            assert result["files_reviewed"] == 1
            assert result["pr_title"] == "Add feature X"
            assert "Clean API implementation" in result["summary"]
            assert len(result["review_result"]["reviews"]) == 1

            assert len(review_updated) == 1
            assert review_updated[0]["status"] == "COMPLETED"
            assert "reviews" in review_updated[0]["review_result"]

            # 12: No use of nonexistent github_accounts
            assert "github_accounts" not in table_calls
            assert "github_credentials" in table_calls

            # 13: No use of nonexistent pull_requests.last_reviewed_at
            assert len(pr_updates) == 0, f"Unexpected pull_requests updates: {pr_updates}"

    asyncio.run(run())


def test_review_failure_sets_failed_status(mock_project_data, mock_credential_data, mock_pr_data):
    """10: Failed review execution updates status to FAILED"""
    async def run():
        service = ReviewService()
        mock_supabase = MagicMock()
        review_updates = []

        reviews_mock = MagicMock()
        reviews_mock.insert.return_value.execute.return_value = MagicMock(data=[{"id": "rev-uuid-failed"}])
        def update_review(data):
            review_updates.append(data)
            u_mock = MagicMock()
            u_mock.eq.return_value.execute.return_value = MagicMock(data=[])
            return u_mock
        reviews_mock.update.side_effect = update_review

        def table_side_effect(table_name):
            if table_name == "projects":
                t_mock = MagicMock()
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
                return t_mock
            elif table_name == "github_credentials":
                t_mock = MagicMock()
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_credential_data])
                return t_mock
            elif table_name == "pull_requests":
                t_mock = MagicMock()
                t_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_pr_data])
                return t_mock
            elif table_name == "reviews":
                return reviews_mock
            return MagicMock()

        mock_supabase.table.side_effect = table_side_effect

        with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase), \
             patch("src.services.review_service.PRReviewer") as mock_reviewer_cls:

            mock_reviewer_instance = MagicMock()
            mock_reviewer_instance.review.side_effect = Exception("LLM connection timed out")
            mock_reviewer_cls.return_value = mock_reviewer_instance

            with pytest.raises(HTTPException) as exc:
                await service.create_and_execute_review(
                    project_id="proj-uuid-123",
                    pr_number=42,
                    user_id="user-uuid-456",
                    user_token="user_jwt_token"
                )

            assert exc.value.status_code == 500
            assert "Unable to complete AI analysis" in exc.value.detail
            assert len(review_updates) == 1
            assert review_updates[0]["status"] == "FAILED"
            assert "LLM connection timed out" in review_updates[0]["error_message"]

    asyncio.run(run())


def test_get_review_by_id_maps_author_username_and_github_url(mock_project_data, mock_ai_review_output):
    """Task 3: Test review detail maps author_username and github_url from pull_requests table"""
    async def run():
        service = ReviewService()
        mock_supabase = MagicMock()

        mock_review_record = {
            "id": "rev-uuid-detail",
            "project_id": "proj-uuid-123",
            "pull_request_id": "pr-db-uuid-1",
            "github_pr_number": 42,
            "status": "COMPLETED",
            "summary": "Clean code",
            "review_result": mock_ai_review_output,
            "issues_count": 2,
            "high_count": 1,
            "created_at": "2026-08-26T22:00:00Z"
        }

        mock_pr_record = {
            "id": "pr-db-uuid-1",
            "title": "PR Title X",
            "source_branch": "feat/x",
            "target_branch": "main",
            "author_username": "octocat",
            "github_url": "https://github.com/test-owner/test-repo/pull/42"
        }

        def table_side_effect(table_name):
            t_mock = MagicMock()
            if table_name == "projects":
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
            elif table_name == "reviews":
                t_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_review_record])
            elif table_name == "pull_requests":
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[mock_pr_record]
                )
            return t_mock

        mock_supabase.table.side_effect = table_side_effect

        with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase), \
             patch.object(service, "_resolve_project_and_token", return_value=(mock_project_data, "token_123")):

            review = await service.get_review_by_id(
                project_id="proj-uuid-123",
                review_id="rev-uuid-detail",
                user_id="user-uuid-456",
                user_token="user_jwt_token"
            )

            assert review["id"] == "rev-uuid-detail"
            assert review["status"] == "COMPLETED"
            assert review["pr_title"] == "PR Title X"
            assert review["pr_author"] == "octocat"
            assert review["pr_html_url"] == "https://github.com/test-owner/test-repo/pull/42"
            assert "reviews" in review["review_result"]

    asyncio.run(run())


def test_list_project_reviews_with_filters_and_pagination(mock_project_data):
    """Test listing project reviews with status filter, pagination, and PR title mapping"""
    async def run():
        service = ReviewService()
        mock_supabase = MagicMock()

        mock_reviews = [
            {
                "id": "rev-1",
                "project_id": "proj-uuid-123",
                "pull_request_id": "pr-1",
                "github_pr_number": 10,
                "status": "COMPLETED",
                "summary": "Summary 1",
                "issues_count": 3,
                "created_at": "2026-08-26T20:00:00Z"
            },
            {
                "id": "rev-2",
                "project_id": "proj-uuid-123",
                "pull_request_id": "pr-1",
                "github_pr_number": 10,
                "status": "COMPLETED",
                "summary": "Summary 2",
                "issues_count": 0,
                "created_at": "2026-08-26T21:00:00Z"
            }
        ]

        query_mock = MagicMock()
        query_mock.eq.return_value = query_mock
        query_mock.ilike.return_value = query_mock
        query_mock.order.return_value = query_mock
        query_mock.range.return_value = query_mock
        query_mock.execute.return_value = MagicMock(data=mock_reviews, count=2)

        def table_side_effect(table_name):
            t_mock = MagicMock()
            if table_name == "projects":
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
            elif table_name == "reviews":
                t_mock.select.return_value = query_mock
            elif table_name == "pull_requests":
                t_mock.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[{"id": "pr-1", "title": "PR Title"}])
            return t_mock

        mock_supabase.table.side_effect = table_side_effect

        with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase), \
             patch.object(service, "_resolve_project_and_token", return_value=(mock_project_data, "token_123")):

            result = await service.list_project_reviews(
                project_id="proj-uuid-123",
                user_id="user-uuid-456",
                user_token="user_jwt_token",
                status_filter="COMPLETED",
                page=1,
                per_page=10
            )

            assert len(result["reviews"]) == 2
            assert result["total_count"] == 2
            assert result["page"] == 1
            assert result["per_page"] == 10
            assert result["reviews"][0]["pr_title"] == "PR Title"

    asyncio.run(run())


def test_get_pull_request_reviews(mock_project_data):
    """Test getting review history for a specific pull request"""
    async def run():
        service = ReviewService()
        mock_supabase = MagicMock()

        mock_reviews = [
            {
                "id": "rev-pr-1",
                "project_id": "proj-uuid-123",
                "pull_request_id": "pr-1",
                "github_pr_number": 42,
                "status": "COMPLETED",
                "summary": "First review",
                "created_at": "2026-08-26T20:00:00Z"
            }
        ]

        query_mock = MagicMock()
        query_mock.select.return_value = query_mock
        query_mock.eq.return_value = query_mock
        query_mock.order.return_value = query_mock
        query_mock.execute.return_value = MagicMock(data=mock_reviews)

        def table_side_effect(table_name):
            t_mock = MagicMock()
            if table_name == "projects":
                t_mock.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_project_data])
            elif table_name == "reviews":
                return query_mock
            return t_mock

        mock_supabase.table.side_effect = table_side_effect

        with patch("src.services.review_service.get_supabase_client", return_value=mock_supabase), \
             patch.object(service, "_resolve_project_and_token", return_value=(mock_project_data, "token_123")):

            reviews = await service.get_pull_request_reviews(
                project_id="proj-uuid-123",
                pr_number=42,
                user_id="user-uuid-456",
                user_token="user_jwt_token"
            )

            assert len(reviews) == 1
            assert reviews[0]["id"] == "rev-pr-1"
            assert reviews[0]["github_pr_number"] == 42

    asyncio.run(run())
