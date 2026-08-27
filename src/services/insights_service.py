import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from fastapi import HTTPException, status

from src.api.auth import get_supabase_client

logger = logging.getLogger("insights_service")

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
        """
        Aggregates and returns comprehensive project insights for the specified date range.
        """
        supabase = get_supabase_client(user_token)
        project = self._resolve_project(project_id, user_id, user_token)
        cutoff = self._get_date_cutoff(range_str)
        cutoff_iso = cutoff.isoformat() if cutoff else None

        # 1. Fetch Pull Requests for the project
        pr_query = supabase.table("pull_requests").select("*").eq("project_id", project_id)
        if cutoff_iso:
            pr_query = pr_query.gte("created_at", cutoff_iso)
        pr_res = pr_query.order("created_at", desc=True).execute()
        pull_requests = pr_res.data or []

        # Also get all PRs count if date filtered, or calculate PR stats from filtered set
        total_prs = len(pull_requests)
        open_prs = sum(1 for p in pull_requests if p.get("state") == "OPEN")
        merged_prs = sum(1 for p in pull_requests if p.get("state") == "MERGED")
        closed_prs = sum(1 for p in pull_requests if p.get("state") == "CLOSED")
        draft_prs = sum(1 for p in pull_requests if p.get("is_draft") is True or p.get("state") == "DRAFT")

        avg_changed_files = (
            round(sum(p.get("changed_files_count", 0) for p in pull_requests) / total_prs, 1)
            if total_prs > 0 else 0.0
        )
        avg_additions = (
            round(sum(p.get("additions", 0) for p in pull_requests) / total_prs, 1)
            if total_prs > 0 else 0.0
        )
        avg_deletions = (
            round(sum(p.get("deletions", 0) for p in pull_requests) / total_prs, 1)
            if total_prs > 0 else 0.0
        )

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

        # 2. Fetch Reviews for the project in the date range
        review_query = supabase.table("reviews").select("*").eq("project_id", project_id)
        if cutoff_iso:
            review_query = review_query.gte("created_at", cutoff_iso)
        review_res = review_query.order("created_at", desc=True).execute()
        reviews = review_res.data or []

        total_reviews = len(reviews)
        completed_reviews = [r for r in reviews if r.get("status") == "COMPLETED"]
        failed_reviews = [r for r in reviews if r.get("status") == "FAILED"]
        completed_count = len(completed_reviews)
        failed_count = len(failed_reviews)

        # Overview Issue Totals
        total_issues_detected = sum(r.get("issues_count", 0) for r in completed_reviews)
        critical_count = sum(r.get("critical_count", 0) for r in completed_reviews)
        high_count = sum(r.get("high_count", 0) for r in completed_reviews)
        medium_count = sum(r.get("medium_count", 0) for r in completed_reviews)
        low_count = sum(r.get("low_count", 0) for r in completed_reviews)

        # Review Performance
        valid_durations = [
            r["review_duration_ms"] for r in completed_reviews
            if r.get("review_duration_ms") and r["review_duration_ms"] > 0
        ]
        avg_duration_ms = (
            int(sum(valid_durations) / len(valid_durations))
            if valid_durations else 0
        )
        fastest_duration_ms = min(valid_durations) if valid_durations else None
        slowest_duration_ms = max(valid_durations) if valid_durations else None

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
        activity_map = defaultdict(lambda: {"total": 0, "completed": 0, "failed": 0})
        for r in reviews:
            created_str = r.get("created_at")
            if created_str:
                date_key = created_str[:10]
                activity_map[date_key]["total"] += 1
                if r.get("status") == "COMPLETED":
                    activity_map[date_key]["completed"] += 1
                elif r.get("status") == "FAILED":
                    activity_map[date_key]["failed"] += 1

        # Sort chronological
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

        trend_map = defaultdict(lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})
        for r in completed_reviews:
            created_str = r.get("created_at")
            if created_str:
                date_key = created_str[:10]
                trend_map[date_key]["critical"] += r.get("critical_count", 0)
                trend_map[date_key]["high"] += r.get("high_count", 0)
                trend_map[date_key]["medium"] += r.get("medium_count", 0)
                trend_map[date_key]["low"] += r.get("low_count", 0)

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
        file_metrics = defaultdict(lambda: {"total_issues": 0, "high_critical": 0, "review_count": 0, "seen_reviews": set()})

        for r in completed_reviews:
            r_id = r.get("id")
            result_json = r.get("review_result") or {}
            files_list = result_json.get("reviews") or []

            for f_item in files_list:
                fname = f_item.get("filename") or "unknown"
                rev_obj = f_item.get("review") or {}
                issues_list = rev_obj.get("issues") or []

                if r_id not in file_metrics[fname]["seen_reviews"]:
                    file_metrics[fname]["seen_reviews"].add(r_id)
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
        # Build PR title map for latest reviews
        latest_reviews = []
        if reviews:
            pr_map = {p["id"]: p.get("title") for p in pull_requests}
            for r in reviews[:5]:
                latest_reviews.append({
                    "id": r["id"],
                    "github_pr_number": r["github_pr_number"],
                    "pr_title": pr_map.get(r.get("pull_request_id")),
                    "status": r.get("status", "QUEUED"),
                    "issues_count": r.get("issues_count", 0),
                    "high_count": r.get("high_count", 0),
                    "critical_count": r.get("critical_count", 0),
                    "head_commit_sha": r.get("head_commit_sha"),
                    "created_at": r.get("created_at")
                })

        latest_pull_requests = []
        for p in pull_requests[:5]:
            author_data = p.get("author") or {}
            author_login = p.get("author_username") or p.get("author_login") or (author_data.get("login") if isinstance(author_data, dict) else "unknown")
            latest_pull_requests.append({
                "github_pr_number": p.get("github_pr_number", 0),
                "title": p.get("title", ""),
                "state": p.get("state", "OPEN"),
                "author_login": author_login or "unknown",
                "changed_files_count": p.get("changed_files_count", 0),
                "updated_at": p.get("updated_at") or p.get("created_at")
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

        has_data = Boolean = bool(total_reviews > 0 or total_prs > 0)

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
