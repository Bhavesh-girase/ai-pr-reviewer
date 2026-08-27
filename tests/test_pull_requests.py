import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from src.services.pull_request_service import PullRequestService
from src.github.github_client import GitHubClient

@pytest.fixture
def mock_project():
    return {
        "id": "proj-1234-uuid",
        "user_id": "user-5678-uuid",
        "project_name": "Test Repository",
        "github_owner": "test-owner",
        "github_repository": "test-repo",
        "default_branch": "main",
        "auth_type": "connected_account",
        "status": "READY"
    }

@pytest.fixture
def mock_pr_list_data():
    return [
        {
            "number": 101,
            "title": "feat: add authentication support",
            "state": "open",
            "draft": False,
            "user": {
                "login": "alice",
                "avatar_url": "https://avatars.githubusercontent.com/u/101",
                "html_url": "https://github.com/alice"
            },
            "created_at": "2026-08-25T10:00:00Z",
            "updated_at": "2026-08-26T12:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "head": {"ref": "feature/auth", "sha": "headsha101"},
            "base": {"ref": "main", "sha": "basesha101"},
            "html_url": "https://github.com/test-owner/test-repo/pull/101",
            "additions": 120,
            "deletions": 15,
            "changed_files": 4,
            "comments": 2,
            "commits": 3,
        },
        {
            "number": 102,
            "title": "fix: resolve memory leak in worker",
            "state": "closed",
            "draft": False,
            "user": {
                "login": "bob",
                "avatar_url": "https://avatars.githubusercontent.com/u/102",
                "html_url": "https://github.com/bob"
            },
            "created_at": "2026-08-20T10:00:00Z",
            "updated_at": "2026-08-21T12:00:00Z",
            "closed_at": "2026-08-21T12:00:00Z",
            "merged_at": "2026-08-21T12:00:00Z",
            "head": {"ref": "bugfix/leak", "sha": "headsha102"},
            "base": {"ref": "main", "sha": "basesha102"},
            "html_url": "https://github.com/test-owner/test-repo/pull/102",
            "additions": 10,
            "deletions": 4,
            "changed_files": 1,
            "comments": 5,
            "commits": 1,
        },
        {
            "number": 103,
            "title": "draft: experimental cache engine",
            "state": "open",
            "draft": True,
            "user": {
                "login": "charlie",
                "avatar_url": "https://avatars.githubusercontent.com/u/103",
                "html_url": "https://github.com/charlie"
            },
            "created_at": "2026-08-26T08:00:00Z",
            "updated_at": "2026-08-26T09:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "head": {"ref": "experiment/cache", "sha": "headsha103"},
            "base": {"ref": "main", "sha": "basesha103"},
            "html_url": "https://github.com/test-owner/test-repo/pull/103",
            "additions": 450,
            "deletions": 80,
            "changed_files": 8,
            "comments": 0,
            "commits": 6,
        }
    ]

def test_list_pull_requests_open_filter(mock_project, mock_pr_list_data):
    service = PullRequestService()
    
    with patch.object(service, "_resolve_project_and_token", return_value=(mock_project, "ghp_mock_token")):
        with patch.object(GitHubClient, "list_pull_requests", return_value=mock_pr_list_data):
            result = service.get_pull_requests(
                project_id="proj-1234-uuid",
                user_id="user-5678-uuid",
                user_token="user_jwt_token",
                state="open"
            )
            
            assert "pull_requests" in result
            prs = result["pull_requests"]
            # Open filter returns open and draft
            assert len(prs) == 2
            assert prs[0].number == 101
            assert prs[0].state == "OPEN"
            assert prs[0].author.login == "alice"
            assert prs[1].number == 103
            assert prs[1].state == "DRAFT"

def test_list_pull_requests_merged_filter(mock_project, mock_pr_list_data):
    service = PullRequestService()
    
    with patch.object(service, "_resolve_project_and_token", return_value=(mock_project, "ghp_mock_token")):
        with patch.object(GitHubClient, "list_pull_requests", return_value=mock_pr_list_data):
            result = service.get_pull_requests(
                project_id="proj-1234-uuid",
                user_id="user-5678-uuid",
                user_token="user_jwt_token",
                state="merged"
            )
            
            prs = result["pull_requests"]
            assert len(prs) == 1
            assert prs[0].number == 102
            assert prs[0].state == "MERGED"

