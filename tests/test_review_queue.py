import asyncio
from unittest.mock import MagicMock, patch

from src.services.review_service import ReviewService
from src.services.review_queue_worker import ReviewQueueWorker


def test_enqueue_review_persists_queued_record():
    async def run():
        service = ReviewService()
        supabase = MagicMock()
        project = {"id": "proj-uuid-123", "user_id": "user-uuid-456"}
        pull_request = {
            "id": "pr-uuid-1",
            "project_id": "proj-uuid-123",
            "github_pr_number": 42,
            "base_sha": "base-sha",
            "head_sha": "head-sha",
        }

        pr_table = MagicMock()
        pr_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[pull_request]
        )
        review_table = MagicMock()
        review_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "review-queued-1"}]
        )
        supabase.table.side_effect = lambda name: {
            "pull_requests": pr_table,
            "reviews": review_table,
        }[name]

        with patch("src.services.review_service.get_supabase_client", return_value=supabase), \
             patch.object(service, "_resolve_project_and_token", return_value=(project, "pat")):
            result = await service.enqueue_review(
                project_id="proj-uuid-123",
                pr_number=42,
                user_id="user-uuid-456",
                user_token="user-jwt",
            )

        queued_row = review_table.insert.call_args.args[0]
        assert queued_row["status"] == "QUEUED"
        assert queued_row["project_id"] == "proj-uuid-123"
        assert queued_row["github_pr_number"] == 42
        assert result["review_id"] == "review-queued-1"
        assert result["status"] == "QUEUED"

    asyncio.run(run())


def test_worker_claims_jobs_with_shared_concurrency_configuration():
    worker = ReviewQueueWorker()
    supabase = MagicMock()
    supabase.rpc.return_value.execute.return_value = MagicMock(
        data=[{"id": "review-queued-1"}]
    )

    with patch("src.services.review_queue_worker.get_supabase_client", return_value=supabase):
        claimed = worker._claim_next_job()

    assert claimed["id"] == "review-queued-1"
    rpc_name, rpc_args = supabase.rpc.call_args.args
    assert rpc_name == "claim_next_review_job"
    assert rpc_args["p_worker_id"] == worker.worker_id
    assert rpc_args["p_max_concurrency"] >= 1
