import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from src.api.auth import get_supabase_client
from src.github.github_client import GitHubClient
from src.services.github_credentials_service import github_credentials_service

logger = logging.getLogger(__name__)

class PullRequestSyncService:
    """
    Orchestrates authoritative Pull Request synchronization between GitHub REST API
    and the local Supabase PostgreSQL `public.pull_requests` table.
    """

    TABLE_NAME = "pull_requests"

    def _resolve_token_and_project(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Fetches project and resolves decrypted PAT.
        Works in both authenticated user context and server-side webhook context.
        """
        supabase = get_supabase_client(user_token)
        res = supabase.table("projects").select("*").eq("id", project_id).execute()
        if not res.data or len(res.data) == 0:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
        project = res.data[0]

        target_user_id = user_id or project["user_id"]
        token = github_credentials_service.resolve_project_token(
            project,
            target_user_id,
            user_token,
        )

        return project, token

    def upsert_pull_request_record(
        self,
        project_id: str,
        pr_data: Dict[str, Any],
        user_token: Optional[str] = None,
        from_webhook: bool = True
    ) -> Dict[str, Any]:
        """
        Performs an atomic UPSERT on public.pull_requests matching (project_id, github_pr_number).
        """
        pr_number = pr_data.get("number")
        if not pr_number:
            raise ValueError("PR data missing 'number' field")

        is_draft = bool(pr_data.get("draft", False))
        is_merged = bool(pr_data.get("merged", False) or pr_data.get("merged_at") is not None)
        closed_at = pr_data.get("closed_at")
        merged_at = pr_data.get("merged_at")

        if is_merged:
            state = "MERGED"
        elif is_draft:
            state = "DRAFT"
        elif closed_at or pr_data.get("state") == "closed":
            state = "CLOSED"
        else:
            state = "OPEN"

        author_data = pr_data.get("user") or {}
        now_iso = datetime.now(timezone.utc).isoformat()

        db_payload = {
            "project_id": project_id,
            "github_pr_number": pr_number,
            "github_pr_id": pr_data.get("id"),
            "title": pr_data.get("title", ""),
            "description": pr_data.get("body"),
            "state": state,
            "draft": is_draft,
            "merged": is_merged,
            "author_login": author_data.get("login", "unknown"),
            "author_avatar_url": author_data.get("avatar_url"),
            "source_branch": pr_data.get("head", {}).get("ref", ""),
            "target_branch": pr_data.get("base", {}).get("ref", ""),
            "head_sha": pr_data.get("head", {}).get("sha"),
            "base_sha": pr_data.get("base", {}).get("sha"),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "changed_files": pr_data.get("changed_files", 0),
            "comments_count": pr_data.get("comments", 0),
            "commits_count": pr_data.get("commits", 0),
            "github_url": pr_data.get("html_url"),
            "created_at": pr_data.get("created_at"),
            "updated_at": pr_data.get("updated_at"),
            "last_synced_at": now_iso,
            "created_from_webhook": from_webhook
        }

        supabase = get_supabase_client(user_token)

        try:
            # Check existing record
            existing = supabase.table(self.TABLE_NAME)\
                .select("id")\
                .eq("project_id", project_id)\
                .eq("github_pr_number", pr_number)\
                .execute()

            if existing.data and len(existing.data) > 0:
                record_id = existing.data[0]["id"]
                res = supabase.table(self.TABLE_NAME)\
                    .update(db_payload)\
                    .eq("id", record_id)\
                    .execute()
                return res.data[0] if res.data else db_payload
            else:
                res = supabase.table(self.TABLE_NAME)\
                    .insert(db_payload)\
                    .execute()
                return res.data[0] if res.data else db_payload

        except Exception as e:
            logger.error(f"Failed to upsert PR #{pr_number} for project {project_id}: {str(e)}")
            raise

    def sync_single_pull_request(
        self,
        project_id: str,
        pr_number: int,
        user_id: Optional[str] = None,
        user_token: Optional[str] = None,
        webhook_pr_data: Optional[Dict[str, Any]] = None,
        from_webhook: bool = True
    ) -> Dict[str, Any]:
        """
        Fetches authoritative PR details from GitHub API and upserts into database.
        """
        project, token = self._resolve_token_and_project(project_id, user_id, user_token)
        owner = project["github_owner"]
        repo = project["github_repository"]

        client = GitHubClient(token=token)
        try:
            authoritative_data = client.get_pull_request(owner=owner, repository=repo, pull_number=pr_number)
        except Exception as e:
            logger.warning(f"Could not fetch full GitHub API PR data for #{pr_number}, using webhook payload if present: {str(e)}")
            authoritative_data = webhook_pr_data or {"number": pr_number, "title": f"PR #{pr_number}"}

        return self.upsert_pull_request_record(
            project_id=project_id,
            pr_data=authoritative_data,
            user_token=user_token,
            from_webhook=from_webhook
        )

    def sync_project_pull_requests(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> int:
        """
        Performs full initial or manual PR synchronization for a project repository.
        Fetches all open and closed PRs from GitHub REST API and upserts them.
        """
        project, token = self._resolve_token_and_project(project_id, user_id, user_token)
        owner = project["github_owner"]
        repo = project["github_repository"]

        client = GitHubClient(token=token)
        logger.info(f"Initiating full PR sync for project {project_id} ({owner}/{repo})")

        # Fetch every page so repositories with more than 100 PRs have a
        # complete local cache for review history and analytics.
        prs = client.list_all_pull_requests(owner=owner, repository=repo, state="all")

        synced_count = 0
        for pr in prs:
            try:
                self.upsert_pull_request_record(
                    project_id=project_id,
                    pr_data=pr,
                    user_token=user_token,
                    from_webhook=False
                )
                synced_count += 1
            except Exception as e:
                logger.error(f"Error during bulk sync of PR #{pr.get('number')}: {str(e)}")

        logger.info(f"Successfully synced {synced_count} PRs for project {project_id}")
        return synced_count

pull_request_sync_service = PullRequestSyncService()