def test_list_pull_requests_search(mock_project, mock_pr_list_data):
    service = PullRequestService()
    
    with patch.object(service, "_resolve_project_and_token", return_value=(mock_project, "ghp_mock_token")):
        with patch.object(GitHubClient, "list_pull_requests", return_value=mock_pr_list_data):
            result = service.get_pull_requests(
                project_id="proj-1234-uuid",
                user_id="user-5678-uuid",
                user_token="user_jwt_token",
                state="all",
                search="leak"
            )
            
            prs = result["pull_requests"]
            assert len(prs) == 1
            assert prs[0].number == 102
            assert "leak" in prs[0].title

def test_get_pull_request_detail(mock_project, mock_pr_list_data):
    service = PullRequestService()
    single_pr = dict(mock_pr_list_data[0])
    single_pr["body"] = "Detailed description of authentication feature."
    single_pr["mergeable"] = True

    with patch.object(service, "_resolve_project_and_token", return_value=(mock_project, "ghp_mock_token")):
        with patch.object(GitHubClient, "get_pull_request", return_value=single_pr):
            result = service.get_pull_request(
                project_id="proj-1234-uuid",
                pr_number=101,
                user_id="user-5678-uuid",
                user_token="user_jwt_token"
            )
            
            assert result["number"] == 101
            assert result["title"] == "feat: add authentication support"
            assert result["body"] == "Detailed description of authentication feature."
            assert result["source_branch"] == "feature/auth"
            assert result["target_branch"] == "main"
            assert result["mergeable"] is True

def test_get_pull_request_files(mock_project):
    service = PullRequestService()
    mock_files = [
        {
            "sha": "f1a2b3",
            "filename": "src/api/auth.py",
            "status": "modified",
            "additions": 45,
            "deletions": 10,
            "changes": 55,
            "patch": "@@ -1,5 +1,10 @@\n+import logging\n"
        }
    ]

    with patch.object(service, "_resolve_project_and_token", return_value=(mock_project, "ghp_mock_token")):
        with patch.object(GitHubClient, "get_pull_request_files", return_value=mock_files):
            result = service.get_pull_request_files(
                project_id="proj-1234-uuid",
                pr_number=101,
                user_id="user-5678-uuid",
                user_token="user_jwt_token"
            )
            
            assert len(result) == 1
            assert result[0]["filename"] == "src/api/auth.py"
            assert result[0]["additions"] == 45
            assert "+import logging" in result[0]["patch"]

def test_get_pull_request_diff(mock_project):
    service = PullRequestService()
    diff_text = "diff --git a/src/api/auth.py b/src/api/auth.py\n+import logging\n"
    mock_files = [{"additions": 10, "deletions": 2}]

    with patch.object(service, "_resolve_project_and_token", return_value=(mock_project, "ghp_mock_token")):
        with patch.object(GitHubClient, "get_pull_request_diff", return_value=diff_text):
            with patch.object(GitHubClient, "get_pull_request_files", return_value=mock_files):
                result = service.get_pull_request_diff(
                    project_id="proj-1234-uuid",
                    pr_number=101,
                    user_id="user-5678-uuid",
                    user_token="user_jwt_token"
                )
                
                assert result["raw_diff"] == diff_text
                assert result["additions"] == 10
                assert result["deletions"] == 2
                assert result["files_count"] == 1

def test_project_not_found_raises_404():
    service = PullRequestService()
    with patch("src.services.project_service.project_service.get_project_by_id", side_effect=HTTPException(status_code=404, detail="Project not found.")):
        with pytest.raises(HTTPException) as exc_info:
            service.get_pull_requests(
                project_id="non-existent",
                user_id="user-123",
                user_token="jwt-123"
            )
        assert exc_info.value.status_code == 404
