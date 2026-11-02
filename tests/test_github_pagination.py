from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.github.github_client import GitHubClient
from src.services.pull_request_service import PullRequestService
from src.services.pull_request_sync_service import PullRequestSyncService


def test_list_all_pull_requests_fetches_each_github_page():
    client = GitHubClient()
    first_page = [{"number": number} for number in range(1, 101)]
    second_page = [{"number": 101}, {"number": 102}]

    with patch.object(client, "list_pull_requests", side_effect=[first_page, second_page]) as fetch_page:
        all_pull_requests = client.list_all_pull_requests(
            owner="acme",
            repository="service",
            state="all",
        )

    assert len(all_pull_requests) == 102
    assert [call.kwargs["page"] for call in fetch_page.call_args_list] == [1, 2]
    assert all(call.kwargs["per_page"] == 100 for call in fetch_page.call_args_list)


def test_pull_request_files_fetches_all_file_pages():
    client = GitHubClient()
    first_page = [{"filename": f"file-{number}.py"} for number in range(100)]
    second_page = [{"filename": "last-file.py"}]
    first_response = MagicMock(status_code=200)
    first_response.json.return_value = first_page
    second_response = MagicMock(status_code=200)
    second_response.json.return_value = second_page
    client.session = MagicMock()
    client.session.get.side_effect = [first_response, second_response]

    files = client.get_pull_request_files("acme", "service", 17)

    assert len(files) == 101
    assert [call.kwargs["params"]["page"] for call in client.session.get.call_args_list] == [1, 2]
    assert all(call.kwargs["params"]["per_page"] == 100 for call in client.session.get.call_args_list)


def test_full_pr_sync_uses_all_pages():
    service = PullRequestSyncService()
    all_pull_requests = [{"number": number} for number in range(1, 103)]
    github_client = MagicMock()
    github_client.list_all_pull_requests.return_value = all_pull_requests

    with patch.object(service, "_resolve_token_and_project", return_value=(
        {"github_owner": "acme", "github_repository": "service"}, "token"
    )), patch("src.services.pull_request_sync_service.GitHubClient", return_value=github_client), \
         patch.object(service, "upsert_pull_request_record", return_value={}) as upsert:
        synced_count = service.sync_project_pull_requests("project-1")

    assert synced_count == 102
    github_client.list_all_pull_requests.assert_called_once_with(
        owner="acme",
        repository="service",
        state="all",
    )
    assert upsert.call_count == 102


def test_merged_filter_searches_beyond_first_github_page():
    service = PullRequestService()
    github_records = [
        {
            "number": number,
            "title": f"PR {number}",
            "state": "closed",
            "draft": False,
            "user": {"login": "octocat"},
            "head": {"ref": "feature", "sha": f"head-{number}"},
            "base": {"ref": "main", "sha": f"base-{number}"},
            "closed_at": "2026-01-01T00:00:00Z",
            "merged_at": None,
        }
        for number in range(1, 101)
    ]
    github_records.append({
        "number": 101,
        "title": "Merged after the first page",
        "state": "closed",
        "draft": False,
        "user": {"login": "octocat"},
        "head": {"ref": "feature", "sha": "head-101"},
        "base": {"ref": "main", "sha": "base-101"},
        "closed_at": "2026-01-01T00:00:00Z",
        "merged_at": "2026-01-01T00:00:00Z",
    })

    query = MagicMock()
    query.eq.return_value = query
    query.order.return_value = query
    query.range.return_value = query
    query.execute.return_value = SimpleNamespace(data=[], count=0)
    supabase = MagicMock()
    supabase.table.return_value.select.return_value = query
    github_client = MagicMock()
    github_client.list_all_pull_requests.return_value = github_records

    with patch.object(service, "_resolve_project_and_token", return_value=(
        {"github_owner": "acme", "github_repository": "service"}, "token"
    )), patch("src.services.pull_request_service.get_supabase_client", return_value=supabase), \
         patch("src.services.pull_request_service.GitHubClient", return_value=github_client):
        result = service.get_pull_requests(
            project_id="project-1",
            user_id="user-1",
            user_token="jwt",
            state="merged",
            page=1,
            per_page=20,
        )

    assert result["total_count"] == 1
    assert len(result["pull_requests"]) == 1
    assert result["pull_requests"][0].number == 101


def test_cached_pr_search_filter_is_applied_before_database_pagination():
    service = PullRequestService()
    project = {"github_owner": "acme", "github_repository": "service"}
    matching_pr = {
        "github_pr_number": 42,
        "title": "Fix authentication",
        "state": "OPEN",
        "draft": False,
        "author_login": "octocat",
        "source_branch": "fix/authentication",
        "target_branch": "main",
    }
    query = MagicMock()
    query.eq.return_value = query
    query.in_.return_value = query
    query.or_.return_value = query
    query.order.return_value = query
    query.range.return_value = query
    query.execute.return_value = SimpleNamespace(data=[matching_pr], count=1)
    supabase = MagicMock()
    supabase.table.return_value.select.return_value = query

    with patch.object(service, "_resolve_project_and_token", return_value=(project, "token")), \
         patch("src.services.pull_request_service.get_supabase_client", return_value=supabase), \
         patch("src.services.pull_request_service.GitHubClient") as github_client:
        result = service.get_pull_requests(
            project_id="project-1",
            user_id="user-1",
            user_token="jwt",
            search="#42",
            page=1,
            per_page=1,
        )

    assert result["total_count"] == 1
    assert result["pull_requests"][0].number == 42
    query.or_.assert_called_once()
    assert "github_pr_number.eq.42" in query.or_.call_args.args[0]
    query.range.assert_called_once_with(0, 0)
    github_client.assert_not_called()
