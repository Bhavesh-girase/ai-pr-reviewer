import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from fastapi import HTTPException, status
from starlette.concurrency import run_in_threadpool

from src.api.auth import get_supabase_client

logger = logging.getLogger("insights_service")

INSIGHTS_PAGE_SIZE = 500


def _iter_project_rows(
    supabase,
    table_name: str,
    columns: str,
    project_id: str,
    cutoff_iso: Optional[str],
    *,
    status_filter: Optional[str] = None,
    order_by: Optional[str] = None,
):
    """Yield bounded pages so PostgREST's row cap cannot truncate analytics."""
    offset = 0
    while True:
        query = supabase.table(table_name).select(columns).eq("project_id", project_id)
        if cutoff_iso:
            query = query.gte("created_at", cutoff_iso)
        if status_filter:
            query = query.eq("status", status_filter)
        if order_by:
            query = query.order(order_by, desc=True).order("id", desc=True)

        result = query.range(offset, offset + INSIGHTS_PAGE_SIZE - 1).execute()
        rows = result.data or []
        yield from rows

        if len(rows) < INSIGHTS_PAGE_SIZE:
            return
        offset += INSIGHTS_PAGE_SIZE


class InsightsService:
    """
    Computes deterministic, project-scoped engineering analytics and code quality insights
    from persistent Pull Requests, Reviews, and Synchronization records.
    """

    def _resolve_project(
        self,
        project_id: str,
        user_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        supabase = get_supabase_client(user_token)
        proj_res = (
            supabase.table("projects")
            .select("id, user_id, sync_status, last_synced_at")
            .eq("id", project_id)
            .execute()
        )
        if not proj_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found or unauthorized."
            )
        project = proj_res.data[0]

        if project["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access insights for this project."
            )
        return project

    def _get_date_cutoff(self, range_str: str) -> Optional[datetime]:
        normalized = (range_str or "30d").lower()
        now = datetime.now(timezone.utc)
        if normalized == "7d":
            return now - timedelta(days=7)
        elif normalized == "30d":
            return now - timedelta(days=30)
        elif normalized == "90d":
            return now - timedelta(days=90)
        elif normalized == "all":
            return None
        return now - timedelta(days=30)

    async def get_project_insights(
        self,
        project_id: str,
        user_id: str,
        user_token: str,
        range_str: str = "30d"
    ) -> Dict[str, Any]:
        """Run synchronous database reads and analytics outside the event loop."""
        return await run_in_threadpool(
            self._get_project_insights_sync,
            project_id,
            user_id,
            user_token,
            range_str,
        )

    def _get_project_insights_sync(
        self,
        project_id: str,
        user_id: str,
        user_token: str,
        range_str: str = "30d"
    ) -> Dict[str, Any]:
        """
        Aggregates and returns comprehensive project insights for the specified date range.
        """
        supabase = get_supabase_client(user_token)
        project = self._resolve_project(project_id, user_id, user_token)
        range_str = str(getattr(range_str, "value", range_str)).lower()
        if range_str not in {"7d", "30d", "90d", "all"}:
            range_str = "30d"
        cutoff = self._get_date_cutoff(range_str)
        cutoff_iso = cutoff.isoformat() if cutoff else None

        # 1. Aggregate PR fields in bounded pages; avoid loading unused columns.
        total_prs = open_prs = merged_prs = closed_prs = draft_prs = 0
        changed_files_sum = additions_sum = deletions_sum = 0
        latest_pr_rows = []
        for pr in _iter_project_rows(
            supabase,
            "pull_requests",
            "id, github_pr_number, title, state, draft, additions, deletions, changed_files, created_at, updated_at, author_login",
            project_id,
            cutoff_iso,
            order_by="created_at",
        ):
            total_prs += 1
            state = pr.get("state")
            open_prs += state == "OPEN"
            merged_prs += state == "MERGED"
            closed_prs += state == "CLOSED"
            draft_prs += bool(pr.get("draft") or pr.get("is_draft") or state == "DRAFT")
            changed_files_sum += pr.get("changed_files_count") or pr.get("changed_files") or 0
            additions_sum += pr.get("additions") or 0
            deletions_sum += pr.get("deletions") or 0
            if len(latest_pr_rows) < 5:
                latest_pr_rows.append(pr)

        avg_changed_files = round(changed_files_sum / total_prs, 1) if total_prs else 0.0
        avg_additions = round(additions_sum / total_prs, 1) if total_prs else 0.0
        avg_deletions = round(deletions_sum / total_prs, 1) if total_prs else 0.0

        pr_stats = {
            "total_prs": total_prs,
            "open_prs": open_prs,
            "merged_prs": merged_prs,
            "closed_prs": closed_prs,
            "draft_prs": draft_prs,
            "avg_changed_files": avg_changed_files,
            "avg_additions": avg_additions,
            "avg_deletions": avg_deletions
        }

        # 2. Aggregate compact review rows in bounded pages. Large JSONB review
        # payloads are fetched separately and one page at a time below.
        review_columns = (
            "id, pull_request_id, github_pr_number, status, issues_count, "
            "critical_count, high_count, medium_count, low_count, "
            "review_duration_ms, created_at, head_commit_sha"
        )
        total_reviews = completed_count = failed_count = 0
        total_issues_detected = critical_count = high_count = medium_count = low_count = 0
        duration_sum = duration_count = 0
        fastest_duration_ms = slowest_duration_ms = None
        latest_review_rows = []
        activity_map = defaultdict(lambda: {"total": 0, "completed": 0, "failed": 0})
        trend_map = defaultdict(lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})

        for review in _iter_project_rows(
            supabase,
            "reviews",
            review_columns,
            project_id,
            cutoff_iso,
            order_by="created_at",
        ):
            total_reviews += 1
            if len(latest_review_rows) < 5:
                latest_review_rows.append(review)

            review_status = review.get("status")
            created_at = review.get("created_at")
            if created_at:
                date_key = str(created_at)[:10]
                activity_map[date_key]["total"] += 1

            if review_status == "COMPLETED":
                completed_count += 1
                total_issues_detected += review.get("issues_count") or 0
                critical_count += review.get("critical_count") or 0
                high_count += review.get("high_count") or 0
                medium_count += review.get("medium_count") or 0
                low_count += review.get("low_count") or 0
                if created_at:
                    activity_map[date_key]["completed"] += 1
                    trend_map[date_key]["critical"] += review.get("critical_count") or 0
                    trend_map[date_key]["high"] += review.get("high_count") or 0
                    trend_map[date_key]["medium"] += review.get("medium_count") or 0
                    trend_map[date_key]["low"] += review.get("low_count") or 0

                duration = review.get("review_duration_ms") or 0
                if duration > 0:
                    duration_sum += duration
                    duration_count += 1
                    fastest_duration_ms = duration if fastest_duration_ms is None else min(fastest_duration_ms, duration)
                    slowest_duration_ms = duration if slowest_duration_ms is None else max(slowest_duration_ms, duration)
            elif review_status == "FAILED":
                failed_count += 1
                if created_at:
                    activity_map[date_key]["failed"] += 1

        avg_duration_ms = int(duration_sum / duration_count) if duration_count else 0

        active_finished_count = completed_count + failed_count
        success_rate = (
            round((completed_count / active_finished_count) * 100, 1)
            if active_finished_count > 0 else (100.0 if total_reviews == 0 else 0.0)
        )

        review_perf = {
            "avg_duration_ms": avg_duration_ms,
            "fastest_duration_ms": fastest_duration_ms,
            "slowest_duration_ms": slowest_duration_ms,
            "completed_reviews": completed_count,
            "failed_reviews": failed_count,
            "total_reviews": total_reviews,
            "success_rate": success_rate
        }

        # 3. Review Activity Time Series (Daily)
        sorted_dates = sorted(activity_map.keys())
        review_activity = [
            {
                "date": d,
                "total_reviews": activity_map[d]["total"],
                "completed_reviews": activity_map[d]["completed"],
                "failed_reviews": activity_map[d]["failed"]
            }
            for d in sorted_dates
        ]

        # 4. Severity Distribution & Severity Trends
        severity_dist = {
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "total_issues": total_issues_detected
        }

        sorted_trend_dates = sorted(trend_map.keys())
        severity_trends = [
            {
                "date": d,
                "critical_count": trend_map[d]["critical"],
                "high_count": trend_map[d]["high"],
                "medium_count": trend_map[d]["medium"],
                "low_count": trend_map[d]["low"]
            }
            for d in sorted_trend_dates
        ]

        # 5. Dynamically Derive Issue Categories from review_result JSONB
        category_counts = defaultdict(int)
        file_metrics = defaultdict(lambda: {"total_issues": 0, "high_critical": 0, "review_count": 0})

        for review_result_row in _iter_project_rows(
            supabase,
            "reviews",
            "id, review_result",
            project_id,
            cutoff_iso,
            status_filter="COMPLETED",
            order_by="created_at",
        ):
            result_json = review_result_row.get("review_result") or {}
            files_list = result_json.get("reviews") or []
            seen_files = set()

            for f_item in files_list:
                fname = f_item.get("filename") or "unknown"
                rev_obj = f_item.get("review") or {}
                issues_list = rev_obj.get("issues") or []

                if fname not in seen_files:
                    seen_files.add(fname)
                    file_metrics[fname]["review_count"] += 1

                for iss in issues_list:
                    cat_name = iss.get("category")
                    if not cat_name or not str(cat_name).strip():
                        cat_name = "General"
                    category_counts[str(cat_name).strip()] += 1

                    file_metrics[fname]["total_issues"] += 1
                    sev_upper = str(iss.get("severity", "")).upper()
                    if sev_upper in ["CRITICAL", "HIGH"]:
                        file_metrics[fname]["high_critical"] += 1

        total_categorized_issues = sum(category_counts.values())
        issue_categories = [
            {
                "category": cat,
                "count": count,
                "percentage": round((count / total_categorized_issues) * 100, 1) if total_categorized_issues > 0 else 0.0
            }
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # 6. Top Problematic Files
        problematic_files = []
        for fname, metrics in file_metrics.items():
            if metrics["total_issues"] > 0:
                problematic_files.append({
                    "filename": fname,
                    "total_issues": metrics["total_issues"],
                    "high_critical_count": metrics["high_critical"],
                    "review_count": metrics["review_count"]
                })

        problematic_files.sort(key=lambda x: (x["total_issues"], x["high_critical_count"]), reverse=True)
        top_problematic_files = problematic_files[:10]

        # 7. Repository Review Health (Defined using recent reviews within selected date range)
        failure_rate = (failed_count / total_reviews * 100) if total_reviews > 0 else 0.0
        sync_status = project.get("sync_status") or "READY"
        factors = []

        if critical_count > 0:
            health_status = "Needs Attention"
            factors.append(f"{critical_count} critical severity finding(s) detected in recent reviews.")
        elif sync_status == "SYNC_FAILED":
            health_status = "Needs Attention"
            factors.append("Repository synchronization failed. Codebase may be out of date.")
        elif failure_rate > 20.0 and total_reviews >= 3:
            health_status = "Needs Attention"
            factors.append(f"High review failure rate ({round(failure_rate, 1)}% failed executions).")
        elif high_count > 0:
            health_status = "Good"
            factors.append(f"{high_count} high severity issue(s) identified in code changes.")
        else:
            health_status = "Strong"
            factors.append("Zero critical or high severity vulnerabilities detected in recent reviews.")

        if sync_status == "READY":
            factors.append("Local Git repository and ChromaDB vector store are fully synchronized.")

        if total_reviews == 0:
            summary_text = "No reviews have been executed for this project yet."
        elif health_status == "Strong":
            summary_text = "Repository review health is strong. No blocking security or correctness vulnerabilities found."
        elif health_status == "Good":
            summary_text = "Repository health is good. Minor high severity suggestions require developer attention."
        else:
            summary_text = "Action required: Critical issues or review/sync anomalies detected in recent audits."

        repository_health = {
            "status": health_status,
            "summary_text": summary_text,
            "critical_issues_recent": critical_count,
            "high_issues_recent": high_count,
            "failure_rate_percentage": round(failure_rate, 1),
            "sync_status": sync_status,
            "last_synced_at": project.get("last_synced_at"),
            "factors": factors
        }

        # 8. Latest Reviews & Latest Pull Requests
        # Resolve titles only for the latest review cards rather than retaining
        # every PR row in memory for the entire analytics request.
        latest_reviews = []
        pr_map = {}
        latest_pr_ids = list({r.get("pull_request_id") for r in latest_review_rows if r.get("pull_request_id")})
        if latest_pr_ids:
            pr_result = (
                supabase.table("pull_requests")
                .select("id, title")
                .eq("project_id", project_id)
                .in_("id", latest_pr_ids)
                .execute()
            )
            pr_map = {p["id"]: p.get("title") for p in (pr_result.data or [])}

        for review in latest_review_rows:
            latest_reviews.append({
                "id": review["id"],
                "github_pr_number": review["github_pr_number"],
                "pr_title": pr_map.get(review.get("pull_request_id")),
                "status": review.get("status", "QUEUED"),
                "issues_count": review.get("issues_count", 0),
                "high_count": review.get("high_count", 0),
                "critical_count": review.get("critical_count", 0),
                "head_commit_sha": review.get("head_commit_sha"),
                "created_at": review.get("created_at")
            })

        latest_pull_requests = []
        for pull_request in latest_pr_rows:
            latest_pull_requests.append({
                "github_pr_number": pull_request.get("github_pr_number", 0),
                "title": pull_request.get("title", ""),
                "state": pull_request.get("state", "OPEN"),
                "author_login": pull_request.get("author_login") or "unknown",
                "changed_files_count": pull_request.get("changed_files_count") or pull_request.get("changed_files", 0),
                "updated_at": pull_request.get("updated_at") or pull_request.get("created_at")
            })

        overview = {
            "total_pull_requests": total_prs,
            "open_pull_requests": open_prs,
            "merged_pull_requests": merged_prs,
            "closed_pull_requests": closed_prs,
            "total_reviews": total_reviews,
            "completed_reviews": completed_count,
            "failed_reviews": failed_count,
            "total_issues_detected": total_issues_detected,
            "avg_review_duration_ms": avg_duration_ms
        }

        has_data = bool(total_reviews > 0 or total_prs > 0)

        return {
            "project_id": project_id,
            "date_range": range_str,
            "overview": overview,
            "review_activity": review_activity,
            "severity_distribution": severity_dist,
            "severity_trends": severity_trends,
            "issue_categories": issue_categories,
            "problematic_files": top_problematic_files,
            "pull_request_statistics": pr_stats,
            "review_performance": review_perf,
            "repository_health": repository_health,
            "latest_reviews": latest_reviews,
            "latest_pull_requests": latest_pull_requests,
            "has_data": has_data
        }

insights_service = InsightsService()
