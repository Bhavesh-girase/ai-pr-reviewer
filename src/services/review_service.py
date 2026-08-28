import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status

from src.api.auth import get_supabase_client
from src.pr_reviewer import PRReviewer
from src.services.pull_request_sync_service import pull_request_sync_service
from src.storage.project_storage import project_storage
from src.utils.security import encryption_service, sanitize_error_message

logger = logging.getLogger("review_service")

class ReviewService:
    """
    Manages the lifecycle, persistence, and querying of AI Code Reviews.
    Wraps the existing AI PR Review pipeline with immutable database snapshots.
    """

    def _resolve_project_and_token(
        self,
        project_id: str,
        user_id: str,
        user_token: str
    ) -> tuple[Dict[str, Any], str]:
        supabase = get_supabase_client(user_token)
        proj_res = supabase.table("projects").select("*").eq("id", project_id).execute()
        if not proj_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found or unauthorized."
            )
        project = proj_res.data[0]

        if project["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access reviews for this project."
            )

        auth_type = project.get("auth_type", "connected_account")
        token: Optional[str] = None

        if auth_type == "custom_token":
            encrypted_token = project.get("custom_token")
            if encrypted_token:
                try:
                    token = encryption_service.decrypt_or_passthrough(encrypted_token)
                except Exception as e:
                    logger.error(f"Failed to decrypt custom token for project {project_id}: {sanitize_error_message(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to decrypt project credentials."
                    )
        else:
            # connected_account
            github_credential_id = project.get("github_credential_id")
            encrypted_pat: Optional[str] = None

            # 1. Prefer project["github_credential_id"]
            if github_credential_id:
                try:
                    cred_res = (
                        supabase.table("github_credentials")
                        .select("id, user_id, encrypted_pat")
                        .eq("id", github_credential_id)
                        .execute()
                    )
                    if cred_res.data and len(cred_res.data) > 0:
                        cred = cred_res.data[0]
                        # 3. Verify the credential belongs to the same user_id
                        if cred.get("user_id") != user_id:
                            logger.warning(
                                f"Credential {github_credential_id} does not belong to user {user_id}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="You do not have permission to use this GitHub credential."
                            )
                        encrypted_pat = cred.get("encrypted_pat")
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error querying github_credentials by ID {github_credential_id}: {e}")

            # Safe backward-compatible fallback by querying github_credentials using user_id
            if not encrypted_pat:
                try:
                    cred_res = (
                        supabase.table("github_credentials")
                        .select("id, user_id, encrypted_pat")
                        .eq("user_id", user_id)
                        .execute()
                    )
                    if cred_res.data and len(cred_res.data) > 0:
                        cred = cred_res.data[0]
                        if cred.get("user_id") == user_id:
                            encrypted_pat = cred.get("encrypted_pat")
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error querying fallback github_credentials for user {user_id}: {e}")

            if encrypted_pat:
                try:
                    token = encryption_service.decrypt(encrypted_pat)
                except Exception as e:
                    logger.error(f"Failed to decrypt user GitHub PAT for user {user_id}: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to decrypt GitHub account credentials."
                    )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No GitHub authentication token found. Please connect your GitHub account or configure a custom token."
            )

        return project, token

    async def create_and_execute_review(
        self,
        project_id: str,
        pr_number: int,
        user_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        """
        Executes an AI review for a Pull Request and persists the immutable Review record.
        """
        supabase = get_supabase_client(user_token)
        project, token = self._resolve_project_and_token(project_id, user_id, user_token)

        owner = project["github_owner"]
        repo = project["github_repository"]
        repo_url = f"https://github.com/{owner}/{repo}"

        # 1. Resolve or synchronize the Pull Request database record
        pr_query = (
            supabase.table("pull_requests")
            .select("*")
            .eq("project_id", project_id)
            .eq("github_pr_number", pr_number)
            .execute()
        )

        pr_record = None
        if pr_query.data:
            pr_record = pr_query.data[0]
        else:
            # Sync single PR from GitHub if not yet cached in DB
            try:
                pr_record = pull_request_sync_service.sync_single_pull_request(
                    project_id=project_id,
                    pr_number=pr_number,
                    user_id=user_id,
                    user_token=user_token
                )
            except Exception as e:
                logger.warning(f"Could not pre-sync PR #{pr_number}: {e}")

        if not pr_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pull Request #{pr_number} not found for project '{project_id}'."
            )

        base_sha = pr_record.get("base_commit_sha") or pr_record.get("base_sha") or "unknown"
        head_sha = pr_record.get("head_commit_sha") or pr_record.get("head_sha") or "unknown"

        # 2. Insert initial Review record with status 'RUNNING'
        now_started = datetime.now(timezone.utc).isoformat()
        new_review = {
            "project_id": project_id,
            "pull_request_id": pr_record["id"],
            "github_pr_number": pr_number,
            "status": "RUNNING",
            "model_name": "Gemini 2.5 Flash",
            "base_commit_sha": base_sha,
            "head_commit_sha": head_sha,
            "created_by": user_id,
            "created_at": now_started,
        }

        insert_res = supabase.table("reviews").insert(new_review).execute()
        if not insert_res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize review record in database."
            )

        review_id = insert_res.data[0]["id"]
        logger.info(f"Initialized Review {review_id} (RUNNING) for PR #{pr_number} on Project {project_id}")

        # 3. Execute AI Review Pipeline
        start_time = time.time()
        try:
            repo_dir, _ = project_storage.ensure_project_directories(user_id, project_id)
            local_repo_path = Path(project.get("clone_path") or str(repo_dir))

            reviewer = PRReviewer(github_token=token)
            review_data = reviewer.review(
                repo_url=repo_url,
                owner=owner,
                repository=repo,
                pull_number=pr_number,
                local_path=local_repo_path
            )

            # 4. Extract structured metadata & calculate severity metrics
            all_issues: List[Dict[str, Any]] = []
            reviews_list = review_data.get("reviews", [])
            for r in reviews_list:
                file_review = r.get("review", {})
                if hasattr(file_review, "dict"):
                    file_review_dict = file_review.dict()
                elif isinstance(file_review, dict):
                    file_review_dict = file_review
                else:
                    file_review_dict = {}

                for iss in file_review_dict.get("issues", []):
                    if hasattr(iss, "dict"):
                        iss_dict = iss.dict()
                    elif isinstance(iss, dict):
                        iss_dict = iss
                    else:
                        continue
                    all_issues.append(iss_dict)

            critical_count = sum(1 for i in all_issues if i.get("severity") == "CRITICAL")
            high_count = sum(1 for i in all_issues if i.get("severity") == "HIGH")
            medium_count = sum(1 for i in all_issues if i.get("severity") == "MEDIUM")
            low_count = sum(1 for i in all_issues if i.get("severity") == "LOW")
            issues_count = len(all_issues)
            files_reviewed = len(reviews_list)

            # Calculate review duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Summary generation fallback
            summary = review_data.get("summary")
            if not summary:
                if reviews_list:
                    first_r = reviews_list[0].get("review", {})
                    if hasattr(first_r, "summary"):
                        summary = first_r.summary
                    elif isinstance(first_r, dict):
                        summary = first_r.get("summary", "")
            if not summary:
                summary = (
                    f"AI PR Review completed. Analyzed {files_reviewed} files with {issues_count} potential issues identified "
                    f"({critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low)."
                )

            base_sha = (
                pr_record.get("base_sha")
                or (pr_record.get("raw_data") or {}).get("base", {}).get("sha", "unknown")
            )
            head_sha = (
                pr_record.get("head_sha")
                or (pr_record.get("raw_data") or {}).get("head", {}).get("sha", "unknown")
            )

            # Clean serializable payload
            serializable_reviews = []
            for r in reviews_list:
                f_rev = r.get("review")
                if hasattr(f_rev, "dict"):
                    f_rev = f_rev.dict()
                serializable_reviews.append({
                    "filename": r.get("filename"),
                    "patch": r.get("patch", ""),
                    "original_code": r.get("original_code", ""),
                    "modified_code": r.get("modified_code", ""),
                    "review": f_rev,
                    "retrieved_context": r.get("retrieved_context", [])
                })

            final_review_payload = {
                "reviews": serializable_reviews,
                "metadata": review_data.get("metadata", {})
            }

            # 5. Persist COMPLETED review
            now_completed = datetime.now(timezone.utc).isoformat()
            update_data = {
                "status": "COMPLETED",
                "summary": summary,
                "review_result": final_review_payload,
                "issues_count": issues_count,
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count,
                "files_reviewed": files_reviewed,
                "review_duration_ms": duration_ms,
                "completed_at": now_completed,
                "error_message": None
            }

            supabase.table("reviews").update(update_data).eq("id", review_id).execute()

            logger.info(f"Review {review_id} COMPLETED for PR #{pr_number} ({issues_count} issues found)")

            # Return review response
            res_item = {
                "id": review_id,
                "project_id": project_id,
                "pull_request_id": pr_record["id"],
                "github_pr_number": pr_number,
                "status": "COMPLETED",
                "summary": summary,
                "review_result": final_review_payload,
                "issues_count": issues_count,
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count,
                "files_reviewed": files_reviewed,
                "lines_analyzed": 0,
                "model_name": "Gemini 2.5 Flash",
                "review_duration_ms": duration_ms,
                "base_commit_sha": base_sha,
                "head_commit_sha": head_sha,
                "created_by": user_id,
                "created_at": now_started,
                "completed_at": now_completed,
                "error_message": None,
                "pr_title": pr_record.get("title")
            }
            return res_item

        except Exception as e:
            sanitized_err = sanitize_error_message(str(e))
            logger.error(f"AI review execution failed for Review {review_id}: {sanitized_err}", exc_info=False)
            now_failed = datetime.now(timezone.utc).isoformat()
            safe_error = "Unable to complete AI analysis. " + sanitized_err
            try:
                supabase.table("reviews").update({
                    "status": "FAILED",
                    "error_message": safe_error,
                    "completed_at": now_failed
                }).eq("id", review_id).execute()
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=safe_error
            )

    async def list_project_reviews(
        self,
        project_id: str,
        user_id: str,
        user_token: str,
        pr_number: Optional[int] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort: str = "created_at",
        direction: str = "desc",
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lists paginated lightweight reviews belonging to a project.
        """
        supabase = get_supabase_client(user_token)
        self._resolve_project_and_token(project_id, user_id, user_token)

        # Build select query (without huge review_result JSON for list performance)
        columns = (
            "id, project_id, pull_request_id, github_pr_number, status, summary, "
            "issues_count, critical_count, high_count, medium_count, low_count, "
            "files_reviewed, lines_analyzed, model_name, review_duration_ms, "
            "base_commit_sha, head_commit_sha, created_by, created_at, completed_at, error_message"
        )
        query = supabase.table("reviews").select(columns, count="exact").eq("project_id", project_id)

        if pr_number:
            query = query.eq("github_pr_number", pr_number)

        if status_filter and status_filter.upper() != "ALL":
            query = query.eq("status", status_filter.upper())

        if search:
            query = query.ilike("summary", f"%{search}%")

        is_desc = direction.lower() == "desc"
        query = query.order(sort, desc=is_desc)

        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        result = query.execute()
        reviews = result.data or []
        total_count = result.count if result.count is not None else len(reviews)

        # Attach PR titles
        if reviews:
            pr_ids = list({r["pull_request_id"] for r in reviews if r.get("pull_request_id")})
            if pr_ids:
                pr_res = supabase.table("pull_requests").select("id, title").in_("id", pr_ids).execute()
                pr_map = {p["id"]: p.get("title") for p in pr_res.data or []}
                for r in reviews:
                    r["pr_title"] = pr_map.get(r.get("pull_request_id"))

        return {
            "reviews": reviews,
            "page": page,
            "per_page": per_page,
            "total_count": total_count
        }

    async def get_review_by_id(
        self,
        project_id: str,
        review_id: str,
        user_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        """
        Retrieves complete review details including full structured review_result JSONB.
        """
        supabase = get_supabase_client(user_token)
        self._resolve_project_and_token(project_id, user_id, user_token)

        res = supabase.table("reviews").select("*").eq("id", review_id).eq("project_id", project_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review '{review_id}' not found for project '{project_id}'."
            )

        review = res.data[0]

        # Attach PR metadata
        if review.get("pull_request_id"):
            pr_res = supabase.table("pull_requests").select("*").eq("id", review["pull_request_id"]).execute()
            if pr_res.data:
                pr = pr_res.data[0]
                review["pr_title"] = pr.get("title")
                review["pr_source_branch"] = pr.get("source_branch")
                review["pr_target_branch"] = pr.get("target_branch")
                review["pr_author"] = pr.get("author_username")
                review["pr_html_url"] = pr.get("github_url")

        return review

    async def get_pull_request_reviews(
        self,
        project_id: str,
        pr_number: int,
        user_id: str,
        user_token: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all historical reviews for a specific Pull Request, sorted newest first.
        """
        supabase = get_supabase_client(user_token)
        self._resolve_project_and_token(project_id, user_id, user_token)

        columns = (
            "id, project_id, pull_request_id, github_pr_number, status, summary, "
            "issues_count, critical_count, high_count, medium_count, low_count, "
            "files_reviewed, lines_analyzed, model_name, review_duration_ms, "
            "base_commit_sha, head_commit_sha, created_by, created_at, completed_at, error_message"
        )
        res = (
            supabase.table("reviews")
            .select(columns)
            .eq("project_id", project_id)
            .eq("github_pr_number", pr_number)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []

review_service = ReviewService()

