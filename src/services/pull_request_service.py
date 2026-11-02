import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status

from src.api.auth import get_supabase_client
from src.github.github_client import GitHubClient
from src.services.project_service import project_service
from src.services.github_credentials_service import github_credentials_service
from src.pr_reviewer import PRReviewer
from src.schemas.pull_request import (
    PullRequestListResponseSchema,
    PullRequestItemSchema,
    PullRequestDetailSchema,
    PullRequestAuthorSchema,
    PullRequestFileSchema,
    PullRequestDiffSchema,
)

logger = logging.getLogger(__name__)

class PullRequestService:
    """
    Dedicated business service managing Pull Requests for provisioned Projects.
    Uses Supabase PostgreSQL `public.pull_requests` as the primary local data source,
    seamlessly falling back to live GitHub REST API if synchronization has not occurred.
    """

    TABLE_NAME = "pull_requests"

    def _resolve_project_and_token(self, project_id: str, user_id: str, user_token: str) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Verifies project existence & user ownership via Supabase RLS,
        then resolves and decrypts the appropriate GitHub token.
        """
        project = project_service.get_project_by_id(project_id, user_id, user_token)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )

        token = github_credentials_service.resolve_project_token(
            project,
            user_id,
            user_token,
        )

        return project, token

    def get_pull_requests(
        self,
        project_id: str,
        user_id: str,
        user_token: str,
        state: str = "open",
        page: int = 1,
        per_page: int = 20,
        sort: str = "created",
        direction: str = "desc",
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves Pull Requests for the project. Checks the PostgreSQL database cache first;
        if empty, fetches live from GitHub REST API.
        """
        start_time = time.time()
        project, token = self._resolve_project_and_token(project_id, user_id, user_token)
        supabase = get_supabase_client(user_token)

        # Attempt to read from PostgreSQL database
        try:
            query = supabase.table(self.TABLE_NAME).select("*", count="exact").eq("project_id", project_id)

            state_lower = state.lower()
            if state_lower == "open":
                query = query.in_("state", ["OPEN", "DRAFT"])
            elif state_lower == "closed":
                query = query.eq("state", "CLOSED")
            elif state_lower == "merged":
                query = query.eq("state", "MERGED")
            elif state_lower == "draft":
                query = query.eq("draft", True)

            if search and search.strip():
                search_value = search.strip()
                escaped_search = (
                    search_value
                    .replace("\\", "\\\\")
                    .replace("%", r"\%")
                    .replace("_", r"\_")
                    .replace('"', '\\"')
                )
                pattern = f'"%{escaped_search}%"'
                search_filters = [
                    f"title.ilike.{pattern}",
                    f"author_login.ilike.{pattern}",
                    f"source_branch.ilike.{pattern}",
                    f"target_branch.ilike.{pattern}",
                ]
                number_query = search_value.removeprefix("#")
                if number_query.isdigit():
                    search_filters.append(f"github_pr_number.eq.{int(number_query)}")
                query = query.or_(",".join(search_filters))

            order_col = "updated_at" if sort == "updated" else "created_at"
            desc_order = (direction.lower() == "desc")
            query = query.order(order_col, desc=desc_order)

            # Pagination range in Supabase PostgREST is 0-indexed [start, end]
            start_range = (page - 1) * per_page
            end_range = start_range + per_page - 1
            query = query.range(start_range, end_range)

            db_res = query.execute()
            db_records = db_res.data or []
            total_db_count = db_res.count if db_res.count is not None else len(db_records)

            if total_db_count > 0 or db_records:
                items: List[PullRequestItemSchema] = []
                for rec in db_records:
                    if search and search.strip():
                        q = search.strip().lower()
                        num_m = str(rec["github_pr_number"]) == q.replace("#", "")
                        title_m = q in (rec.get("title") or "").lower()
                        author_name_db = rec.get("author_username") or rec.get("author_login") or ""
                        author_m = q in author_name_db.lower()
                        branch_m = q in (rec.get("source_branch") or "").lower() or q in (rec.get("target_branch") or "").lower()
                        if not (num_m or title_m or author_m or branch_m):
                            continue

                    author_name = rec.get("author_username") or rec.get("author_login") or "unknown"
                    author = PullRequestAuthorSchema(
                        login=author_name,
                        avatar_url=rec.get("author_avatar_url"),
                        html_url=f"https://github.com/{author_name}" if author_name != "unknown" else None,
                    )
                    item = PullRequestItemSchema(
                        number=rec["github_pr_number"],
                        title=rec.get("title", ""),
                        author=author,
                        state=rec.get("state", "OPEN"),
                        is_draft=bool(rec.get("draft", False)),
                        created_at=rec.get("created_at"),
                        updated_at=rec.get("updated_at"),
                        closed_at=rec.get("closed_at"),
                        merged_at=rec.get("merged_at"),
                        source_branch=rec.get("source_branch", ""),
                        target_branch=rec.get("target_branch", ""),
                        html_url=rec.get("github_url") or f"https://github.com/{project['github_owner']}/{project['github_repository']}/pull/{rec['github_pr_number']}",
                        additions=rec.get("additions", 0),
                        deletions=rec.get("deletions", 0),
                        changed_files_count=rec.get("changed_files_count", rec.get("changed_files", 0)),
                        comments_count=rec.get("comments_count", 0),
                        commits_count=rec.get("commits_count", 0),
                        review_status="PENDING",
                    )
                    items.append(item)

                duration = round(time.time() - start_time, 3)
                logger.info(f"Loaded {len(items)} PRs from PostgreSQL database for project {project_id} in {duration}s")
                return {
                    "pull_requests": items,
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_db_count,
                }

        except Exception as e:
            logger.debug(f"Database PR read skipped or empty, falling back to GitHub API: {str(e)}")

        # Fallback to GitHub REST API
        owner = project["github_owner"]
        repo = project["github_repository"]
        client = GitHubClient(token=token)

        state_lower = state.lower()
        gh_state = "all" if state_lower in ["all", "merged"] else ("closed" if state_lower == "closed" else "open")

        needs_client_side_filter = bool(search and search.strip()) or state_lower in ["merged", "draft"]
        if needs_client_side_filter:
            gh_prs = client.list_all_pull_requests(
                owner=owner,
                repository=repo,
                state=gh_state,
                sort=sort,
                direction=direction,
            )
        else:
            gh_prs = client.list_pull_requests(
                owner=owner,
                repository=repo,
                state=gh_state,
                page=page,
                per_page=per_page,
                sort=sort,
                direction=direction,
            )

        items = []
        for pr in gh_prs:
            is_draft = bool(pr.get("draft", False))
            merged_at = pr.get("merged_at")
            closed_at = pr.get("closed_at")

            if merged_at:
                pr_state = "MERGED"
            elif is_draft:
                pr_state = "DRAFT"
            elif closed_at or pr.get("state") == "closed":
                pr_state = "CLOSED"
            else:
                pr_state = "OPEN"

            if state_lower == "open" and pr_state not in ["OPEN", "DRAFT"]:
                continue
            elif state_lower == "closed" and pr_state != "CLOSED":
                continue
            elif state_lower == "merged" and pr_state != "MERGED":
                continue
            elif state_lower == "draft" and not is_draft:
                continue

            user_data = pr.get("user") or {}
            author = PullRequestAuthorSchema(
                login=user_data.get("login", "unknown"),
                avatar_url=user_data.get("avatar_url"),
                html_url=user_data.get("html_url"),
            )

            title = pr.get("title", "")
            source_branch = pr.get("head", {}).get("ref", "")
            target_branch = pr.get("base", {}).get("ref", "")
            pr_number = pr.get("number", 0)

            if search and search.strip():
                query_str = search.strip().lower()
                num_match = str(pr_number) == query_str.replace("#", "")
                title_match = query_str in title.lower()
                author_match = query_str in author.login.lower()
                branch_match = query_str in source_branch.lower() or query_str in target_branch.lower()
                if not (num_match or title_match or author_match or branch_match):
                    continue

            item = PullRequestItemSchema(
                number=pr_number,
                title=title,
                author=author,
                state=pr_state,
                is_draft=is_draft,
                created_at=pr.get("created_at"),
                updated_at=pr.get("updated_at"),
                closed_at=closed_at,
                merged_at=merged_at,
                source_branch=source_branch,
                target_branch=target_branch,
                html_url=pr.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pr_number}"),
                additions=pr.get("additions", 0),
                deletions=pr.get("deletions", 0),
                changed_files_count=pr.get("changed_files", 0),
                comments_count=pr.get("comments", 0),
                commits_count=pr.get("commits", 0),
                review_status="PENDING",
            )
            items.append(item)

        total_count = len(items)
        if search or state_lower in ["merged", "draft"]:
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_items = items[start_idx:end_idx]
        else:
            paginated_items = items

        duration = round(time.time() - start_time, 3)
        logger.info(f"Fetched {len(paginated_items)} PRs from GitHub REST API for project {project_id} in {duration}s")

        return {
            "pull_requests": paginated_items,
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
        }

    def get_pull_request(
        self,
        project_id: str,
        pr_number: int,
        user_id: str,
        user_token: str,
    ) -> Dict[str, Any]:
        """
        Fetches detailed metadata for a single pull request from GitHub.
        """
        project, token = self._resolve_project_and_token(project_id, user_id, user_token)
        owner = project["github_owner"]
        repo = project["github_repository"]

        client = GitHubClient(token=token)
        pr = client.get_pull_request(owner=owner, repository=repo, pull_number=pr_number)

        user_data = pr.get("user") or {}
        author = PullRequestAuthorSchema(
            login=user_data.get("login", "unknown"),
            avatar_url=user_data.get("avatar_url"),
            html_url=user_data.get("html_url"),
        )

        is_draft = bool(pr.get("draft", False))
        merged_at = pr.get("merged_at")
        closed_at = pr.get("closed_at")

        if merged_at:
            pr_state = "MERGED"
        elif is_draft:
            pr_state = "DRAFT"
        elif closed_at or pr.get("state") == "closed":
            pr_state = "CLOSED"
        else:
            pr_state = "OPEN"

        return {
            "number": pr.get("number", pr_number),
            "title": pr.get("title", ""),
            "body": pr.get("body"),
            "author": author,
            "state": pr_state,
            "is_draft": is_draft,
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "closed_at": closed_at,
            "merged_at": merged_at,
            "source_branch": pr.get("head", {}).get("ref", ""),
            "target_branch": pr.get("base", {}).get("ref", ""),
            "source_sha": pr.get("head", {}).get("sha"),
            "target_sha": pr.get("base", {}).get("sha"),
            "html_url": pr.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pr_number}"),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files_count": pr.get("changed_files", 0),
            "comments_count": pr.get("comments", 0),
            "commits_count": pr.get("commits", 0),
            "mergeable": pr.get("mergeable"),
        }

    def get_pull_request_files(
        self,
        project_id: str,
        pr_number: int,
        user_id: str,
        user_token: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetches all changed files with diff patches for a pull request from GitHub.
        """
        project, token = self._resolve_project_and_token(project_id, user_id, user_token)
        owner = project["github_owner"]
        repo = project["github_repository"]

        client = GitHubClient(token=token)
        files = client.get_pull_request_files(owner=owner, repository=repo, pull_number=pr_number)

        result = []
        for f in files:
            result.append({
                "sha": f.get("sha"),
                "filename": f.get("filename", ""),
                "status": f.get("status", "modified"),
                "additions": f.get("additions", 0),
                "deletions": f.get("deletions", 0),
                "changes": f.get("changes", 0),
                "patch": f.get("patch"),
                "raw_url": f.get("raw_url"),
                "contents_url": f.get("contents_url"),
                "previous_filename": f.get("previous_filename"),
            })
        return result

    def get_pull_request_diff(
        self,
        project_id: str,
        pr_number: int,
        user_id: str,
        user_token: str,
    ) -> Dict[str, Any]:
        """
        Fetches raw unified PR diff from GitHub.
        """
        project, token = self._resolve_project_and_token(project_id, user_id, user_token)
        owner = project["github_owner"]
        repo = project["github_repository"]

        client = GitHubClient(token=token)
        diff_text = client.get_pull_request_diff(owner=owner, repository=repo, pull_number=pr_number)

        files = client.get_pull_request_files(owner=owner, repository=repo, pull_number=pr_number)
        additions = sum(f.get("additions", 0) for f in files)
        deletions = sum(f.get("deletions", 0) for f in files)

        return {
            "raw_diff": diff_text,
            "files_count": len(files),
            "additions": additions,
            "deletions": deletions,
        }

    async def review_pull_request(
        self,
        project_id: str,
        pr_number: int,
        user_id: str,
        user_token: str,
    ) -> Dict[str, Any]:
        """
        Enqueues an AI review and returns its status record immediately.
        """
        from src.services.review_service import review_service
        return await review_service.enqueue_review(
            project_id=project_id,
            pr_number=pr_number,
            user_id=user_id,
            user_token=user_token
        )

pull_request_service = PullRequestService()
